#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from string import Template

# 3rd party:

# Internal:

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    "LatestEasyRead",
    "PostcodeAreaCodeLookup",
    "HealthCheck"
]


HealthCheck = """\
SELECT TOP 1 *
FROM c 
WHERE c.type = 'general'\
"""


PostcodeAreaCodeLookup = Template("""\
SELECT TOP 1 *
FROM     c
WHERE    c.type         = 'postcode'
     AND c.${area_type} = @areaCode\
""")


LatestEasyRead = Template("""\
SELECT TOP 7 VALUE {
        'date':       c.date, 
        'areaName':   c.areaName,
        'value':      c.$metric,
        'rollingSum': c.${metric}RollingSum ?? null,
        'change':     c.${metric}Change ?? null,
        'percentage': ABS(c.${metric}ChangePercentage) ?? null
    }
FROM     c
WHERE    c.releaseTimestamp = @releaseTimestamp
     AND c.areaType         = @areaType
     AND c.areaCode         = @areaCode
     AND IS_DEFINED(c.$metric)
ORDER BY 
    c.date DESC\
""")
