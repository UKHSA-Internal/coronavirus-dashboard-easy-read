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
from typing import Union
from datetime import datetime
from os.path import abspath, split as split_path, join as join_path

# 3rd party:
from pandas import DataFrame

# Internal:
from ..database.postgres import Connection
from ..template_processor import render_template

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'get_home_page'
]


curr_dir, _ = split_path(abspath(__file__))
queries_dir = join_path(curr_dir, "queries")

with open(join_path(queries_dir, "overview_data.sql")) as fp:
    overview_data_query = fp.read()


metrics = [
    'newAdmissions',
    'newAdmissionsChange',
    'newAdmissionsChangePercentage',
    'newAdmissionsRollingSum',
    'newAdmissionsDirection',

    'cumPeopleVaccinatedFirstDoseByPublishDate',
    'cumPeopleVaccinatedSecondDoseByPublishDate',

    'newDeaths28DaysByPublishDate',
    'newDeaths28DaysByPublishDateChange',
    'newDeaths28DaysByPublishDateChangePercentage',
    'newDeaths28DaysByPublishDateRollingSum',
    'newDeaths28DaysByPublishDateDirection',
    'newDeaths28DaysByDeathDateRollingRate',

    'newCasesByPublishDate',
    'newCasesByPublishDateChange',
    'newCasesByPublishDateChangePercentage',
    'newCasesByPublishDateRollingSum',
    'newCasesByPublishDateDirection',
    'newCasesBySpecimenDateRollingRate',

    'newVirusTests',
    'newVirusTestsChange',
    'newVirusTestsChangePercentage',
    'newVirusTestsRollingSum',
    'newVirusTestsDirection',

    'transmissionRateMin',
    'transmissionRateMax',
    'transmissionRateGrowthRateMin',
    'transmissionRateGrowthRateMax',

    'hospitalCases',
    'covidOccupiedMVBeds'
]


async def get_landing_data(conn, timestamp):
    ts = datetime.fromisoformat(timestamp.replace("5Z", ""))
    query = overview_data_query.format(partition=f"{ts:%Y_%-m_%-d}_other")

    values = conn.fetch(query, ts, metrics)

    df = DataFrame(
        await values,
        columns=["areaCode", "areaType", "areaName", "date", "metric", "value", "rank"]
    )

    df = df.assign(formatted_date=df.date.map(lambda x: f"{x:%-d %B %Y}"))

    return df


async def get_home_page(request, timestamp: str, invalid_postcode=None, render=True) -> Union[render_template, DataFrame]:
    async with Connection() as conn:
        data = await get_landing_data(conn, timestamp)

    if not render:
        return data

    return await render_template(
        request,
        "html/easy_read.html",
        context={
            "timestamp": timestamp,
            "data": data,
            "invalid_postcode": invalid_postcode
        }
    )
