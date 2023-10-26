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

with open(join_path(queries_dir, "table_names.sql")) as fp_tables:
    table_names_query = fp_tables.read()

virus_test_metrics = [
    'newVirusTestsByPublishDate',
    'newVirusTestsByPublishDateChange',
    'newVirusTestsByPublishDateChangePercentage',
    'newVirusTestsByPublishDateRollingSum',
    'newVirusTestsByPublishDateDirection',
]


metrics = [
    'newAdmissions',
    'newAdmissionsChange',
    'newAdmissionsChangePercentage',
    'newAdmissionsRollingSum',
    'newAdmissionsDirection',

    'cumPeopleVaccinatedSpring23ByVaccinationDate75plus',

    'newDailyNsoDeathsByDeathDateChange',
    'newDailyNsoDeathsByDeathDateRollingSum',
    'newDailyNsoDeathsByDeathDateChangePercentage',
    'newDailyNsoDeathsByDeathDateDirection',
    'newDailyNsoDeathsByDeathDate',

    'newCasesBySpecimenDate',
    'newCasesBySpecimenDateChange',
    'newCasesBySpecimenDateChangePercentage',
    'newCasesBySpecimenDateRollingSum',
    'newCasesBySpecimenDateDirection',
    'newCasesBySpecimenDateRollingRate',

    *virus_test_metrics,

    'transmissionRateMin',
    'transmissionRateMax',
    'transmissionRateGrowthRateMin',
    'transmissionRateGrowthRateMax',

    'hospitalCases',
    'covidOccupiedMVBeds'
]


async def get_latest_records(conn: Connection, record_metrics, pattern):
    # Get a list of tables that match the pattern
    records = await conn.fetch(table_names_query, pattern)
    tables = [record[0] for record in records]

    # Sort tables based on the date in their name
    def extract_date(tname):
        match = re.search(r'(\d{4}_\d{1,2}_\d{1,2})', tname)
        if match:
            date_parts = match.group(1).split("_")
            return "-".join([date_parts[0], date_parts[1].zfill(2), date_parts[2].zfill(2)])
        return ''
    tables.sort(key=extract_date, reverse=True)

    # Query each table for the latest row with metric = 'newBat'
    for table in tables:
        table_date = extract_date(table).replace("_", "-")
        ts = datetime.fromisoformat(table_date.replace("5Z", ""))
        query = overview_data_query.format(partition=f"{ts:%Y_%-m_%-d}_other")
        # query = overview_data_query.format(partition="{:%Y}_{:n}_{:n}_other".format(ts, ts.month, ts.day))

        result = await conn.fetch(query, ts, record_metrics)
        if result:
            return result
    return None


async def get_landing_data(conn, timestamp):
    ts = datetime.fromisoformat(timestamp.replace("5Z", ""))
    query = overview_data_query.format(partition=f"{ts:%Y_%-m_%-d}_other")

    # Get latest available virus test records
    values = await conn.fetch(query, ts, metrics)
    if not any(val['metric'] == virus_test_metrics[0] for val in values):
        values_virus_test = await get_latest_records(conn, virus_test_metrics, pattern="time_series_p%_other")
        if values_virus_test:
            values += values_virus_test

    df = DataFrame(
        values,
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
            "invalid_postcode": invalid_postcode,
        }
    )
