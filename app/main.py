#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
import logging
from datetime import datetime, timedelta

# 3rd party:
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from opencensus.trace.samplers import AlwaysOnSampler

# Internal:
from app.easy_read import create_and_redirect as get_pdf
from app.config import Settings
from app.views import base_router
from app.healthcheck import run_healthcheck
from app.exceptions import exception_handlers
from app.common.utils import add_cloud_role_name, add_instance_role_id
from app.middleware.tracers.starlette import TraceRequestMiddleware

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

HTTP_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"

routes = [
    Route('/easy_read', endpoint=base_router, methods=["GET", "HEAD"]),
    Route('/easy_read/download', endpoint=get_pdf, methods=["GET", "HEAD"]),
    Route('/easy_read/{area_type:str}/{area_code:str}', endpoint=base_router, methods=["GET", "HEAD"]),
    Route('/easy_read/download/{area_type:str}/{area_code:str}', endpoint=get_pdf, methods=["GET", "HEAD"]),
    Route(f'/{Settings.healthcheck_path}', endpoint=run_healthcheck, methods=["GET", "HEAD"]),
    Route(f'/easy_read/{Settings.healthcheck_path}', endpoint=run_healthcheck, methods=["GET", "HEAD"]),
    Mount('/public/assets/summary', StaticFiles(directory="static"), name="static")
]

logging_instances = [
    [logging.getLogger("app"), logging.INFO],
    [logging.getLogger('uvicorn'), logging.WARNING],
    [logging.getLogger('uvicorn.access'), logging.WARNING],
    [logging.getLogger('uvicorn.error'), logging.ERROR],
    [logging.getLogger('azure'), logging.WARNING],
    [logging.getLogger('gunicorn'), logging.WARNING],
    [logging.getLogger('gunicorn.access'), logging.WARNING],
    [logging.getLogger('gunicorn.error'), logging.ERROR],
    [logging.getLogger('asyncpg'), logging.WARNING],
]

middleware = [
    Middleware(ProxyHeadersMiddleware, trusted_hosts=Settings.service_domain),
    Middleware(
        TraceRequestMiddleware,
        sampler=AlwaysOnSampler(),
        instrumentation_key=Settings.instrumentation_key,
        cloud_role_name=add_cloud_role_name,
        instance_role_id=add_instance_role_id,
        extra_attrs=dict(
            environment=Settings.ENVIRONMENT,
            server_location=Settings.server_location
        ),
        logging_instances=logging_instances
    )
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
    response.headers['UKHSA-Server-Loc'] = Settings.server_location

    return response


if __name__ == "__main__":
    # app.run(host='0.0.0.0', debug=False, port=5050)
    from uvicorn import run as uvicorn_run

    uvicorn_run(app, port=1245)
