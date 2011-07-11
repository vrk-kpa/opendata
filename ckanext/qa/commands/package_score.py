"""
Warning: This command is deprecated.

Instead, please use:

    paster archive 
    paster qa
"""
from ckan.lib.cli import CkanCommand
from archive import Archive
from qa import QA

class PackageScore(CkanCommand):
    """
    Warning: This command is deprecated. 
    
    Instead, please use:

        paster archive 
        paster qa
    """    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0
    max_args = 2 

    existing_dests = [o.dest for o in CkanCommand.parser.option_list]
    if not 'start' in existing_dests:
        CkanCommand.parser.add_option('-s', '--start',
            action='store',
            dest='start',
            default=False,
            help="""Start the process from the specified package.
                    (Ignored if a package id is provided as an argument)"""
        )
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
        print PackageScore.__doc__

        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            return
        else:
            archive = Archive('archive')
            archive.options = self.options
            archive.args = self.args
            archive.command()
            qa = QA('qa')
            qa.options = self.options
            qa.args = self.args
            qa.command()
