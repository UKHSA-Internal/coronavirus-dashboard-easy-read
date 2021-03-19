#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from http import HTTPStatus

# 3rd party:
# from werkzeug.exceptions import HTTPException
# from flask import render_template, Response

# Internal: 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'InvalidPostcode',
    'HandledException',
    'InvalidArea'
]


class HandledException(object):
    template = None
    template_kws = dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_body(self, environ=None):
        code = getattr(self, "code", 500)

        return render_template(
            self.template,
            **self.template_kws,
            response_code=code,
            response_message=HTTPStatus(code).phrase
        )


class InvalidPostcode(HandledException):
    code = 400
    message_template = 'Invalid postcode: "{postcode}"'
    template = "html/errors/40x.html"

    def __init__(self, postcode):
        self.postcode = postcode
        self.template_kws = {
            'invalid_postcode': True,
            'error_message': self.message
        }
        super().__init__(description=self.message)

    @property
    def message(self):
        return self.message_template.format(postcode=self.postcode)


class InvalidArea(HandledException):
    code = 404
    message_template = 'Invalid {area_name}: "{area}"'
    template = "html/errors/40x.html"

    def __init__(self, area, area_name="area"):
        self.area = area
        self.template_kws = {
            'invalid_postcode': True,
            'error_message': self.message
        }
        super().__init__(area_name=area_name, description=self.message)

    @property
    def message(self):
        return self.message_template.format(area=self.area)
