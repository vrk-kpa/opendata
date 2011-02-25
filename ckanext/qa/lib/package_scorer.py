"""
Score packages on timbl's five stars of openness:

    0* - The information is not obtainable (links not given or 404)
    1* - The information is publicly obtainable
    2* - The information is machine-readable format
    3* - The information is in an open and standardised format
    4* - The information is ontologically represented
    5* - The information is fully Linked Open Data as appropriate

"""
import httplib
import re
import socket
import urllib2
import hashlib
from datetime import datetime, timedelta
from logging import getLogger
from urllib2 import URLError, HTTPError, FileHandler
from ckan.model.domain_object import Enum

log = getLogger(__name__)

__all__ = ['PKGEXTRA', 'package_score', 'update_package_score']

# PackageExtra keys used by the scorer
PKGEXTRA = Enum(
    u'openness_score',
    u'openness_score_reason',
    u'openness_score_last_checked',
    u'openness_score_failure_count',
    u'openness_score_override',
)

# How many times to retry a package with temporary fetch erros before giving up
# and scoring it at zero
max_retries = 5

# Minimum interval between retries for a package that previously failed
retry_interval = timedelta(hours=6)

# How long to wait for a timeout when fetching a resource
url_timeout = 30

# how many bytes to read at a time for calculating the hash of the content
# of a resource 102400 = 1KB
chunk_size = 102400

class BadURLError(Exception):
    """
    URL is either not well formed or not permitted
    """

class URLFetchError(Exception):
    """
    Can't fetch a URL
    """

class TemporaryFetchError(URLFetchError):
    """
    Can't fetch resource, might succeed if retried later
    """

class PermanentFetchError(URLFetchError):
    """
    Can't fetch resource, no point retrying
    """

class UrlDetails(object):
	"""
	Holds the details about a specific resource URL.
	"""
	def __init__(self):
		self.score = None
		self.reason = None
		self.content_type = None
		self.content_length = None
		self.hash = None
		self.bytes = 0
		
# List of status codes together with the error that should be raised.
# If a status code is returned not in this list a PermanentFetchError will be
# raised
http_error_codes = {
    httplib.MULTIPLE_CHOICES: NotImplementedError("300 Multiple Choices not implemented"),
    httplib.USE_PROXY: NotImplementedError("305 Use Proxy not implemented"),
    httplib.INTERNAL_SERVER_ERROR: TemporaryFetchError,
    httplib.BAD_GATEWAY: TemporaryFetchError,
    httplib.SERVICE_UNAVAILABLE: TemporaryFetchError,
    httplib.GATEWAY_TIMEOUT: TemporaryFetchError,
}

# Content types mapped to score and reason
mime_types = [
    (1, 'obtainable via web page', [
        'text/html',
    ]),
    (2, 'machine readable format', [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.ms-excel.sheet.binary.macroenabled.12',
        'application/vnd.ms-excel.sheet.macroenabled.12',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ]),
    (3, 'open and standardized format', [
        'application/json',
        'text/xml',
    ]),
    (4, 'ontologically represented', [
        'application/rdf+xml',
        'application/xml',
    ]),

]
# Transform to a dict indexed by mime type
mime_types = dict(
    (mt, (score, reason))
    for score, reason, types in mime_types
    for mt in types
)

def check_url(url):
    """
    Return ``url`` if it is allowed, else raise an exception.
    """
    allowed_schemes = ['http', 'https', 'ftp']
    if any(url.startswith(scheme + '://') for scheme in allowed_schemes):
        return url

    raise BadURLError("URL %r is not allowed" % (url,))

def _get_opener():
    """
    Return a urllib2 opener
    """
    redirect_handler = urllib2.HTTPRedirectHandler()
    opener = urllib2.build_opener(redirect_handler)
    # Remove the file handler to make sure people can't supply 'file:///...' in
    # package resources.
    opener.handlers = [h for h in opener.handlers if not isinstance(h, FileHandler)]
    return opener

class GETRequest(urllib2.Request):
    """
    Create a GET request for a URL
    """

class HEADRequest(urllib2.Request):
    """
    Create a HEAD request for a URL
    """
    def get_method(self):
        return "HEAD"


def _parse_iso_time(s):
    """
    Parse a subset of iso 8601 formatted date strings into datetime objects.
    Doesn't support time zones, but is enough for parsing values produced by
    datetime.isoformat().
    """
    return datetime(*(int(n) for n in re.split('[^\d]', s)[:-1]))


def next_check_time(package):
    """
    Return a datetime representing the time after which the given package
    may be rescored, based on the number of previous failures.

    The next check time is defined as:

        last_check_time + retry_interval

    if no failure previously occurred, otherwise:

        last_check_time + 2 ** (n - 1)

    Where n is the number of consecutive failures, based on the
    package.extras['openness_score_failure_count'].
    """
    try:
        last_check_time = _parse_iso_time(package.extras[PKGEXTRA.openness_score_last_checked])
        failures = int(package.extras[PKGEXTRA.openness_score_failure_count])
    except KeyError:
        return datetime.min

    if failures < 1:
        return last_check_time + retry_interval

    return last_check_time + retry_interval * 2 ** (failures - 1)


