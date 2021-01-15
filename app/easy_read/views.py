#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:

# 3rd party:
from flask import render_template, make_response, request, g, current_app as app, redirect


# Internal:
from .utils import get_validated_postcode
from ..common.data.queries import get_easy_read_data, get_area_data, AreaType

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'easy_read',
    'local_easy_read'
]


metrics = {
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


def local_easy_read(area_type, area_code) -> render_template:
    if request.method == "HEAD":
        return make_response("", 200)

    area = get_area_data(area_type, area_code)

    area_name = area.get(f"{area_type}Name")

    data = {
        key: get_easy_read_data(g.timestamp, value, area)
        for key, value in metrics.items()
    }

    return render_template(
        "easy_read.html",
        area_name=area_name,
        **data,
    )


def easy_read() -> render_template:
    if request.method == "HEAD":
        return make_response("", 200)

    postcode = get_validated_postcode(request.args)
    area_name = "United Kingdom"

    if postcode is not None:
        area = get_area_data(AreaType.postcode, postcode)
        area_type = "msoa"

        if area_name is None:
            area_type = "ltla"

        return redirect(f'/easy_read/{area_type}/{area.get(area_type)}', code=308)

    data = {
        key: get_easy_read_data(g.timestamp, value)
        for key, value in metrics.items()
    }

    return render_template(
        "easy_read.html",
        area_name=area_name,
        **data,
    )
