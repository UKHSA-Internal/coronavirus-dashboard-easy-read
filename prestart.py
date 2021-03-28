#!/usr/bin python3

from os import getenv


location = getenv("URL_LOCATION")

with open('/opt/hosts.nginx', 'r') as fp:
    config = fp.read()


config = config.replace("${URL_LOCATION}", location)

with open('/opt/hosts.nginx', 'w') as fp:
    print(config, file=fp)