def response_for_url(url, method=HEADRequest):
    """
    Fetch the given URL, returning the urllib2 response object or raising a
    URLFetchError
    """
    
    url = check_url(url)
    http_request = method(url)
    try:
        return _get_opener().open(http_request, timeout=url_timeout)
    except HTTPError, e:
        if e.code in http_error_codes:
            raise http_error_codes[e.code](e.code, e.message)
        raise PermanentFetchError(e)

    except URLError, e:
        if isinstance(e.reason, socket.error):
            # Socket errors considered temporary as could stem from a temporary
            # network failure rather
            raise TemporaryFetchError(e)
        else:
            # Other URLErrors are generally permanent errors, eg unsupported
            # protocol
            raise PermanentFetchError(e)

    except ValueError:
        raise BadURLError(e)

def resource_details(url):
    """
    Return UrlDetails object for the given URL, where score is a number
    from 0-5 and breakdown is a textual explanation of the scoring reasons.

    If the package is unfetchable due to a temporary error, a score of ``None``
    is returned.
    """

    url_details = UrlDetails()
    
    try:
        response = response_for_url(url)
        headers = response.info()
        try:
            url_details.content_type = headers['Content-Type']
            # 'text/xml; charset=UTF-8' => 'text/xml'
            if ';' in url_details.content_type:
                url_details.content_type = url_details.content_type.split(';')[0]
        except KeyError:
            url_details.score = 0
            url_details.reason = "no content type header"

        url_details.content_length = headers.get('Content-Length', None)

        resource_hash = hashlib.sha1()
        for chunk in iter(lambda: response.read(chunk_size), ''):
            url_details.bytes += len(chunk)
            resource_hash.update(chunk)
        url_details.hash = resource_hash.hexdigest()

        url_details.score, url_details.reason = mime_types.get(url_details.content_type, (1, "unrecognized content type"))
    except TemporaryFetchError:
        url_details.score = None
        url_details.reason = "URL temporarily unavailable"
    except PermanentFetchError:
        url_details.score = 0
        url_details.reason = "URL unobtainable"

    return url_details


def mean(values):
    """
    Return the arithmetic mean of values.

    :param values: list of numbers to average
    """
    if len(values) == 0:
        return 0
    return sum(values, 0.0) / len(values)

def resource_score(resource):
    """
    Score an individual resource for a packge. Store that information
    int he extras JsonDictType on the resource. The score is a number in the
    range 0-5. These scores are aggragted to create an overall package score.
    """
    
    url_details = resource_details(resource.url)
    if url_details.score is None:
        url_details.score = resource.extras.get(PKGEXTRA.openness_score)
        url_details.failure_count = resource.extras.get(PKGEXTRA.openness_score_failure_count, 0) + 1
        if url_details.failure_count > max_retries:
            url_details.score = 0
            url_details.reason = u'%s; too many failures' % url_details.reason
    else:
        url_details.failure_count = 0
    
    resource.hash = url_details.hash
    resource.extras[PKGEXTRA.openness_score] = url_details.score
    resource.extras[PKGEXTRA.openness_score_reason] = url_details.reason
    resource.extras[PKGEXTRA.openness_score_failure_count] = url_details.failure_count
    resource.extras[PKGEXTRA.openness_score_last_checked] = datetime.now().isoformat()
    resource.extras[PKGEXTRA.openness_score_override] = None
    
    return url_details.score, url_details.reason
    
def package_score(package, aggregate_function=mean):
    """
    Attempt to load all resources listed and return a tuple of ``(<score>,
    <reason>)``, where ``score`` is a number in the range 0-5, based on the
    aggregate score of the package resources, and reasons is a human readable
    breakdown of the reasons.
    """

    scores = [resource_score(resource) for resource in package.resources]
    if not scores:
        return None, None
    scores, reasons = zip(*scores)
    scores = [s for s in scores if s is not None]
    score = aggregate_function(scores) if scores else None
    reason = '; '.join(reasons)
    return score, reason

def update_package_score(package, force=False):
    """
    Update the score for ``package`` and write scoring information to the
    database.

    If the package cannot be scored because of a temporary error, the previous
    score is retained and ``package.extras['openness_score_failure_count']``
    value is incremented, up to ``max_retries``, after which the package will
    be scored at zero.

    Packages won't be re-scored until after ``next_check_time(package)``. If
    ``force`` is True, this condition is skipped and the package is updated anyway.
    """
    # Don't update scores that have been manually overridden
    if package.extras.get(PKGEXTRA.openness_score_override):
        return

    if not force and datetime.now() < next_check_time(package):
        return
    
    score, reason = package_score(package)
    if score is None:
        score = package.extras.get(PKGEXTRA.openness_score)
        failure_count = package.extras.get(PKGEXTRA.openness_score_failure_count, 0) + 1
        if failure_count > max_retries:
            score = 0
            reason = u'%s; too many failures' % reason
    else:
        failure_count = 0

    package.extras[PKGEXTRA.openness_score] = score
    package.extras[PKGEXTRA.openness_score_reason] = reason
    package.extras[PKGEXTRA.openness_score_failure_count] = failure_count
    package.extras[PKGEXTRA.openness_score_last_checked] = datetime.now().isoformat()
    package.extras[PKGEXTRA.openness_score_override] = None