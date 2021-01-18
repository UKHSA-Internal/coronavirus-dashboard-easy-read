#!/usr/bin python3

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from os import getenv
from ...config import Config

# 3rd party:
import certifi
from flask_caching import Cache

# Internal: 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'cache_client'
]


ENVIRONMENT = getenv("API_ENV", "PRODUCTION")

cache_config = {
    "CACHE_TYPE": "redis",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "easy-read::",
    "CACHE_OPTIONS": {
        "ssl": True,
        "ssl_ca_certs": certifi.where()
    },
    "CACHE_REDIS_HOST": getenv(f"AZURE_REDIS_HOST"),
    "CACHE_REDIS_PORT": int(getenv(f"AZURE_REDIS_PORT")),
    "CACHE_REDIS_PASSWORD": getenv(f"AZURE_REDIS_PASSWORD"),
    "CACHE_REDIS_DB": 0
}


if Config.DEBUG:
    cache_config = {
        "CACHE_TYPE": "null",
    }


cache_client = Cache(config=cache_config)



# from opencensus.trace.tracer import Tracer
# from opencensus.ext.azure.trace_exporter
#
# config_integration.trace_integrations(['requests'])  # <-- this line enables the requests integration
#
# tracer = Tracer(exporter=AzureExporter(connection_string="InstrumentationKey=<your-ikey-here>"), sampler=ProbabilitySampler(1.0))
#
# with tracer.span(name='parent') as span:
#     span.attributes.
#     response = requests.get(url='https://www.wikipedia.org/wiki/Rabbit') # <-- this request will be tracked
#
#
# with tracer.span(name='covid19pubdashprod-uksouth.documents.azure.com') as s: #
#     s.add_attribute("myattributekey", "1337")
#     s.add_attribute("aString", "Hello World")
#     time.sleep(3)
#     s.add_attribute('component', 'Azure DocumentDB')
#     s.span_kind = 2
#     logger.info('Query to cosmos')

# Trace ID: Operation ID
# Span ID: Parent ID
