SELECT area_name
FROM covid19.area_reference
WHERE
      area_type = $1
  AND area_code = $2
FETCH FIRST 1 ROW ONLY;