"""
Warning: This command is deprecated.

Instead, please use:

    paster archive 
    paster qa
"""
import sys
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

    def command(self):
        print PackageScore.__doc__

        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            return
        else:
            archive = Archive('archive')
            archive.options = self.options
            archive.args = self.args
            archive.command()
