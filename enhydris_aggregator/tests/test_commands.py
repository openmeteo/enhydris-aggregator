from django.core.management import call_command
from django.test import override_settings, TestCase

from enhydris.hcore import models

from .mocks import get_free_port, start_mock_server


class TestAggregate(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mock_server_port = get_free_port()
        start_mock_server(cls.mock_server_port)

    def test_aggregate(self):
        config = {
            'SOURCE_DATABASES': [{
                'URL': 'http://localhost:{}/'.format(self.mock_server_port),
                'ID_OFFSET': 10000,
            }],
        }
        with override_settings(ENHYDRIS_AGGREGATOR=config):
            call_command('aggregate')
            # Do it a second time to ensure db deletion
            call_command('aggregate')

        # Stations
        self.assertEqual(models.Station.objects.count(), 2)
        self.assertEqual(models.Station.objects.get(pk=11403).name,
                         'Agios Spiridonas')
        self.assertEqual(models.Station.objects.get(pk=11360).stype.count(), 1)
        self.assertEqual(
            models.Station.objects.get(pk=11360).stype.all()[0].descr,
            'Stage - Hydrometric')

        # GentityAltCodeType
        self.assertEqual(models.GentityAltCodeType.objects.count(), 2)
        self.assertEqual(models.GentityAltCodeType.objects.get(pk=10003).descr,
                         'Hydroscope')

        # Organizations
        self.assertEqual(models.Organization.objects.count(), 2)
        self.assertEqual(models.Organization.objects.get(pk=10009).name,
                         'Deukalion')

        # StationType
        self.assertEqual(models.StationType.objects.count(), 2)
        self.assertEqual(models.StationType.objects.get(pk=10001).descr,
                         'Meteorological')

        # PoliticalDivision
        self.assertEqual(models.PoliticalDivision.objects.count(), 4)
        self.assertEqual(models.PoliticalDivision.objects.get(pk=10306).name,
                         'ΗΠΕΙΡΟΥ')

        # WaterDivision
        self.assertEqual(models.WaterDivision.objects.count(), 2)
        self.assertEqual(models.WaterDivision.objects.get(pk=10501).name,
                         'ΔΥΤΙΚΗ ΠΕΛΟΠΟΝΝΗΣΟΣ')

        # WaterBasin
        self.assertEqual(models.WaterBasin.objects.count(), 1)
        self.assertEqual(models.WaterBasin.objects.get(pk=11353).name,
                         'Νέδοντας')

        # Timeseries
        self.assertEqual(models.Timeseries.objects.count(), 1)
        self.assertEqual(models.Timeseries.objects.get(pk=19206).name,
                         'Air temperature')

        # Variable
        self.assertEqual(models.Variable.objects.count(), 1)
        self.assertEqual(models.Variable.objects.get(pk=15683).descr,
                         'Temperature')

        # UnitOfMeasurement
        self.assertEqual(models.UnitOfMeasurement.objects.count(), 1)
        self.assertEqual(models.UnitOfMeasurement.objects.get(pk=10014).descr,
                         'Celsius degrees')

        # TimeZone
        self.assertEqual(models.TimeZone.objects.count(), 1)
        self.assertEqual(models.TimeZone.objects.get(pk=10001).utc_offset, 120)

        # TimeStep
        self.assertEqual(models.TimeStep.objects.count(), 1)
        self.assertEqual(models.TimeStep.objects.get(pk=10007).descr,
                         'Quarter')

        # Instrument
        self.assertEqual(models.Instrument.objects.count(), 1)
        self.assertEqual(models.Instrument.objects.get(pk=10019).station.id,
                         11360)

        # InstrumentType
        self.assertEqual(models.InstrumentType.objects.count(), 1)
        self.assertEqual(models.InstrumentType.objects.get(pk=10023).descr,
                         'Thermograph')

        # GentityEvent
        self.assertEqual(models.GentityEvent.objects.count(), 1)
        self.assertEqual(models.GentityEvent.objects.get(pk=10586).gentity.id,
                         11360)

        # GentityEventType
        self.assertEqual(models.EventType.objects.count(), 1)
        self.assertEqual(models.EventType.objects.get(pk=10004).descr,
                         'Station Malfunction')

        # GentityFile
        self.assertEqual(models.GentityFile.objects.count(), 1)
        self.assertEqual(models.GentityFile.objects.get(pk=10052).descr,
                         'Photo 1')

        # FileType
        self.assertEqual(models.FileType.objects.count(), 1)
        self.assertEqual(models.FileType.objects.get(pk=10001).descr,
                         'jpg Picture')
