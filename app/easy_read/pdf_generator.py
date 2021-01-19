#!/usr/bin python3


# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from os import getenv
from time import sleep
import re

# 3rd party:
from flask import g, redirect, make_response, request
from latex import build_pdf

# Internal: 
from .views import easy_read, local_easy_read
from ..common.data.queries import get_area_data, AreaType
from ..storage import StorageClient

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'create_and_redirect'
]


PDF_TYPE = "application/pdf"
PDF_CACHE = "public, max-age=86400, s-maxage=604800"
CONTAINER = "ondemand"
LOCK_DURATION = 15  # seconds
WAIT_DURATION = 5  # seconds


def name2url(name):
    return re.sub(r"['.\s_]", "-", name)


def generate_pdf(area_type: str, area_code: str) -> bytes:
    if area_type is None:
        resp = easy_read(g.timestamp, None, template="latex/easy_read.tex")
    else:
        resp = local_easy_read(
            g.timestamp,
            area_type,
            area_code,
            template="latex/easy_read.tex"
        )

    latex = str.join("", [item.decode() for item in resp.response])

    pdf_raw = build_pdf(latex)

    return pdf_raw.data


def create_and_redirect(area_type, area_code):
    area_name = "United Kingdom"

    if area_type is not None:
        area = get_area_data(area_type, area_code)
        area_name = area.get(f"{area_type.lower()}Name")

    date = g.timestamp.split("T")[0]

    filename = f"ER_{name2url(area_name)}_{date}.pdf"
    path = f"easy_read/{date}/{area_type or AreaType.uk}/{filename}"

    storage_kws = dict(
        container=CONTAINER,
        path=path,
        compressed=False,
        content_type=PDF_TYPE,
        cache_control=PDF_CACHE,
        content_disposition=f'inline; filename="ER_{area_name}_{date}.pdf"'
    )

    with StorageClient(**storage_kws) as cli:
        if not cli.exists():
            cli.upload(b"")
            with cli.lock_file(LOCK_DURATION):
                pdf = generate_pdf(area_type, area_code)
                cli.upload(pdf)
        else:
            counter = 0

            while cli.is_locked():
                sleep(1)
                counter += 1

                if counter == WAIT_DURATION:
                    raise RuntimeError(
                        "Failed to obtained the file - lock was not released."
                    )

    host = request.headers.get("X-Forwarded-Host", "")
    if host:
        host = f"https://{host}"

    resp = redirect(f"{host}/downloads/{CONTAINER}/{path}", code=303)

    return make_response(resp)
