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


class Command(BaseCommand):
    help = "Deletes database content and re-creates it by copying " \
        "from the source databases"
    model_names = ('GentityAltCodeType', 'FileType', 'EventType',
                   'StationType', 'InstrumentType', 'Variable', 'TimeZone',
                   'UnitOfMeasurement', 'Person', 'Organization',
                   'PoliticalDivision', 'WaterDivision', 'WaterBasin',
                   'Station', 'GentityAltCode', 'GentityFile', 'GentityEvent',
                   'Overseer', 'Instrument', 'TimeStep', 'Timeseries')

    @transaction.atomic
    def handle(self, *args, **options):
        self.delete_database()
        for source_db in settings.ENHYDRIS_AGGREGATOR['SOURCE_DATABASES']:
            self.copy_source_db(source_db)

    def delete_database(self):
        for model_name in reversed(self.model_names):
            model = models.__dict__[model_name]
            model.objects.all().delete()

    def copy_source_db(self, source_db):
        for model_name in self.model_names:
            self.copy_model(source_db, model_name)

    def copy_model(self, source_db, model_name):
        model = models.__dict__[model_name]
        r = requests.get(urljoin(source_db['URL'], 'api', model_name, ''))
        r.raise_for_status()
        objects = r.json()
        self.reorder(objects)
        for item in objects:
            self.copy_object(model, item, source_db['ID_OFFSET'])

    def copy_object(self, model, item, id_offset):
        many_to_many = {}
        fields = list(item.keys())

        for key in fields:
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
