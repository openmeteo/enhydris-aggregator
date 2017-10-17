from copy import deepcopy
import sys

from django import template
from django.conf import settings

from ..management.commands.aggregate import urljoin

register = template.Library()


@register.assignment_tag
def get_originating_url(timeseries_id):
    # Sort SOURCE_DATABASES by ID_OFFSET
    source_databases = deepcopy(
        settings.ENHYDRIS_AGGREGATOR['SOURCE_DATABASES'])
    source_databases.sort(key=lambda x: x['ID_OFFSET'])

    # Find the originating database for this id
    originating_db = None
    for i, source_db in enumerate(source_databases):
        min_id = source_db['ID_OFFSET']
        try:
            max_id = source_databases[i + 1]['ID_OFFSET']
        except IndexError:
            max_id = sys.maxsize
        if timeseries_id > min_id and timeseries_id < max_id:
            originating_db = source_db
            break

    # Return the result
    original_id = timeseries_id - originating_db['ID_OFFSET']
    return urljoin(originating_db['URL'], 'timeseries', 'd',
                   str(original_id) + '/')
