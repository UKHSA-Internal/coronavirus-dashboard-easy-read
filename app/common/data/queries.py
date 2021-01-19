#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from datetime import datetime
from typing import Dict
from functools import lru_cache
from json import dumps
from operator import itemgetter
from dataclasses import dataclass
import re

# 3rd party:
from flask import current_app as app
from azure.core.exceptions import AzureError

# Internal:
from . import query_templates as queries
from . import dtypes
from ..caching import cache_client
from ..exceptions import InvalidArea
from ...database import CosmosDB, Collection

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'get_easy_read_data',
    'get_area_data',
    'AreaType'
]


data_db = CosmosDB(Collection.DATA)
lookup_db = CosmosDB(Collection.LOOKUP)
weekly_db = CosmosDB(Collection.WEEKLY)


@dataclass()
class AreaType:
    msoa = "msoa"
    lower_tier_la = "ltla"
    upper_tier_la = "utla"
    region = "region"
    nhs_region = "nhsRegion"
    nhs_trust = "nhsTrust"
    nation = "nation"
    uk = "overview"
    postcode = "postcode"
    trimmed_postcode = "trimmedPostcode"


AreaTypeTable = {
    "ltla": "ltla",
    "utla": "utla",
    "region": "region",
    "nhsRegion": "nhsRegion",
    "nhsTrust": "nhsTrust",
    "nation": "nation",
    "overview": "overview",
    "msoa": "msoa",
    "postcode": "trimmedPostcode",
}


def process_dates(date: str) -> dtypes.ProcessedDateType:
    result: dict = {
        'date': datetime.strptime(date, "%Y-%m-%d"),
    }

    result['formatted'] = result['date'].strftime('%-d %B %Y')

    return result


@cache_client.memoize(60 * 60 * 12)
def get_postcode_areas_from_db(area_type, area_code):
    query = queries.PostcodeAreaCodeLookup.substitute(area_type=area_type)

    params = [
        {"name": "@areaCode", "value": area_code}
    ]

    try:
        result = lookup_db.query(query, params=params)

        if not result:
            raise InvalidArea(f"{area_type} - {area_code}")

        return result.pop()

    except AzureError as err:
        app.logger.exception(err, extra={
            "custom_dimensions": {
                "query": query,
                "query_params": dumps(params)
            }
        })
        raise err


@lru_cache(maxsize=256)
def get_area_data(area_type, area_code) -> dtypes.DBArea:
    query_area_type = AreaTypeTable.get(area_type.lower())

    if query_area_type is None:
        raise InvalidArea(area_type)

    if query_area_type == AreaType.trimmed_postcode:
        area_code = area_code.replace(" ", "")

    area_code = area_code.upper()
    if not re.fullmatch(r"^[A-Z0-9]{6,12}$", area_code):
        raise InvalidArea(area_code)

    return get_postcode_areas_from_db(query_area_type, area_code)


@cache_client.memoize(60 * 60 * 6)
def get_easy_read_data(timestamp, metric_data, **area):
    category = metric_data["category"]
    metric = metric_data['metric']

    area_type = AreaType.uk
    area_code = "K02000001"  # UK code

    if len(area):
        area_type = metric_data["postcode_destination"]

        if category == "vaccinations":
            area_type = AreaType.nation
        elif category in ["admissions", "in_patients", "ventilators"] and area[AreaType.nation][0].upper() != "E":
            area_type = AreaType.nation
        elif category == "deaths" and area[AreaType.nation][0].upper() == "W":
            area_type = AreaType.nation

        area_code = area[area_type]

    query = queries.LatestEasyRead.substitute(metric=metric)

    params = [
        {"name": "@releaseTimestamp", "value": timestamp},
        {"name": "@areaCode", "value": area_code},
        {"name": "@areaType", "value": area_type},
    ]

    getter = itemgetter(0, -1)

    try:
        results = data_db.query(query, params=params)
        results_iter = (
            {**res, **process_dates(res["date"])}
            for res in getter(results)
        )

        return dict(zip(["latest", "previous"], results_iter))

    except (KeyError, IndexError):
        return dict()
