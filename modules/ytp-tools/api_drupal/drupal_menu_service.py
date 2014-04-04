#!/usr/bin/env python
#

"""Pull menus from Drupal via Service API, see https://drupal.org/project/services

https://drupal.org/node/1699354
"""

import logging
import requests
import json

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


if __name__ == '__main__':

    request_url = 'http://10.10.10.10/api/ytp_menu_service/menu/main-menu.json'
    response = requests.get(request_url)

    log.debug(json.dumps(response.json(), indent=2, sort_keys=True))
