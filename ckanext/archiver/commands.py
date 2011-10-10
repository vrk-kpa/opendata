from paste.script.command import Command
import tasks

import logging
logger = logging.getLogger()

class Archiver(Command):
    """
    Download and save copies of all package resources.

    If we already have a copy of a resource (tested by checking the hash value),
    then it is not saved again.
    The result of each download attempt is saved to a webstore database, so the
    information can be used later for QA analysis.

    Usage:

        paster archiver update [{package-id}]
           - Archive all resources or just those belonging to a specific package 
             if a package id is provided

        paster archiver clean        
            - Remove all archived resources
    """    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 2 
    pkg_names = []

    parser = Command.standard_parser(verbose=True)
    existing_dests = [o.dest for o in parser.option_list]
    if not 'limit' in existing_dests:
        parser.add_option('-l', '--limit',
            action='store',
            dest='limit',
            default=False,
            help="""Limit the process to a number of packages.
                    (Ignored if a package id is provided as an argument)"""
        )

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print Archiver.__doc__
            return

        cmd = self.args[0]

        if cmd == 'update':
            tasks.update.delay(unicode(self.args[1]) if len(self.args) > 1 else None)
        elif cmd == 'clean':
            tasks.clean.delay()
        else:
            logger.error('Command %s not recognized' % (cmd,))
