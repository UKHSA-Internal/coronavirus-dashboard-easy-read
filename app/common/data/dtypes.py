#!/usr/bin python3

"""
<Description of the programme>

Author:        Pouria Hadjibagheri <pouria.hadjibagheri@phe.gov.uk>
Created:       24 Oct 2020
License:       MIT
Contributors:  Pouria Hadjibagheri
"""

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from datetime import datetime
from typing import Dict, Union, List, TypedDict

# 3rd party:

# Internal: 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Header
__author__ = "Pouria Hadjibagheri"
__copyright__ = "Copyright (c) 2020, Public Health England"
__license__ = "MIT"
__version__ = "0.0.1"
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ProcessedDateType = Dict[str, Union[str, datetime]]

NumericType = Union[int, float]

DatabaseValueType = Union[str, Union[str, NumericType, ProcessedDateType]]

DatabaseRowType = Union[
    Dict[str, DatabaseValueType],
    List[DatabaseValueType]
]

DatabaseOutputType = List[DatabaseRowType]


# Area query response
SingleAreaValue = Union[str, None]


class DBArea(TypedDict):
    nation: str
    nationName: str
    nhsTrust: SingleAreaValue
    nhsTrustName: SingleAreaValue
    nhsRegion: str
    nhsRegionName: str
    utla: str
    utlaName: str
    ltla: str
    ltlaName: str
    msoa: SingleAreaValue
    msoaName: SingleAreaValue

