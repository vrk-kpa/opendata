import os
from pylons import config
from ckan.lib.cli import CkanCommand
import tasks

import logging
logger = logging.getLogger()


class Archive(CkanCommand):
    """
    Download and save copies of all package resources.

    If we already have a copy of a resource (tested by checking the hash value),
    then it is not saved again.
    The result of each download attempt is saved to a webstore database, so the
    information can be used later for QA analysis.

    Usage:

        paster archive update [{package-id}]
           - Archive all resources or just those belonging to a specific package 
             if a package id is provided

        paster archive clean        
            - Remove all archived resources

    The commands should be run from the ckanext-archiver directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster archive --config=../ckan/development.ini
    """    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 2 
    pkg_names = []

    existing_dests = [o.dest for o in CkanCommand.parser.option_list]
    if not 'limit' in existing_dests:
        CkanCommand.parser.add_option('-l', '--limit',
            action='store',
            dest='limit',
            default=False,
            help="""Limit the process to a number of packages.
                    (Ignored if a package id is provided as an argument)"""
        )
    if not 'force' in existing_dests:
        CkanCommand.parser.add_option('-o', '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Force the score update even if it already exists."
        )

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print Archive.__doc__
            return

        self._load_config()
        self.archive_folder = os.path.join(config['ckan.qa_archive'], 'downloads')
        cmd = self.args[0]

        if cmd == 'update':
            tasks.update.delay(unicode(self.args[1]) if len(self.args) > 1 else None)
        elif cmd == 'clean':
            tasks.clean.delay()
        else:
            logger.error('Command %s not recognized' % (cmd,))
