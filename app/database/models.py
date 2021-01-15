#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from hashlib import blake2b
from typing import Union, Dict, List

# 3rd party:

# Internal:

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class QueryCosmos:
    def __init__(self):
        pass


class BaseModel:
    _ordering = list()
    _params = list()
    _metrics: Union[Dict[str, str], List[str]] = None
    _total = None
    _is_defined = list()

    def __init__(self):
        pass

    def all(self, metrics, total=None):
        self._metrics = {
            metric: f"c.{metric}" for metric in metrics
        }
        self._total = total

    def is_defined(self, *metrics):
        self._is_defined = metrics
        return self

    def list(self,):
        self._metrics = list(self._metrics.values())

    def order_by(self, metric):
        self._ordering.append(metric)
        return self

    def filter(self, **filters):
        for key, value in filters.items():
            self._params.append({
                "name": f"@{key}{blake2b(value).hexdigest()}",
                "value": value
            })

        return self
