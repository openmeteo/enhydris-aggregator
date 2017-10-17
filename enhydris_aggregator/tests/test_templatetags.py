import sys

from django.core.management import call_command
from django.test import override_settings, TestCase

from enhydris_aggregator.management.commands import aggregate

from .mocks import start_mock_server

_mock_server_port = start_mock_server()
_config = {
    'SOURCE_DATABASES': [{
        'URL': 'http://localhost:{}/'.format(_mock_server_port),
        'ID_OFFSET': 10000,
    }, {
        'URL': 'http://localhost:{}/'.format(_mock_server_port),
        'ID_OFFSET': 20000,
    }, {
        'URL': 'http://localhost:{}/'.format(_mock_server_port),
        'ID_OFFSET': 30000,
    }],
}


@override_settings(ENHYDRIS_AGGREGATOR=_config)
class TestGetOriginatingUrl(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('aggregate')

    @classmethod
    def tearDownClass(cls):
        # Delete database contents
        c = aggregate.Command()
        c.delete_from_database(0, sys.maxsize)

    def test_get_originating_url(self):
        r = self.client.get('/timeseries/d/19206/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(
            r,
            'http://localhost:{}/timeseries/d/9206/'.format(_mock_server_port),
        )

        r = self.client.get('/timeseries/d/29206/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(
            r,
            'http://localhost:{}/timeseries/d/9206/'.format(_mock_server_port),
        )

        r = self.client.get('/timeseries/d/39206/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(
            r,
            'http://localhost:{}/timeseries/d/9206/'.format(_mock_server_port),
        )
