#! /usr/bin/env python

""" Simple script to replace packages on development machine. Intended to be used inside Vagrant machine.
    See doc/local-development.md for instructions.
"""

import sys
import re
import types
import subprocess
import os
import shutil
import getpass


class YtpDevelopMain(object):
    """ Dynamic handler class that replaces sources from static location. Hides complexity of package installation. """

    source_path = "/vagrant/modules"
    virtual_environment = "/usr/lib/ckan/default"
    _mappings = None

    def develop_ckanext(self, name):
        """ Develop ckan extensions handler. ckanext-* """
        project_path = os.path.join(self.source_path, name)
        if not os.path.isdir(project_path):
            print "Failed to find project at %s" % project_path
            return 1

        subprocess.call([os.path.join(self.virtual_environment, "bin/pip"), "uninstall", "--yes", name])
        os.chdir(project_path)
        subprocess.call([os.path.join(self.virtual_environment, "bin/python"), "setup.py", "develop"])

        return 0

    def _replace_with_link(self, original_path, source_path, ignore_errors=False):
        """ Replace path with link """
        if os.path.islink(original_path):
            print u"Already linked"
            return 0

        shutil.rmtree(original_path, ignore_errors=ignore_errors)
        os.symlink(source_path, original_path)
        return 0

    def develop_assets(self, name):
        """ Develop ytp-assets-common handler. """
        return self._replace_with_link("/var/www/resources", "/vagrant/modules/ytp-assets-common/resources")

    def develop_drupal_theme(self, name):
        """ Develop avoindata-drupal-theme handler. """
        self._replace_with_link("/var/www/opendata/web/themes/avoindata", "/vagrant/modules/avoindata-drupal-theme")
        if not os.path.exists("/var/www/opendata/web/themes/avoindata/vendor"):
            subprocess.call(["mkdir", "/var/www/opendata/web/themes/avoindata/vendor"])
            subprocess.call(["cp", "-r", "/var/www/resources/vendor", "/var/www/opendata/web/themes/avoindata/"])
        return 0

    def develop_header(self, name):
        """ Develop avoindata-header handler. """
        return self._replace_with_link("/var/www/opendata/web/modules/avoindata-header", "/vagrant/modules/avoindata-drupal-header")

    def develop_frontpagesearch(self, name):
        """ Develop avoindata-frontpagesearch handler. """
        return self._replace_with_link("/var/www/opendata/web/modules/avoindata-frontpagesearch", "/vagrant/modules/avoindata-drupal-frontpagesearch")

    # def develop_drupal_user(self, name):
    #     """ Develop ytp-drupal-user handler. """
    #     return self._replace_with_link("/var/www/ytp/web/modules/ytp_user", "/vagrant/modules/ytp-drupal-user")

    # def develop_drupal_features(self, name):
    #     """ Develop ytp-drupal-features handler. """
    #     return self._replace_with_link("/var/www/ytp/web/modules/ytp_features", "/vagrant/modules/ytp-drupal-features")

    # def develop_drupal_tutorial(self, name):
    #     """ Develop ytp-drupal-tutorial handler. """
    #     return self._replace_with_link("/var/www/ytp/web/modules/ytp_tutorial", "/vagrant/modules/ytp-drupal-tutorial")

    # def develop_drupal_footer(self, name):
    #     """ Develop ytp-drupal-footer handler. """
    #     return self._replace_with_link("/var/www/ytp/web/modules/ytp_footer", "/vagrant/modules/ytp-drupal-footer")

    # def develop_drupal_frontpage(self, name):
    #     """ Develop ytp-drupal-frontpage handler. """
    #     return self._replace_with_link("/var/www/ytp/web/modules/ytp_frontpage", "/vagrant/modules/ytp-drupal-frontpage")

    def _get_projects(self):
        for project_name in os.listdir(self.source_path):
            if os.path.isdir(os.path.join(self.source_path, project_name)) and self._get_mapping(project_name):
                yield project_name

    def list_projects(self, name=None):
        """ List and print projects handler """
        for project_name in self._get_projects():
            print project_name
        return 0

    def paster_serve(self, name=None):
        """ Serve delopment server handler """
        subprocess.call(["/usr/sbin/ufw", "allow", "5000"])
        process_arguments = ["/usr/bin/sudo", "-u", "www-data", os.path.join(self.virtual_environment, "bin/paster"), "serve",
                             "/etc/ckan/default/production.ini", "--reload", "--monitor-restart"]
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
            self._mappings = {re.compile(u'^ckanext-.+'): self.develop_ckanext,
                              u'ytp-assets-common': self.develop_assets,
                              u'avoindata-drupal-theme': self.develop_drupal_theme,
                              u'avoindata-header': self.develop_header,
                              u'avoindata-frontpagesearch': self.develop_frontpagesearch,
                              # u'ytp-drupal-user': self.develop_drupal_user,
                              # u'ytp-drupal-features': self.develop_drupal_features,
                              # u'ytp-drupal-tutorial': self.develop_drupal_tutorial,
                              # u'ytp-drupal-footer': self.develop_drupal_footer,
                              # u'ytp-drupal-frontpage': self.develop_drupal_frontpage,
                              u'--list': self.list_projects,
                              u'--serve': self.paster_serve,
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
