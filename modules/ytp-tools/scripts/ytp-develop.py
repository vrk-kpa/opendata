#! /usr/bin/env python

""" Simple script to replace packages on development machine """

import sys
import re
import types
import subprocess
import os
import shutil
import getpass


class YtpDevelopMain(object):
    source_path = "/src/modules"
    virtual_environment = "/usr/lib/ckan/default"
    _mappings = None

    def develop_ckanext(self, name):
        project_path = os.path.join(self.source_path, name)
        if not os.path.isdir(project_path):
            print "Failed to find project at %s" % project_path
            return 1

        subprocess.call([os.path.join(self.virtual_environment, "bin/pip"), "uninstall", "--yes", name])
        os.chdir(project_path)
        subprocess.call([os.path.join(self.virtual_environment, "bin/python"), "setup.py", "develop"])

        return 0

    def _replace_with_link(self, original_path, source_path):
        if os.path.islink(original_path):
            print u"Already linked"
            return 0

        shutil.rmtree(original_path)
        os.symlink(source_path, original_path)
        return 0

    def develop_assets(self, name):
        return self._replace_with_link("/var/www/resources", "/src/modules/ytp-assets-common/resources")

    def develop_drupal(self, name):
        return self._replace_with_link("/var/www/ytp/sites/all/themes/ytp_theme", "/src/modules/ytp-theme-drupal")

    def _get_projects(self):
        for project_name in os.listdir(self.source_path):
            if os.path.isdir(os.path.join(self.source_path, project_name)) and self._get_mapping(project_name):
                yield project_name

    def list_projects(self, name=None):
        for project_name in self._get_projects():
            print project_name
        return 0

    def paster_serve(self, name=None):
        subprocess.call(["/usr/sbin/ufw", "allow", "5000"])
        process_arguments = ["/usr/bin/sudo", "-u", "www-data", os.path.join(self.virtual_environment, "bin/paster"), "serve",
                             "/etc/ckan/default/production.ini", "--reload"]
        process = subprocess.Popen(process_arguments)
        try:
            process.wait()  # exit via ctrl-c
        finally:  # ensure that process is terminated
            try:
                process.terminate()
            except:
                pass
            print "killed"
            return 0

    def _execute_all(self, name=None):
        if name != '--all':
            return
        methods = {}
        for project_name in self._get_projects():
            methods[project_name] = self._get_mapping(project_name)
        self._execute_methods(methods)

    def _get_mappings(self):
        if self._mappings is None:
            self._mappings = {re.compile(u'^ckanext-.+'): self.develop_ckanext, u'ytp-assets-common': self.develop_assets,
                              u'ytp-theme-drupal': self.develop_drupal,
                              u'--list': self.list_projects, u'--serve': self.paster_serve,
                              u'--all': self._execute_all}
        return self._mappings

    def _get_mapping(self, project_name):
        for matcher, method in self._get_mappings().iteritems():
            if type(matcher) in types.StringTypes:
                if matcher == project_name:
                    return method
            elif getattr(matcher, 'match', False):
                if matcher.match(project_name):
                    return method
        return None

    def _execute_methods(self, methods):
        end_return_code = 0
        for project_name, method in methods.iteritems():
            return_code = method(project_name)
            if return_code != 0:
                end_return_code = return_code

        return end_return_code

    def main(self, arguments):
        if getpass.getuser() != 'root':
            print "You must run this script as root"
            return 4

        if len(arguments) < 2 or "--help" in arguments or "-h" in arguments:
            print u"Usage: %s <project-name>...\n       %s --list\n       %s --serve\n       %s --all\n" \
                % (arguments[0], arguments[0], arguments[0], arguments[0])
            print u"Available projects:\n"
            self.list_projects()
            return 2

        methods = {}
        for project_name in arguments[1:]:
            method = self._get_mapping(project_name)
            if not method:
                print u"Failed to find handler for project name '%s'" % project_name
                return 3
            methods[project_name] = method

        assert len(methods) > 0

        return self._execute_methods(methods)


if __name__ == '__main__':
    exit_code = YtpDevelopMain().main(sys.argv)
    if exit_code != 0:
        print u"\nProcess failed. See output for details.\n"

    exit(exit_code)
