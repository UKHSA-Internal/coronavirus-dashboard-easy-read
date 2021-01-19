#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
import re
import logging
from os import getenv
from datetime import datetime, timedelta
from os.path import abspath, join as join_path, pardir
from typing import Union
from functools import lru_cache

# 3rd party:
from flask import Flask, Response, g, render_template, make_response, request
from flask_minify import minify
from pytz import timezone

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace import config_integration
# from opencensus.trace.tracer import Tracer
from opencensus.trace.propagation.trace_context_http_header_format import TraceContextPropagator

# Internal:
from app.easy_read import (
    easy_read, local_easy_read, get_validated_postcode,
    create_and_redirect as get_pdf
)
from app.common.caching import cache_client
from app.common.exceptions import HandledException
from app.common.utils import add_cloud_role_name
from app.storage import StorageClient
from app.database import CosmosDB, Collection
from app.common.data.query_templates import HealthCheck

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'app'
]


HEALTHCHECK_PATH = "/healthcheck"
WEBSITE_TIMESTAMP = {
    "container": "publicdata",
    "path":  "assets/dispatch/website_timestamp"
}
LATEST_PUBLISHED_TIMESTAMP = {
    "container": "pipeline",
    "path": "info/latest_published"
}
NOT_AVAILABLE = "N/A"
PDF_TYPE = "application/pdf"
INSTRUMENTATION_CODE = getenv("APPINSIGHTS_INSTRUMENTATIONKEY", "")
AI_INSTRUMENTATION_KEY = f"InstrumentationKey={INSTRUMENTATION_CODE}"
SERVER_LOCATION_KEY = "SERVER_LOCATION"
SERVER_LOCATION = getenv(SERVER_LOCATION_KEY, NOT_AVAILABLE)
PYTHON_TIMESTAMP_LEN = 24
HTTP_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"
LOG_LEVEL = getenv("LOG_LEVEL", "INFO")

timestamp_pattern = "%A %d %B %Y at %-I:%M %p"
timezone_LN = timezone("Europe/London")

lookup_db = CosmosDB(Collection.LOOKUP)

instance_path = abspath(join_path(abspath(__file__), pardir))

app = Flask(
    __name__,
    instance_path=instance_path,
    static_folder="static",
    static_url_path="/easy_read/assets/",
    template_folder='templates'
)
app.url_map.strict_slashes = False
config_integration.trace_integrations(['requests'])
config_integration.trace_integrations(['logging'])

app.config.from_object('app.config.Config')

# Logging -------------------------------------------------
log_level = getattr(logging, LOG_LEVEL)

logging_instances = [
    [app.logger, log_level],
    [logging.getLogger('werkzeug'), logging.WARNING],
    [logging.getLogger('azure'), logging.WARNING]
]

# ---------------------------------------------------------

cache_client.init_app(app)

minifier = minify(
    html=True,
    js=True,
    cssless=True,
    caching_limit=0,
    fail_safe=True
)


@app.template_filter()
@lru_cache(maxsize=256)
def format_timestamp(latest_timestamp: str) -> str:
    ts_python_iso = latest_timestamp[:-1] + "+00:00"
    ts = datetime.fromisoformat(ts_python_iso)
    ts_london = ts.astimezone(timezone_LN)
    formatted = ts_london.strftime(timestamp_pattern)
    result = re.sub(r'\s([AP]M)', lambda found: found.group(1).lower(), formatted)
    return result


@app.template_filter()
@lru_cache(maxsize=64)
def as_date(latest_timestamp: str) -> str:
    ts_python_iso = latest_timestamp[:-1] + "+00:00"
    ts = datetime.fromisoformat(ts_python_iso)
    ts_london = ts.astimezone(timezone_LN)
    formatted = ts_london.strftime("%A, %d %B %Y")
    return formatted


@app.template_filter()
@lru_cache(maxsize=256)
def format_number(value: Union[int, float]) -> str:
    try:
        value_int = int(value)
    except ValueError:
        if value == "0-2":
            value = "0 &ndash; 2"
        return str(value)
    except TypeError:
        return NOT_AVAILABLE

    if value == value_int:
        return format(value_int, ',d')

    return str(value)


@app.template_filter()
def trim_area_name(area_name):
    pattern = re.compile(r"(nhs\b.*)", re.IGNORECASE)
    name = pattern.sub("", area_name)

    return name.strip()


@app.template_filter()
def escape_name(area_name):
    area_name = area_name.replace("&", r"\&")
    return area_name


@app.template_filter()
def pluralise(number, singular, plural, null=str()):
    if abs(number) > 1:
        return plural

    if abs(number) == 1:
        return singular

    if number == 0 and not len(null):
        return plural

    return null


@app.template_filter()
def comparison_verb(number, greater, smaller, same):
    if number > 0:
        return greater

    if number < 0:
        return smaller

    return same


@app.template_filter()
def isnone(value):
    return value is None


