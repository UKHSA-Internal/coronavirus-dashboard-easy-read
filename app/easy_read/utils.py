#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
import re
from operator import itemgetter
from typing import Union

# 3rd party:

# Internal:

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'get_validated_postcode'
]


postcode_pattern = re.compile(r'(^[a-z]{1,2}\d{1,2}[a-z]?\s?\d{1,2}[a-z]{1,2}$)', re.I)
get_value = itemgetter("value")


# @lru_cache(maxsize=256)
def get_validated_postcode(params: dict) -> Union[str, None]:
    found = postcode_pattern.search(params.get("postcode", "").strip())

    if found is not None:
        extract = found.group(0)
        return extract

    return None


def get_latest_test_record(conn_str, query, wildcard_name="time_series_p*_other"):
    # Connect to the database
    with psycopg2.connect(conn_str) as conn:
        with conn.cursor() as cur:
            # Get a list of tables that match the wildcard name
            query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'covid19'
            AND table_name LIKE %s;
            """
            cur.execute(query, (wildcard_name.replace("*", "%"),))
            tables = [record[0] for record in cur.fetchall()]
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
                print(table)
                table_date = extract_date(table).replace("_", "-")
                query = f"""
SELECT
    *
FROM (
    SELECT area_code    AS "areaCode",
         MAX(area_type) AS "areaType",
         MAX(area_name) AS "areaName",
         MAX(date)      AS "date",
         metric,
         MAX(
             CASE
                WHEN (payload ->> 'value')::TEXT = 'UP'   THEN 0
                WHEN (payload ->> 'value')::TEXT = 'DOWN' THEN 180
                WHEN (payload ->> 'value')::TEXT = 'SAME' THEN 90
                ELSE (payload ->> 'value')::NUMERIC
            END
         ) AS value,
         RANK() OVER (
            PARTITION BY (metric)
            ORDER BY date DESC
         ) AS rank
    FROM covid19.{table}   AS main
    JOIN covid19.release_reference AS rr ON rr.id = release_id
    JOIN covid19.metric_reference  AS mr ON mr.id = metric_id
    JOIN covid19.area_reference    AS ar ON ar.id = main.area_id
    WHERE
          area_type = 'nation'
      AND area_name = 'England'
      AND date > ( DATE('{table_date}') - INTERVAL '56 days' )
      AND metric = ANY( '{{newVirusTestsByPublishDate,newVirusTestsByPublishDateChange,newVirusTestsByPublishDateChangePercentage,newVirusTestsByPublishDateRollingSum,newVirusTestsByPublishDateDirection}}'::VARCHAR[] )
    GROUP BY area_type, area_code, date, metric
) AS result
WHERE result.rank = 1;
                """
                cur.execute(query)
                result = cur.fetchall()
                if result:
                    return result
    return None
