SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'covid19'
AND table_name LIKE $1;