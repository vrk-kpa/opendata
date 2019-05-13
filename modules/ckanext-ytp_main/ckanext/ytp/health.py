import ckan.lib.base as base
import pylons.config as config
import urllib2
import logging
log = logging.getLogger(__name__)

SITE_URL_FAILURE_LOGMESSAGE = "Site URL '%s' failed to respond during health check."
FAILURE_MESSAGE = "An error has occurred, check the server log for details"
SUCCESS_MESSAGE = "OK"


def check_url(url):
    try:
        response = urllib2.urlopen(url, timeout=30)
        return response.getcode() == 200
    except urllib2.URLError:
        return False


class HealthController(base.BaseController):
    check_site_urls = ['/', '/data/fi/dataset']

    def check(self):
        result = True
        site_url = config.get('ckan.site_url')

        for url in self.check_site_urls:
            if not check_url("%s/%s" % (site_url, url)):
                log.warn(SITE_URL_FAILURE_LOGMESSAGE % url)
                result = False

        if result:
            base.abort(200, SUCCESS_MESSAGE)
        else:
            base.abort(503, FAILURE_MESSAGE)
