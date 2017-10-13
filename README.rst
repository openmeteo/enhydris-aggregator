===================
Enhydris aggregator
===================

.. image:: https://travis-ci.org/openmeteo/enhydris-aggregator.svg?branch=master
    :alt: Build button
    :target: https://travis-ci.org/openmeteo/enhydris-aggregator

.. image:: https://codecov.io/github/openmeteo/enhydris-aggregator/coverage.svg?branch=master
    :alt: Coverage
    :target: https://codecov.io/gh/openmeteo/enhydris-aggregator

The Enhydris aggregator helps you create an Enhydris_ instance (the
**"target"** database) that only contains copies of data that exist in
other Enhydris instances (the **"source"** databases).

For example, the Hydroscope project has four databases (four Enhydris
instances) that belong to four organizations: kyy.hydroscope.gr,
emy.hydroscope.gr, deh.hydroscope.gr, and ypaat.hydroscope.gr.
There is also a database, main.hydroscope.gr, that serves as an
alternative entry point to all these; it contains the stations of all
four, but if you actually want the time series data, it redirects you to
the actual database. This database, main.hydroscope.gr, is powered by
Enhydris and the Enhydris aggregator.

The aggregator does two things:

1) It has a management command, ``./manage.py aggregate``, which should
   be run from a cron job, say once per day. It currently works in a
   relatively naïve way: it deletes all data from the target database,
   and copies it from scratch from the source databases through their
   web APIs.

2) It provides a modified template for the timeseries detail page,
   which, instead of a link to download the data, contains a link that
   points to the equivalent page of the originating database.

Installation and configuration
==============================

1. Clone the ``enhydris-aggregator`` repository and make sure that when
   Enhydris is executed it is in the Python path.
   
2. Make the following adjustments to the settings of Enhydris::

    INSTALLED_APPS = {
        ...
        'enhydris_aggregator',
    }

    ENHYDRIS_AGGREGATOR = {
        'SOURCE_DATABASES': [
            {
                'URL': 'http://some.enhydris.instance.com/',
                'STARTING_ID': 1000000,
            },
            {
                'URL': 'http://some.other.enhydris.instance.com/',
                'STARTING_ID': 2000000,
            },
        ]
    }

   Because an object with a certain id in one source database may be
   different from the object with the same id in another source
   database, these ids must be changed before entering these objects to
   the target database. The Enhydris aggregator achieves this by adding
   the ``STARTING_ID`` to the source id. It does this for all objects,
   including lookups, and it changes the foreign keys as well. You must
   select the ``STARTING_ID`` for all source databases so that there is
   no id conflict (e.g. in the above example make sure the first source
   database does not use an id larger 999999).

3. Execute ``./manage.py aggregate`` and also have cron execute it. You
   can also try ``./manage.py aggregate --help`` to see possible
   options.

Meta
====

© 2017-2018 National Technical University of Athens

The Enhydris aggregator is free software: you can redistribute it and/or
modify it under the terms of the GNU Affero General Public License, as
published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

The software is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
licenses for more details.

You should have received a copy of the license along with this
program.  If not, see http://www.gnu.org/licenses/.

Originally written by Antonis Christofides of the National Technical
University of Athens.

The Enhydris aggregator was funded by the `Ministry of Environment`_ of
Greece as part of the Hydroscope_ project.

.. _Enhydris: http://enhydris.readthedocs.io/
.. _ministry of environment: http://ypeka.gr/
.. _hydroscope: http://hydroscope.gr/
