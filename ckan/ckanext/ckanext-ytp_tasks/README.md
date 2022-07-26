ckanext-ytp-tasks
=================

Schduled task handling for CKAN and YTP tasks. Intented to be used with CKAN celery.

Requires Celery on CKAN.

Installation
------------

Installed as CKAN extension: ytp_tasks

[See how to install CKAN extensions.](http://docs.ckan.org/en/latest/extensions/tutorial.html#installing-the-extension)


Configuration
-------------

Copy ytp_celery.py.j2 to /etc/ckan/default/ytp_celery.py and rename variables.


Execution
---------

sudo -u $CELERY_USER /usr/lib/ckan/default/bin/celery beat --config=ytp_celery --workdir=/etc/ckan/default/ --pidfile=/tmp/celerybeat_pid --schedule=/tmp/celerybeat_schedule


Commands
--------

Execute commands via paster:
/usr/lib/ckan/default/bin/paster --plugin=ckanext-ytp-tasks -c /etc/ckan/default/$CONFIG_FILE <command-name> [arguments...]

::

    opendata-tasks add ID NAME FREQUENCY DATA - add task to scheduling

::

    opendata-tasks init-db - initialize scheduling database

::

    opendata-tasks execute-all - execute (queue) all tasks now

