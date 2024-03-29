#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from logging import getLogger
from http import HTTPStatus
from starlette.requests import Request

# 3rd party:

# Internal:
from app.template_processor import render_template
from app.config import Settings

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'exception_handlers'
]


logger = getLogger(__name__)


async def handle_404(request: Request, exc, **context):
    status = HTTPStatus.NOT_FOUND
    status_code = getattr(status, "value", 404)
    status_detail = getattr(status, "phrase", "Not Found")

    custom_dims = dict(
        custom_dimensions=dict(
            is_healthcheck=Settings.healthcheck_path in request.url.path,
            url=str(request.url),
            path=str(request.url.path),
            query_string=str(request.query_params),
            status_code=status_code,
            status_detail=status_detail,
            api_environment=Settings.ENVIRONMENT,
            server_location=Settings.server_location,
            is_dev=Settings.DEBUG,
            **context
        )
    )

    logger.warning(exc, extra=custom_dims, exc_info=True)

    return await render_template(
        request,
        "html/errors/40x.html",
        context={
            "status_code": status_code,
            "status_detail": status_detail,
            **context
        },
        status_code=status_code
    )


async def handle_500(request: Request, exc, **context):
    if hasattr(exc, "status_code"):
        status_code = getattr(exc, "status_code")
        status_detail = getattr(exc, "phrase", "detail")
    else:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        status_code = getattr(status, "value", 500)
        status_detail = getattr(status, "phrase", "Internal Server Error")

    custom_dims = dict(
        custom_dimensions=dict(
            is_healthcheck=Settings.healthcheck_path in request.url.path,
            url=str(request.url),
            path=str(request.url.path),
            query_string=str(request.query_params),
            status_code=status_code,
            status_detail=status_detail,
            API_environment=Settings.ENVIRONMENT,
            server_location=Settings.server_location,
            is_dev=Settings.DEBUG,
            **context
        )
    )

    logger.error(exc, extra=custom_dims, exc_info=True)

    return await render_template(
        request,
        "html/errors/50x.html",
        context={
            "status_code": status_code,
            "status_detail": status_detail,
            **context
        },
        status_code=status_code
    )


exception_handlers = {
    404: handle_404,
    500: handle_500,
    502: handle_500,
    503: handle_500
}
