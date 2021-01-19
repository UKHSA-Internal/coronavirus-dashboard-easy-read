#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from functools import wraps
from typing import Union, TypedDict, Dict

# 3rd party:
from flask import render_template, make_response, request, current_app as app, redirect

# Internal:
from ..common.caching import cache_client
from ..common.data.queries import get_easy_read_data, get_area_data, AreaType

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'easy_read',
    'local_easy_read'
]


class SingleMetricType(TypedDict):
    metric: str
    postcode_destination: str
    category: str


MetricsType = Dict[str, SingleMetricType]


metrics: MetricsType = {
    'cases': {
        "metric": 'newCasesByPublishDate',
        "postcode_destination": "ltla",
        "category": "cases"
    },
    'deaths': {
        "metric": 'newDeaths28DaysByPublishDate',
        "postcode_destination": "ltla",
        "category": "deaths"
    },
    'admissions': {
        "metric": 'newAdmissions',
        "postcode_destination": "nhsTrust",
        "category": "admissions"
    },
    'testing': {
        "metric": 'newVirusTests',
        "postcode_destination": "nation",
        "category": "testing"
    },
    'in_patients': {
        "metric": 'hospitalCases',
        "postcode_destination": "nhsRegion",
        "category": "in_patients"
    },
    'ventilators': {
        "metric": 'covidOccupiedMVBeds',
        "postcode_destination": "nhsRegion",
        "category": "ventilators"
    },
    'vaccinations_first': {
        "metric": 'cumPeopleVaccinatedFirstDoseByPublishDate',
        "postcode_destination": "nation",
        "category": "vaccinations"
    },
    'vaccinations_second': {
        "metric": 'cumPeopleVaccinatedSecondDoseByPublishDate',
        "postcode_destination": "nation",
        "category": "vaccinations"
    },
}


def cache_header(max_age: int, **kwargs):
    def decorator(view):
        cacher = cache_client.memoize(max_age, **kwargs)(view)

        @wraps(cacher)
        def wrapper(*args, **kws):
            resp = cacher(*args, **kws)
            return resp.make_conditional(request)

        return wrapper

    return decorator


@cache_client.memoize(60 * 60 * 24)
def process_postcode_request(postcode) -> make_response:
    area = get_area_data(AreaType.postcode, postcode)

    area_type = AreaType.msoa
    area_code = area.get(area_type)
    msoa_name = area.get(f"{area_type}Name")

    if msoa_name is None:
        area_type = AreaType.upper_tier_la
        area_code = area.get(area_type)

    host = request.headers.get("X-Forwarded-Host", "")
    if host:
        host = f"https://{host}"

    resp = redirect(f'{host}/easy_read/{area_type}/{area_code}', code=308)

    return make_response(resp)


@cache_header(60 * 60)
def create_response(timestamp: str, template: str, **data) -> make_response:
    resp = render_template(template, release_timestamp=timestamp, **data)
    return make_response(resp)


@cache_client.memoize(60 * 60)
def from_database(timestamp: str, **area):
    data = {
        key: get_easy_read_data(timestamp, value, **area)
        for key, value in metrics.items()
    }

    return data


def local_easy_read(timestamp: str, area_type: str, area_code: str,
                    template: str = "html/easy_read.html") -> render_template:
    area = get_area_data(area_type, area_code)
    area_type = area_type.lower()
    area_code = area.get(area_type)
    msoa_name = area.get(f'{AreaType.msoa}Name')

    if msoa_name is not None:
        area_name = f"{msoa_name}, {area.get('utlaName')}"
    else:
        area_name = area.get('utlaName')

    data = from_database(timestamp, **area)

    resp = create_response(
        timestamp,
        template,
        area_name=area_name,
        area_code=area_code,
        area_type=area_type,
        **data,
    )

    return resp


def easy_read(timestamp: str, postcode: Union[None, str],
              template: str = "html/easy_read.html") -> render_template:

    area_name = "United Kingdom"

    if postcode is not None:
        return process_postcode_request(postcode)

    data = from_database(timestamp)

    resp = create_response(
        timestamp,
        template,
        area_type=AreaType.uk,
        area_name=area_name,
        **data
    )

    return resp
