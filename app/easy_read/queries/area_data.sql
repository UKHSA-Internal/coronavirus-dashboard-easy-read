SELECT ar.area_type, MAX(area_code), priority
FROM covid19.postcode_lookup AS pl
    JOIN covid19.area_reference AS ar ON pl.area_id = ar.id
    JOIN (
        SELECT postcode
        FROM covid19.postcode_lookup AS pl2
            JOIN covid19.area_reference AS ar2 ON ar2.id = pl2.area_id
        WHERE
              area_name ILIKE $1
          AND area_type ILIKE $2
        FETCH FIRST 1 ROW ONLY
    ) AS pc ON pc.postcode = pl.postcode
    JOIN covid19.area_priorities AS ap ON ap.area_type = ar.area_type
WHERE ar.area_type IN ( 'nation', 'utla', 'ltla', 'msoa' )
GROUP BY ar.area_type, priority ORDER BY priority;