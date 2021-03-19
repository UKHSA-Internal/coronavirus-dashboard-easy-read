#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
import logging
from datetime import datetime
from os.path import abspath, split as split_path, join as join_path
from operator import itemgetter
from json import load
from typing import Union, Any

# 3rd party:

from pandas import DataFrame

# Internal:
from .types import AlertsType, QueryDataType
from .utils import get_validated_postcode
from ..database.postgres import Connection
from ..template_processor import render_template

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'postcode_page'
]


get_area_type = itemgetter("areaType")

curr_dir, _ = split_path(abspath(__file__))
queries_dir = join_path(curr_dir, "queries")
assets_dir = join_path(curr_dir, "assets")

with open(join_path(queries_dir, "local_data.sql")) as fp:
    local_data_query = fp.read()


with open(join_path(assets_dir, "alert_levels.json")) as fp:
    alerts: AlertsType = load(fp)


with open(join_path(assets_dir, "query_params.json")) as fp:
    query_data: QueryDataType = load(fp)


async def get_postcode_data(conn: Any, timestamp: str, postcode: str) -> DataFrame:
    ts = datetime.fromisoformat(timestamp.replace("5Z", ""))
    partition_ts = f"{ts:%Y_%-m_%-d}"
    partition_ids = [
        f"{partition_ts}|other",
        f"{partition_ts}|ltla",
        f"{partition_ts}|utla",
        f"{partition_ts}|nhstrust",
    ]
    msoa_partition = f"{partition_ts}_msoa"
    msoa_metric = query_data["local_data"]["msoa_metric"]

    query = local_data_query.format(msoa_partition=msoa_partition)

    substitutes = (
        query_data["local_data"]["metrics"],
        postcode,
        partition_ids,
        f"{msoa_metric}%",
        ["%Percentage%", "%Rate%"]
    )

    values = conn.fetch(query, *substitutes)

    df = DataFrame(
        await values,
        columns=query_data["local_data"]["column_names"]
    )

    df = df.assign(formatted_date=df.date.map(lambda x: f"{x:%-d %B %Y}"))

    return df


async def invalid_postcode_response(request, timestamp, raw_postcode):
    from ..landing.views import get_home_page

    return await get_home_page(
        request=request,
        timestamp=timestamp,
        invalid_postcode=raw_postcode.upper()
    )


async def postcode_page(request, timestamp: str, render=True) -> Union[render_template, DataFrame]:
    postcode_raw = request.query_params["postcode"]
    postcode = get_validated_postcode(postcode_raw)

    async with Connection() as conn:
        data = await get_postcode_data(conn, timestamp, postcode)

    if not data.size:
        return await invalid_postcode_response(request, timestamp, postcode_raw)

    if not render:
        return data

    return await render_template(
        request,
        "html/easy_read.html",
        context={
            "timestamp": timestamp,
            "data": data,
            "postcode": postcode
        }
    )
