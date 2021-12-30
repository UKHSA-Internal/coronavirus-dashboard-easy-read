#!/usr/bin python3


# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from typing import Union
from http import HTTPStatus
import re
from asyncio import sleep

# 3rd party:
from latex import build_pdf
from starlette.responses import RedirectResponse

# Internal: 
from app.storage import AsyncStorageClient
from app.common.utils import get_release_timestamp
from app.landing.views import get_home_page
from app.postcode.views import postcode_page
from app.template_processor.template import smallest_area_name, render_template

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'create_and_redirect'
]


PDF_TYPE = "application/pdf"
PDF_CACHE = "public, max-age=86400, s-maxage=604800"
CONTAINER = "ondemand"
LOCK_DURATION = 15  # seconds
WAIT_DURATION = 10  # seconds


def name2url(name):
    return re.sub(r"['.\s&,]", "-", name)


async def generate_pdf(request, data, area_type: str, timestamp: str) -> bytes:
    if area_type is None:
        resp = await render_template(
            request,
            template_name="latex/easy_read.tex",
            render=False,
            context=dict(
                timestamp=timestamp,
                data=data
            )
        )

        # resp = easy_read(request, timestamp, None, template="latex/easy_read.tex")
    else:
        resp = await render_template(
            request,
            template_name="latex/easy_read.tex",
            render=False,
            context=dict(
                timestamp=timestamp,
                data=data
            )
        )

    pdf_raw = build_pdf(resp)

    return pdf_raw.data


async def create_and_redirect(request):
    area_type = request.path_params.get("area_type", "overview")  # type: str
    area_code = request.path_params.get("area_code", None)  # type: Union[str, None]

    timestamp = await get_release_timestamp()

    get_data = get_home_page
    if area_code is not None:
        get_data = postcode_page

    data = await get_data(request, timestamp, render=False)
    date = timestamp.split("T")[0]
    area_name = smallest_area_name(data)

    filename = f"ER_{name2url(area_name)}_{date}.pdf"
    path = f"easy_read/{date}/{area_type}/{filename}"

    storage_kws = dict(
        container=CONTAINER,
        path=path,
        compressed=False,
        content_type=PDF_TYPE,
        cache_control=PDF_CACHE,
        content_disposition=f'inline; filename="ER_{area_name}_{date}.pdf"'
    )

    host = request.headers.get("X-Forwarded-Host", "")
    if host:
        host = f"https://{host}"

    resp = RedirectResponse(
        url=f"{host}/downloads/{CONTAINER}/{path}",
        status_code=HTTPStatus.SEE_OTHER.real
    )

    async with AsyncStorageClient(**storage_kws) as cli:
        try:
            if not await cli.exists():
                await cli.upload(b"")

                async with cli.lock_file(LOCK_DURATION):
                    pdf = await generate_pdf(request, data, area_type, timestamp)
                    await cli.upload(pdf)

                return resp

            counter = 0
            while await cli.exists() and counter < WAIT_DURATION:
                if await cli.is_locked():
                    await sleep(1)
                    counter += 1
                    continue

                return resp

            raise RuntimeError("Failed to obtained the file - lock was not released.")
        except Exception as err:
            # Remove the blob on exception - data may be incomplete.
            if not isinstance(err, RuntimeError) and await cli.exists():
                await cli.delete()
            raise err

