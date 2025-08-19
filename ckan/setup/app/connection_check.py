"""
Copyright (c) 2016 Keitaro AB
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    https://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

import psycopg2
from sqlalchemy.engine.url import make_url

ckan_ini = os.environ.get('CKAN_INI', '/srv/app/production.ini')

RETRY = 5


def check_db_connection(retry: Optional[int] = None) -> None:

    print('[connection_check] Start check_db_connection...')

    if retry is None:
        retry = RETRY
    elif retry == 0:
        print('[connection_check] Giving up after 5 tries...')
        sys.exit(1)

    conn_str = os.environ.get('CKAN_SQLALCHEMY_URL', '')
    try:
        db_user = make_url(conn_str).username
        db_passwd = make_url(conn_str).password
        db_host = make_url(conn_str).host
        db_name = make_url(conn_str).database
        connection = psycopg2.connect(user=db_user,
                               host=db_host,
                               password=db_passwd,
                               database=db_name)

    except psycopg2.Error as e:
        print(str(e))
        print('[connection_check] Unable to connect to the database...try again in a while.')
        import time
        time.sleep(10)
        check_db_connection(retry=retry - 1)
    else:
        connection.close()


def check_solr_connection(retry: Optional[int] = None) -> None:

    print('[connection_check] Start check_solr_connection...')

    if retry is None:
        retry = RETRY
    elif retry == 0:
        print('[connection_check] Giving up after 5 tries...')
        sys.exit(1)

    url = os.environ.get('CKAN_SOLR_URL', '')
    username = os.environ.get('CKAN_SOLR_USER', '')
    password = os.environ.get('CKAN_SOLR_PASSWORD', '')
    search_url = f'{url}/schema/name?wt=json'

    try:
        if not username:
            connection = urllib.request.urlopen(search_url)
        else:
            request = urllib.request.Request(search_url)
            base64string = base64.b64encode(bytes(f'{username}:{password}', 'ascii'))
            request.add_header("Authorization", f"Basic {base64string.decode('utf-8')}")
            connection = urllib.request.urlopen(request)
    except urllib.error.URLError:
        print('[connection_check] Unable to connect to solr...try again in a while.')
        import time
        time.sleep(10)
        check_solr_connection(retry=retry - 1)
    else:
        conn_info = connection.read()
        schema_name = json.loads(conn_info)
        if 'ckan' in schema_name['name']:
            print('[connection_check] Succesfully connected to solr and CKAN schema loaded')
        else:
            print('[connection_check] Succesfully connected to solr, but CKAN schema not found')
            sys.exit(1)


if __name__ == '__main__':

    maintenance = os.environ.get('MAINTENANCE_MODE', '').lower() == 'true'

    if maintenance:
        print('[connection_check] Maintenance mode, skipping setup...')
    else:
        check_db_connection()
        check_solr_connection()
