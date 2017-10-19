from copy import deepcopy
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import FileField

from enhydris.hcore import models

import requests


def urljoin(*args):
    result = '/'.join([s.strip('/') for s in args])
    if args[-1].endswith('/'):
        result += '/'
    return result


# This is Enhydris 0.2 compatibility stuff. Delete it when this compatibility
# is broken.
_interval_types = [
    {
        "id": 2,
        "last_modified": "2013-12-03T18:16:21.546470+02:00",
        "descr": "Average value",
        "descr_alt": "Average value",
        "value": "AVERAGE"
    },
    {
        "id": 4,
        "last_modified": "2013-12-03T18:16:21.546470+02:00",
        "descr": "Maximum",
        "descr_alt": "Maximum",
        "value": "MAXIMUM"
    },
    {
        "id": 3,
        "last_modified": "2013-12-03T18:16:21.546470+02:00",
        "descr": "Minimum",
        "descr_alt": "Minimum",
        "value": "MINIMUM"
    },
    {
        "id": 1,
        "last_modified": "2013-12-03T18:16:21.546470+02:00",
        "descr": "Sum",
        "descr_alt": "Sum",
        "value": "SUM"
    },
    {
        "id": 5,
        "last_modified": "2013-12-03T18:16:21.546470+02:00",
        "descr": "Vector average",
        "descr_alt": "Vector average",
        "value": "VECTOR_AVERAGE"
    },
]


class Command(BaseCommand):
    help = "Deletes database content and re-creates it by copying " \
        "from the source databases"
    model_names = ('GentityAltCodeType', 'FileType', 'EventType',
                   'IntervalType', 'StationType', 'InstrumentType', 'Variable',
                   'TimeZone', 'UnitOfMeasurement', 'Person', 'Organization',
                   'PoliticalDivision', 'WaterDivision', 'WaterBasin',
                   'Station', 'GentityAltCode', 'GentityFile', 'GentityEvent',
                   'Overseer', 'Instrument', 'TimeStep', 'Timeseries')

    def handle(self, *args, **options):
        # Sort SOURCE_DATABASES by ID_OFFSET
        source_databases = deepcopy(
            settings.ENHYDRIS_AGGREGATOR['SOURCE_DATABASES'])
        source_databases.sort(key=lambda x: x['ID_OFFSET'])

        for i, source_db in enumerate(source_databases):
            min_id = source_db['ID_OFFSET']
            try:
                max_id = source_databases[i + 1]['ID_OFFSET']
            except IndexError:
                max_id = sys.maxsize
            try:
                with transaction.atomic():
                    self.delete_from_database(min_id, max_id)
                    self.copy_source_db(source_db)
            except Exception as e:
                # We have already rolled back; log the problem and continue
                # to the next source database
                print(
                    'Error while copying database {}'.format(source_db['URL']),
                    file=sys.stderr)
                print(str(e), file=sys.stderr)

    def copy_source_db(self, source_db):
        for model_name in self.model_names:
            self.copy_model(source_db, model_name)

    def delete_from_database(self, min_id, max_id):
        for model_name in reversed(self.model_names):
            model = getattr(models, model_name)
            model.objects.filter(id__gte=min_id, id__lte=max_id).delete()

    def copy_model(self, source_db, model_name):
        model = getattr(models, model_name)

        try:
            r = requests.get(urljoin(source_db['URL'], 'api', model_name, ''))
            r.raise_for_status()
            objects = r.json()
        except requests.HTTPError:
            # Quick hack: Enhydris 0.2 has a bug; it does not serve
            # IntervalType through the API (this was fixed in 1af68be). If we
            # come across such a problem, we pretend that the API responded
            # with the contents of IntervalType, which are the same in all
            # known installations.
            if model_name != 'IntervalType':
                raise
            objects = _interval_types
        self.reorder(objects)
        for item in objects:
            self.copy_object(model, item, source_db['ID_OFFSET'])

    def __rename_field(self, old_prefix, new_prefix, item, key):
        if not key.startswith(old_prefix):
            return key
        new_key = new_prefix + key[len(old_prefix):]
        item[new_key] = item[key]
        del item[key]
        return new_key

    def copy_object(self, model, item, id_offset):
        many_to_many = {}
        fields = list(item.keys())

        for key in fields:
            # Ignore obsolete fields from source databases with older
            # Enhydris versions. Also ignore last_modified because it causes
            # too many warnings and is most probably useless anyway (and may
            # be removed in the future).
            if key in ('original_id', 'original_db', 'is_active',
                       'last_modified'):
                del item[key]
                continue

            # Take care about fields that have been renamed from older Enhydris
            # versions
            key = self.__rename_field('nominal_offset_', 'timestamp_rounding_',
                                      item, key)
            key = self.__rename_field('actual_offset_', 'timestamp_offset_',
                                      item, key)

            field = model._meta.get_field(key)

            # Append _id to foreign key field names
            if field.many_to_one or field.one_to_one:
                item[key + '_id'] = item[key]
                del item[key]

            # Save ManyToMany fields for later
            if field.many_to_many:
                many_to_many[key] = item[key]
                del item[key]

            # Ignore file fields (these are in the original database only)
            field = model._meta.get_field(key)
            if isinstance(field, FileField):
                del item[key]

        # Add offset to id and all fields ending in _id
        for key in item.keys():
            if key != 'id' and not key.endswith('_id'):
                continue
            if item[key] is None:
                continue
            item[key] += id_offset

        # Save to database
        new_model_instance = model(**item)
        new_model_instance.save()

        # Add many-to-many relationships
        for m2m in many_to_many:
            many_to_many[m2m] = [x + id_offset for x in many_to_many[m2m]]
            field = model._meta.get_field(m2m)

            # Skip relationships with "through", they are taken care of
            # elsewhere
            if not field.rel.through._meta.auto_created:
                continue

            for m2m_item in many_to_many[m2m]:
                o = field.related_model.objects.get(pk=m2m_item)
                getattr(new_model_instance, m2m).add(o)

    def reorder(self, objects):
        """Re-order so that foreign keys do not refer to nonexistent objects.
        objects is a list of dictionaries. If these objects contain a "parent"
        key, it is assumed to be a self reference. The list is reordered
        in place so that such references refer to preceding objects.
        """
        if (len(objects) <= 1) or ('parent' not in objects[0]):
            return
        seen_ids = set()
        i = 0
        while i < len(objects):
            obj = objects[i]

            # If no problem, then no problem
            if obj['parent'] is None or obj['parent'] in seen_ids:
                i += 1
                seen_ids.add(obj['id'])
                continue

            # Find the referent
            j = i + 1
            while j < len(objects):
                if objects[j]['id'] == obj['parent']:
                    break
                j += 1

            # Swap them
            objects[i], objects[j] = objects[j], objects[i]
