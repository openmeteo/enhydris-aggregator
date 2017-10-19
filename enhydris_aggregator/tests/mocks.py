from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
from threading import Thread

import requests


mock_responses = {
    # Persons
    'Person/42/': {
        'id': 42,
        'last_name': 'Christofides',
        'first_name': 'Antonis',
        'middle_names': '',
        'initials': '',
        'last_name_alt': '',
        'first_name_alt': '',
        'middle_names_alt': '',
        'initials_alt': '',
    },

    # Stations
    'Station/1403/': {
        'id': 1403,
        'last_modified': '2015-06-02T10:29:57.718660Z',
        'name': 'Agios Spiridonas',
        'short_name': '',
        'remarks': 'ADCON S06. Installed in the framework of project IRMA',
        'name_alt': '',
        'short_name_alt': '',
        'remarks_alt': 'ADCON S06. Εγκαταστάθηκε στο πλαίσιο του IRMA',
        'srid': 4326,
        'approximate': False,
        'altitude': 10.0,
        'asrid': None,
        'point': 'SRID=4326;POINT (20.8759100000000011 39.1490399999999994)',
        'is_automatic': False,
        'start_date': None,
        'end_date': None,
        'copyright_holder': 'Decentralised Administration of Epirus',
        'copyright_years': '2015',
        'water_basin': None,
        'water_division': 505,
        'political_division': 306,
        'owner': 12,
        'stype': [
            1
        ],
        'overseers': [42],
        'maintainers': [],
    },
    'Station/1360/': {
        'id': 1360,
        'last_modified': '2013-01-18T14:03:41.696092Z',
        'name': 'Alagonia - Rentifis watermill',
        'short_name': '',
        'remarks': '',
        'name_alt': 'Αλαγονία - Νερόμυλος Ρεντίφη',
        'short_name_alt': '',
        'remarks_alt': 'Ο σταθμηγράφος έχει τοποθετηθεί σε αναβαθμό',
        'srid': 2100,
        'approximate': False,
        'altitude': 576.0,
        'asrid': None,
        'point': 'SRID=4326;POINT (22.2319696063634957 37.1041812433745832)',
        'is_automatic': True,
        'start_date': '2012-02-01',
        'end_date': None,
        'copyright_holder': 'National Observatory of Athens',
        'copyright_years': '2012',
        'water_basin': 1353,
        'water_division': 501,
        'political_division': 412,
        'owner': 9,
        'stype': [
            2
        ],
        'overseers': [],
        'maintainers': [],

        # For compatibility with source databases with Enhydris<=0.5
        'is_active': True,
    },

    # GentityAltCodes
    'GentityAltCodeType/3/': {
        'id': 3,
        'last_modified': '2011-06-22T05:05:33.513723Z',
        'descr': 'Hydroscope',
        'descr_alt': 'Υδροσκόπιο',
    },
    'GentityAltCodeType/5/': {
        'id': 5,
        'last_modified': '2012-06-22T05:05:33.513723Z',
        'descr': 'Other',
        'descr_alt': 'Άλλος',

        # Source database may be Enhydris 0.2. Make sure we aren't being
        # confused by the extra fields.
        'original_db': None,
        'original_id': None,
    },

    # GentityAltCode
    'GentityAltCode/47/': {
        'id': 47,
        'gentity': 1403,
        'type': 5,
        'value': 'A525',
    },

    # Overseer
    'Overseer/37/': {
        'id': 37,
        'station': 1403,
        'person': 42,
        'is_current': True,
    },

    # Organizations
    'Organization/9/': {
        'id': 9,
        'last_modified': '2011-12-15T12:35:47.266705Z',
        'remarks': '',
        'remarks_alt': '',
        'ordering_string': 'Deukalion',
        'name': 'Deukalion',
        'acronym': '',
        'name_alt': 'Δευκαλίων',
        'acronym_alt': '',
    },
    'Organization/12/': {
        'id': 12,
        'last_modified': '2013-10-10T04:57:21.109870Z',
        'remarks': '',
        'remarks_alt': '',
        'ordering_string': 'Hellenic Centre for Marine Research',
        'name': 'Hellenic Centre for Marine Research',
        'acronym': 'HCMR',
        'name_alt': 'Ελληνικό Κέντρο Θαλάσσιων Ερευνών',
        'acronym_alt': 'ΕΛΚΕΘΕ',
    },

    # Station types
    'StationType/1/': {
        'id': 1,
        'last_modified': '2011-06-22T05:21:32.781442Z',
        'descr': 'Meteorological',
        'descr_alt': 'Μετεωρολογικός',
    },
    'StationType/2/': {
        'id': 2,
        'last_modified': '2011-06-22T05:21:23.577317Z',
        'descr': 'Stage - Hydrometric',
        'descr_alt': 'Υδρομετρικός',
    },

    # Political divisions
    'PoliticalDivision/306/': {
        'id': 306,
        'last_modified': None,
        'name': 'ΗΠΕΙΡΟΥ',
        'short_name': 'ΗΠΕΙΡΟΥ',
        'remarks': '',
        'name_alt': '',
        'short_name_alt': '',
        'remarks_alt': '',
        'area': None,
        'mpoly': None,
        'code': '',
        'water_basin': None,
        'water_division': None,
        'political_division': None,
        'parent': 84,
    },
    'PoliticalDivision/412/': {
        'id': 412,
        'last_modified': None,
        'name': 'ΜΕΣΣΗΝΙΑΣ',
        'short_name': 'ΜΕΣΣΗΝΙΑ',
        'remarks': '',
        'name_alt': '',
        'short_name_alt': '',
        'remarks_alt': '',
        'area': None,
        'mpoly': None,
        'code': '',
        'water_basin': None,
        'water_division': None,
        'political_division': None,
        'parent': 301,
    },
    'PoliticalDivision/84/': {
        'id': 84,
        'last_modified': None,
        'name': 'GREECE',
        'short_name': 'GREECE',
        'remarks': '',
        'name_alt': 'GREECE',
        'short_name_alt': 'GREECE',
        'remarks_alt': '',
        'area': None,
        'mpoly': None,
        'code': 'GR',
        'water_basin': None,
        'water_division': None,
        'political_division': None,
        'parent': None,
    },
    'PoliticalDivision/301/': {
        'id': 301,
        'last_modified': None,
        'name': 'ΠΕΛΟΠΟΝΝΗΣΟΥ',
        'short_name': 'ΠΕΛΟΠΟΝΝΗΣΟΥ',
        'remarks': '',
        'name_alt': '',
        'short_name_alt': '',
        'remarks_alt': '',
        'area': None,
        'mpoly': None,
        'code': '',
        'water_basin': None,
        'water_division': None,
        'political_division': None,
        'parent': 84
    },

    # Water divisions
    'WaterDivision/505/': {
        'id': 505,
        'last_modified': None,
        'name': 'ΗΠΕΙΡΟΣ',
        'short_name': 'ΗΠΕΙΡΟΣ',
        'remarks': '',
        'name_alt': '',
        'short_name_alt': '',
        'remarks_alt': '',
        'area': None,
        'mpoly': None,
        'water_basin': None,
        'water_division': None,
        'political_division': None,
    },
    'WaterDivision/501/': {
        'id': 501,
        'last_modified': None,
        'name': 'ΔΥΤΙΚΗ ΠΕΛΟΠΟΝΝΗΣΟΣ',
        'short_name': 'Δ-ΠΕΛΟΠ',
        'remarks': '',
        'name_alt': '',
        'short_name_alt': '',
        'remarks_alt': '',
        'area': None,
        'mpoly': None,
        'water_basin': None,
        'water_division': None,
        'political_division': None,
    },

    # Water basins
    'WaterBasin/1353/': {
        'id': 1353,
        'last_modified': '2012-01-23T13:12:09.378770Z',
        'name': 'Νέδοντας',
        'short_name': 'Νέδοντας',
        'remarks': '',
        'name_alt': 'Nedontas',
        'short_name_alt': '',
        'remarks_alt': '',
        'area': None,
        'mpoly': None,
        'water_basin': None,
        'water_division': 501,
        'political_division': 412,
        'parent': None,
    },

    # Timeseries
    'Timeseries/9206/': {
        'id': 9206,
        'last_modified': '2012-06-12T13:57:56.307020Z',
        'name': 'Air temperature',
        'name_alt': 'Θερμοκρασία αέρα',
        'hidden': False,
        'precision': 1,
        'remarks': '',
        'remarks_alt': '',
        'timestamp_rounding_minutes': None,
        'timestamp_rounding_months': None,
        'timestamp_offset_minutes': 0,
        'timestamp_offset_months': 0,
        'datafile': 'http://some.place.com/some/file',
        'start_date_utc': '2012-02-01T14:00:00Z',
        'end_date_utc': '2013-07-06T17:15:00Z',
        'gentity': 1360,
        'variable': 5683,
        'unit_of_measurement': 14,
        'time_zone': 1,
        'instrument': None,
        'time_step': 7,
        'interval_type': 18,
    },
    'Timeseries/9207/': {
        'id': 9207,
        'last_modified': '2012-06-12T13:57:56.307020Z',
        'name': 'Air temperature',
        'name_alt': 'Θερμοκρασία αέρα',
        'hidden': False,
        'precision': 1,
        'remarks': '',
        'remarks_alt': '',

        # Check compatibility with older Enhydris versions
        'nominal_offset_minutes': None,
        'nominal_offset_months': None,
        'actual_offset_minutes': 0,
        'actual_offset_months': 0,

        'datafile': 'http://some.place.com/some/file',
        'start_date_utc': '2012-02-01T14:00:00Z',
        'end_date_utc': '2013-07-06T17:15:00Z',
        'gentity': 1360,
        'variable': 5683,
        'unit_of_measurement': 14,
        'time_zone': 1,
        'instrument': None,
        'time_step': 7,
        'interval_type': 18,
    },

    # Variables
    'Variable/5683/': {
        'id': 5683,
        'last_modified': '2012-01-24T09:46:50.717154Z',
        'descr': 'Temperature',
        'descr_alt': '',
    },

    # Units of measurement
    'UnitOfMeasurement/14/': {
        'id': 14,
        'last_modified': None,
        'descr': 'Celsius degrees',
        'descr_alt': 'Βαθμοί Κελσίου',
        'symbol': '°C',
        'variables': [],
    },

    # Time zones
    'TimeZone/1/': {
        'id': 1,
        'last_modified': None,
        'code': 'EET',
        'utc_offset': 120,
    },

    # Time steps
    'TimeStep/7/': {
        'id': 7,
        'last_modified': '2012-01-24T09:15:56.463866Z',
        'descr': 'Quarter',
        'descr_alt': 'Quarter',
        'length_minutes': 15,
        'length_months': 0
    },

    # Instruments
    'Instrument/19/': {
        'id': 19,
        'last_modified': '2013-07-01T13:08:12.558369Z',
        'manufacturer': '',
        'model': '',
        'start_date': '2001-04-10',
        'end_date': None,
        'name': '2nd air temperature & humidity',
        'remarks': 'Height from ground 2.35 m.',
        'name_alt': '2ος αισθ θερμοκρασίας & υγρασίας',
        'remarks_alt': 'Ύψος από το έδαφος 2.35 m.',
        'station': 1360,
        'type': 23,
    },

    # Instrument types
    'InstrumentType/23/': {
        'id': 23,
        'last_modified': '2011-06-29T06:49:17.207905Z',
        'descr': 'Thermograph',
        'descr_alt': 'Θερμογράφος',
    },

    # Gentity events
    'GentityEvent/586/': {
        'id': 586,
        'last_modified': '2012-06-01T07:30:18.460003Z',
        'date': '2012-04-28',
        'user': 'gkaravo',
        'report': 'Λόγω βλάβης (κάηκε το τροφοδοτικό) παρέμεινε εκτός',
        'report_alt': '',
        'gentity': 1360,
        'type': 4,
    },

    # Gentity event types
    'EventType/4/': {
        'id': 4,
        'last_modified': '2011-06-22T05:01:10.422552Z',
        'descr': 'Station Malfunction',
        'descr_alt': 'Βλάβη σταθμού',
    },

    # Gentity files
    'GentityFile/52/': {
        'id': 52,
        'last_modified': '2016-04-25T11:55:19.032822Z',
        'date': None,
        'content': 'http://openmeteo.org/media/gentityfile/dummy.jpg',
        'descr': 'Photo 1',
        'remarks': '',
        'descr_alt': 'Φωτογραφία 1',
        'remarks_alt': '',
        'gentity': 1360,
        'file_type': 1,
    },

    # File types
    'FileType/1/': {
        'id': 1,
        'last_modified': '2011-06-22T05:03:33.732472Z',
        'descr': 'jpg Picture',
        'descr_alt': 'Φωτογραφία',
        'mime_type': 'image/jpeg',
    },

    # Interval types
    'IntervalType/18/': {
        'id': 18,
        'descr': 'Sum',
        'descr_alt': 'Sum',
        'value': 'SUM',
    },
}

# Add list views in mock_responses.
# So far it only contains the detail views, in the form XXX/Y/. The list view
# XXX/ is the concatenation of all these.
for key in list(mock_responses.keys()):
    list_view = key[:key.index('/') + 1]
    if list_view not in mock_responses:
        mock_responses[list_view] = []
    mock_responses[list_view].append(mock_responses[key])


class MockServerRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path[5:]  # Strip the "/api/" from the path
        if path not in mock_responses:
            self.send_error(requests.codes.not_found)
            return
        self.send_response(requests.codes.ok)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(mock_responses[path]).encode('utf-8'))


_mock_server_port = None


def start_mock_server():
    global _mock_server_port

    # Return immediately if server is already running
    if _mock_server_port:
        return _mock_server_port

    # Get port
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, _mock_server_port = s.getsockname()
    s.close()

    # Start server on port
    mock_server = HTTPServer(('localhost', _mock_server_port),
                             MockServerRequestHandler)
    mock_server_thread = Thread(target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()
    return _mock_server_port
