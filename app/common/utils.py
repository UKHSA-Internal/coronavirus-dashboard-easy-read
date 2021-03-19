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

# 3rd party:

# Internal:
from ..storage import AsyncStorageClient

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CLOUD_ROLE_NAME = getenv("WEBSITE_SITE_NAME", "landing-page")

get_value = itemgetter("value")
get_area_type = itemgetter("areaType")


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


def add_cloud_role_name(envelope):
    envelope.tags['ai.cloud.role'] = CLOUD_ROLE_NAME
    return True


async def get_release_timestamp():
    latest_published_timestamp = {
        "container": "pipeline",
        "path": "info/latest_published"
    }

    async with AsyncStorageClient(**latest_published_timestamp) as client:
        data = await client.download()
        timestamp = await data.readall()

    return timestamp.decode()
