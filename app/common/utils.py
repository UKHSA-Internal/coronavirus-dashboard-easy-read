#!/usr/bin python3

"""
<Description of the programme>

Author:        Pouria Hadjibagheri <pouria.hadjibagheri@phe.gov.uk>
Created:       25 Oct 2020
License:       MIT
Contributors:  Pouria Hadjibagheri
"""

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from os import getenv
from datetime import datetime
from operator import itemgetter
from typing import Dict
from json import loads

# 3rd party:
from flask import current_app as app

# Internal:
from .caching import cache_client
from .data.variables import DestinationMetrics
from ..storage import StorageClient

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CLOUD_ROLE_NAME = getenv("WEBSITE_SITE_NAME", "easy-read")

get_value = itemgetter("value")
get_area_type = itemgetter("areaType")


@cache_client.memoize(60 * 60 * 12)
def get_og_image_names(latest_timestamp: str) -> list:
    ts_python_iso = latest_timestamp[:-2]
    ts = datetime.fromisoformat(ts_python_iso)
    date = ts.strftime("%Y%m%d")
    og_names = [
        f"/downloads/og-images/og-{metric['metric']}_{date}.png"
        for metric in DestinationMetrics.values()
    ]

    og_names.insert(0, f"/downloads/og-images/og-summary_{date}.png")

    return og_names


def get_by_smallest_areatype(items, areatype_getter):
    order = [
        "lsoa",
        "msoa",
        "ltla",
        "utla",
        "region",
        "nhsRegion",
        "nation",
        "overview"
    ]
    area_types = map(areatype_getter, items)

    min_index = len(order) - 1
    result = None

    for item_ind, area_type in enumerate(area_types):
        order_index = order.index(area_type['abbr'])
        if area_type['abbr'] in order and order_index < min_index:
            result = items[item_ind]
            min_index = order_index

    return result


@cache_client.memoize(300)
def get_notification_data(timestamp):
    with StorageClient("publicdata", "assets/cms/changeLog.json") as cli:
        data = cli.download().readall().decode()

    return loads(data)


def get_notification_content(latest_timestamp):
    ts_python_iso = latest_timestamp[:-1]
    ts = datetime.fromisoformat(ts_python_iso)
    timestamp_date = ts.strftime("%Y-%m-%d")
    data = get_notification_data(latest_timestamp)

    for item in data["changeLog"]:
        if item["displayBanner"] is True and item["date"] >= timestamp_date:
            response = {
                "type": item["type"],
                "headline": item["headline"],
                "relativeUrl": item["relativeUrl"]
            }
            return response

    return None


def add_cloud_role_name(envelope):
    envelope.tags['ai.cloud.role'] = CLOUD_ROLE_NAME
    return True
