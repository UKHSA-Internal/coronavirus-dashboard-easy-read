#!/usr/bin python3

from os import getenv


location = getenv("URL_LOCATION")

with open('/etc/nginx/conf.d/engine.conf', 'r') as fp:
    config = fp.read()


config = config.replace("${URL_LOCATION}", location)

with open('/etc/nginx/conf.d/engine.conf', 'w') as fp:
    print(config, file=fp)
