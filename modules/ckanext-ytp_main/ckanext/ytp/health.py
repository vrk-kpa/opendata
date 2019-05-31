from ckan.common import config
import ckan.lib.base as base
import re
import urllib2
import logging
log = logging.getLogger(__name__)

SITE_URL_FAILURE_LOGMESSAGE = "Site URL '%s' failed to respond during health check."
FAILURE_MESSAGE = "An error has occurred, check the server log for details"
SUCCESS_MESSAGE = "OK"


def check_url(host, url):
    try:
        req = urllib2.Request('http://localhost%s' % url)
        req.add_header('Host', host)
        response = urllib2.urlopen(req, timeout=30)
        return response.getcode() == 200
    except urllib2.URLError:
        return False


class HealthController(base.BaseController):
    check_site_urls = ['/fi', '/data/fi/dataset']

    def check(self):
        result = True
        site_url = config.get('ckan.site_url')
        host = re.sub(r'https?:\/\/', '', site_url)

        for url in self.check_site_urls:
            if not check_url(host, url):
                log.warn(SITE_URL_FAILURE_LOGMESSAGE % url)
                result = False

        if result:
            base.abort(200, SUCCESS_MESSAGE)
        else:
            base.abort(503, FAILURE_MESSAGE)