@app.errorhandler(404)
def handle_404(err):
    if isinstance(err, HandledException):
        return err

    app.logger.info(f"404 - Not found", extra={'custom_dimensions': {"url": request.url}})
    return render_template("html/errors/404.html"), 404


@app.errorhandler(Exception)
def handle_500(err):
    if isinstance(err, HandledException):
        return err

    additional_info = {
        'website_timestamp': g.website_timestamp,
        'latest_release': g.timestamp,
        'db_host': getenv("AzureCosmosHost", NOT_AVAILABLE),
        "API_environment": getenv("API_ENV", NOT_AVAILABLE),
        "server_location": getenv("SERVER_LOCATION", NOT_AVAILABLE),
        "is_dev": getenv("IS_DEV", NOT_AVAILABLE),
        "redis": getenv("AZURE_REDIS_HOST", NOT_AVAILABLE),
        "AzureCosmosDBName": getenv("AzureCosmosDBName", NOT_AVAILABLE),
        "AzureCosmosCollection": getenv("AzureCosmosCollection", NOT_AVAILABLE),
        "AzureCosmosDestinationsCollection": getenv(
            "AzureCosmosDestinationsCollection",
            NOT_AVAILABLE
        ),
    }

    app.logger.exception(err, extra={'custom_dimensions': additional_info})

    return render_template("html/errors/500.html"), 500


@cache_client.memoize(timeout=120)
def get_globals(website_timestamp):
    response = dict(
        DEBUG=app.debug,
        timestamp=website_timestamp,
        app_insight_token=INSTRUMENTATION_CODE
    )

    return response


@app.context_processor
def inject_globals():
    if request.method == "HEAD":
        return dict()

    return get_globals(g.website_timestamp)


@app.before_first_request
def prep_service():
    exporter = AzureExporter(connection_string=AI_INSTRUMENTATION_KEY)
    exporter.add_telemetry_processor(add_cloud_role_name)
    propagator = TraceContextPropagator()

    _ = FlaskMiddleware(
        app=app,
        exporter=exporter,
        sampler=AlwaysOnSampler(),
        propagator=propagator
    )

    handler = AzureLogHandler(connection_string=AI_INSTRUMENTATION_KEY)

    handler.add_telemetry_processor(add_cloud_role_name)

    for log, level in logging_instances:
        log.addHandler(handler)
        log.setLevel(level)


@app.before_request
def prepare_context():
    custom_dims = dict(
        custom_dimensions=dict(
            is_healthcheck=request.path == HEALTHCHECK_PATH,
            url=str(request.url),
            path=str(request.path),
            query_string=str(request.query_string)
        )
    )

    app.logger.info(request.url, extra=custom_dims)

    with StorageClient(**WEBSITE_TIMESTAMP) as client:
        g.website_timestamp = client.download().readall().decode()

    with StorageClient(**LATEST_PUBLISHED_TIMESTAMP) as client:
        g.timestamp = client.download().readall().decode()

    return None


@app.after_request
def prepare_response(resp: Response):
    last_modified = datetime.strptime(
        g.timestamp[:PYTHON_TIMESTAMP_LEN] + "Z",
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    resp.last_modified = last_modified
    resp.expires = datetime.now() + timedelta(minutes=1, seconds=30)
    resp.cache_control.max_age = 30
    resp.cache_control.public = True
    resp.cache_control.s_maxage = 90
    resp.cache_control.must_revalidate = True
    resp.headers['PHE-Server-Loc'] = SERVER_LOCATION

    resp.add_etag()

    if resp.content_type == PDF_TYPE:
        try:
            minified = [
                minifier.get_minified(item.decode(), 'html')
                for item in resp.response
            ]
            data = str.join("", minified).encode()
            resp.set_data(data)
        except UnicodeDecodeError as e:
            app.logger.warning(e)

    return resp


@app.route(HEALTHCHECK_PATH, methods=("HEAD", "GET"))
def health_check(**kwargs):
    result = lookup_db.query(HealthCheck, params=list()).pop()

    if len(result) > 0:
        return make_response("ALIVE", 200)

    raise RuntimeError("Healthcheck failed.")


@app.route("/easy_read", methods=("HEAD", "OPTIONS", "GET"),
           defaults={"area_type": None, "area_code": None})
@app.route("/easy_read/<area_type>/<area_code>", methods=("HEAD", "OPTIONS", "GET"))
def local_responder(area_type, area_code, **kwargs):
    if request.method == "GET":
        postcode = get_validated_postcode(request.args)

        if postcode is not None or area_type is None:
            return easy_read(g.timestamp, postcode)

        return local_easy_read(g.timestamp, area_type, area_code)

    return app.make_default_options_response()


@app.route("/easy_read/download", methods=("HEAD", "OPTIONS", "GET"),
           defaults={"area_type": None, "area_code": None})
@app.route("/easy_read/download/<area_type>/<area_code>", methods=("HEAD", "OPTIONS", "GET"))
def as_pdf(area_type, area_code):
    return get_pdf(area_type, area_code)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False, port=5050)
