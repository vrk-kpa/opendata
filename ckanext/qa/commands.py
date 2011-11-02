from datetime import datetime
import json
import requests
import urlparse
from pylons import config
from ckan.lib.cli import CkanCommand
from ckan.logic import get_action
from ckan import model
import tasks
import logging
logger = logging.getLogger()

class QACommand(CkanCommand):
    """Manage the ratings stored in the db

    Usage::

        paster qa [options] update [{package-id}]
           - Update all package scores or just one if a package id is provided

        paster qa clean        
            - Remove all package score information

    The commands should be run from the ckanext-qa directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster qa update --config=<path to CKAN config file>
    """    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2 
    min_args = 0

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print QACommand.__doc__
            return

        cmd = self.args[0]
        self._load_config()
        user = get_action('get_site_user')({'model': model, 'ignore_auth': True}, {})
        context = json.dumps({
            'site_url': config['ckan.site_url'],
            'apikey': user.get('apikey'),
            'username': user.get('name'),
        })
        api_url = urlparse.urljoin(config['ckan.site_url'], 'api/action')

        if cmd == 'update':
            # self.update(unicode(self.args[1]) if len(self.args) > 1 else None)
            pass
        elif cmd == 'clean':
            pass
        else:
            logger.error('Command %s not recognized' % (cmd,))

    def update(self, package_id = None):
        pass

