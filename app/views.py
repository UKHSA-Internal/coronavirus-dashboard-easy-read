#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:

# 3rd party:

# Internal:
from app.template_processor import render_template
from app.common.utils import get_release_timestamp
from app.landing.views import get_home_page
from app.postcode.views import postcode_page

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


async def base_router(request) -> render_template:
    timestamp = await get_release_timestamp()

    if "postcode" in request.query_params:
        return await postcode_page(request, timestamp)

    return await get_home_page(request, timestamp)
