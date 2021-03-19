#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from datetime import datetime, timedelta

# 3rd party:
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import AlwaysOnSampler
# from opencensus.trace import config_integration
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind

# from opencensus.trace.propagation.trace_context_http_header_format import TraceContextPropagator
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES

# Internal:
from app.easy_read import create_and_redirect as get_pdf
from app.config import Settings
from app.views import base_router
from app.healthcheck import run_healthcheck
from app.exceptions import exception_handlers
from app.common.utils import add_cloud_role_name

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'app'
]


WEBSITE_TIMESTAMP = {
    "container": "publicdata",
    "path":  "assets/dispatch/website_timestamp"
}
LATEST_PUBLISHED_TIMESTAMP = {
    "container": "pipeline",
    "path": "info/latest_published"
}

AI_INSTRUMENTATION_KEY = f"InstrumentationKey={Settings.instrumentation_key}"

HTTP_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"

HTTP_URL = COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

routes = [
    Route('/easy_read', endpoint=base_router, methods=["GET", "HEAD"]),
    Route('/easy_read/download', endpoint=get_pdf, methods=["GET", "HEAD"]),
    Route('/easy_read/{area_type:str}/{area_code:str}', endpoint=base_router, methods=["GET", "HEAD"]),
    Route('/easy_read/download/{area_type:str}/{area_code:str}', endpoint=get_pdf, methods=["GET", "HEAD"]),
    Route('/easy_read/download/{area_type:str}/{area_code:str}', endpoint=get_pdf, methods=["GET", "HEAD"]),
    Route('/healthcheck', endpoint=run_healthcheck, methods=["GET", "HEAD"]),
    Route('/easy_read/healthcheck', endpoint=run_healthcheck, methods=["GET", "HEAD"]),
    Mount('/easy_read/assets', StaticFiles(directory="static"), name="static")
]

middleware = [
    Middleware(ProxyHeadersMiddleware, trusted_hosts=Settings.service_domain)
]


app = Starlette(
    debug=Settings.DEBUG,
    routes=routes,
    middleware=middleware,
    exception_handlers=exception_handlers,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)

    last_modified = datetime.now()
    expires = last_modified + timedelta(minutes=1, seconds=30)

    response.headers['last-modified'] = last_modified.strftime(HTTP_DATE_FORMAT)
    response.headers['expires'] = expires.strftime(HTTP_DATE_FORMAT)
    response.headers['cache-control'] = 'public, must-revalidate, max-age=30, s-maxage=90'
    response.headers['PHE-Server-Loc'] = Settings.server_location

    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    exporter = AzureExporter(connection_string=Settings.instrumentation_key)
    exporter.add_telemetry_processor(add_cloud_role_name)

    tracer = Tracer(
        exporter=exporter,
        sampler=AlwaysOnSampler()
    )

    with tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER

        response = await call_next(request)

        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE,
            attribute_value=response.status_code
        )

        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL,
            attribute_value=str(request.url)
        )

        tracer.add_attribute_to_current_span("environment", Settings.ENVIRONMENT)
        tracer.add_attribute_to_current_span("server_location", Settings.server_location)

    return response


# @app.errorhandler(404)
# def handle_404(err):
#     if isinstance(err, HandledException):
#         return err
#
#     app.logger.info(f"404 - Not found", extra={'custom_dimensions': {"url": request.url}})
#
#     context = dict(
#         response_code=404,
#         response_message="Not found"
#     )
#
#     return render_template("html/errors/40x.html", **context), 404
#
#
# @app.errorhandler(Exception)
# def handle_500(err):
#     if isinstance(err, HandledException):
#         return err
#
#     additional_info = {
#         'website_timestamp': g.website_timestamp,
#         'latest_release': g.timestamp,
#         'db_host': getenv("AzureCosmosHost", NOT_AVAILABLE),
#         "API_environment": getenv("API_ENV", NOT_AVAILABLE),
#         "server_location": getenv("SERVER_LOCATION", NOT_AVAILABLE),
#         "is_dev": getenv("IS_DEV", NOT_AVAILABLE),
#         "redis": getenv("AZURE_REDIS_HOST", NOT_AVAILABLE),
#         "AzureCosmosDBName": getenv("AzureCosmosDBName", NOT_AVAILABLE),
#         "AzureCosmosCollection": getenv("AzureCosmosCollection", NOT_AVAILABLE),
#         "AzureCosmosDestinationsCollection": getenv(
#             "AzureCosmosDestinationsCollection",
#             NOT_AVAILABLE
#         ),
#     }
#
#     app.logger.exception(err, extra={'custom_dimensions': additional_info})
#
#     return render_template("html/errors/500.html"), 500



# @app.before_first_request
# def prep_service():
#     exporter = AzureExporter(connection_string=AI_INSTRUMENTATION_KEY)
#     exporter.add_telemetry_processor(add_cloud_role_name)
#     propagator = TraceContextPropagator()
#
#     _ = FlaskMiddleware(
#         app=app,
#         exporter=exporter,
#         sampler=AlwaysOnSampler(),
#         propagator=propagator
#     )
#
#     handler = AzureLogHandler(connection_string=AI_INSTRUMENTATION_KEY)
#
#     handler.add_telemetry_processor(add_cloud_role_name)
#
#     for log, level in logging_instances:
#         log.addHandler(handler)
#         log.setLevel(level)
#
#
# @app.before_request
# def prepare_context():
#     custom_dims = dict(
#         custom_dimensions=dict(
#             is_healthcheck=request.path == HEALTHCHECK_PATH,
#             url=str(request.url),
#             path=str(request.path),
#             query_string=str(request.query_string)
#         )
#     )
#
#     app.logger.info(request.url, extra=custom_dims)
#
#     with StorageClient(**WEBSITE_TIMESTAMP) as client:
#         g.website_timestamp = client.download().readall().decode()
#
#     with StorageClient(**LATEST_PUBLISHED_TIMESTAMP) as client:
#         g.timestamp = client.download().readall().decode()
#
#     return None
#
#
# @app.after_request
# def prepare_response(resp: Response):
#     last_modified = datetime.now()
#     # (
#     #     g.timestamp[:PYTHON_TIMESTAMP_LEN] + "Z",
#     #     "%Y-%m-%dT%H:%M:%S.%fZ"
#     # )
#
#     resp.last_modified = last_modified
#     resp.expires = datetime.now() + timedelta(minutes=1, seconds=30)
#     resp.cache_control.max_age = 30
#     resp.cache_control.public = True
#     resp.cache_control.s_maxage = 90
#     resp.cache_control.must_revalidate = True
#     resp.headers['PHE-Server-Loc'] = SERVER_LOCATION
#
#     resp.add_etag()
#
#     if resp.content_type == PDF_TYPE:
#         try:
#             minified = [
#                 minifier.get_minified(item.decode(), 'html')
#                 for item in resp.response
#             ]
#             data = str.join("", minified).encode()
#             resp.set_data(data)
#         except UnicodeDecodeError as e:
#             app.logger.warning(e)
#
#     return resp


if __name__ == "__main__":
    # app.run(host='0.0.0.0', debug=False, port=5050)
    from uvicorn import run as uvicorn_run

    uvicorn_run(app, port=1245)
