from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deletes database content and re-creates it by copying " \
        "from the source databases"

    def handle(self, *args, **options):
        pass
