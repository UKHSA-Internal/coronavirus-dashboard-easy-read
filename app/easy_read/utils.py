#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
import re
from operator import itemgetter
from typing import List, Dict, Union
from functools import lru_cache

# 3rd party:
from flask import current_app as app

# Internal:

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

postcode_pattern = re.compile(r'(^[a-z]{1,2}\d{1,2}[a-z]?\s?\d{1,2}[a-z]{1,2}$)', re.I)
get_value = itemgetter("value")


@lru_cache(maxsize=256)
def get_validated_postcode(params: dict) -> Union[str, None]:
    found = postcode_pattern.search(params.get("postcode", "").strip())

    if found is not None:
        extract = found.group(0)
        return extract

    return None
