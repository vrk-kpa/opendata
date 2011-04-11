"""\
Score packages on Sir Tim Bernes-Lee's five stars of openness based on mime-type
"""
import datetime
import hashlib
import httplib
import logging
import os
import socket
import urllib
import urllib2
import urlparse
from pylons import config

log = logging.getLogger(__name__)

openness_score_reason = {
    '-1': 'unscorable content type',
    '0': 'not obtainable',
    '1': 'obtainable via web page',
    '2': 'machine readable format',
    '3': 'open and standardized format',
    '4': 'ontologically represented',
    '5': 'fully Linked Open Data as appropriate',
}

mime_types_scores = {
    '1': [
        'text/html',
        'text/plain',
    ],
    '2': [
        'application/vnd.ms-excel',
        'application/vnd.ms-excel.sheet.binary.macroenabled.12',
        'application/vnd.ms-excel.sheet.macroenabled.12',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ],
    '3': [
        'text/csv',
        'application/json',
        'text/xml',
    ],
    '4': [
        'application/rdf+xml',
        'application/xml',
    ],
    '5': [],
}

score_by_mime_type = {}
for score, mime_types in mime_types_scores.items():
    for mime_type in mime_types:
        score_by_mime_type[mime_type] = score

def get_header(headers, name):
    name = name.lower()
    for k in headers:
        if k.lower() == name:
            return headers[k]

class HEADRequest(urllib2.Request):
    """
    Create a HEAD request for a URL
    """
    def get_method(self):
        return "HEAD"

def package_score(package, force=False, url_timeout=30):
    openness_score = '0'
    for resource in package.resources:
        # Find out if it has unicode characters, and if it does, quote them 
        # so we are left with an ascii string
        url = resource.url
        try:
            url = url.decode('ascii')
        except:
            parts = list(urlparse.urlparse(url))
            parts[2] = urllib.quote(parts[2].encode('utf-8'))
            url = urlparse.urlunparse(parts)
        url = str(url)
        # Check we aren't using any schemes we shouldn't be
        allowed_schemes = ['http', 'https', 'ftp']
        if not any(url.startswith(scheme + '://') for scheme in allowed_schemes):
            resource.extras[u'openness_score'] = 0
            resource.extras[u'openness_score_reason'] = "Invalid scheme"
        else:
            # Send a head request
            http_request = HEADRequest(url)
            try:
                redirect_handler = urllib2.HTTPRedirectHandler()
                opener = urllib2.build_opener(redirect_handler)
                # Remove the file handler to make sure people can't supply 'file:///...' in
                # package resources.
                opener.handlers = [h for h in opener.handlers if not isinstance(h, urllib2.FileHandler)]
                response = opener.open(http_request, timeout=url_timeout)
            except urllib2.HTTPError, e:
                # List of status codes together with the error that should be raised.
                # If a status code is returned not in this list a PermanentFetchError will be
                # raised
                http_error_codes = {
                    httplib.MULTIPLE_CHOICES: "300 Multiple Choices not implemented",
                    httplib.USE_PROXY: "305 Use Proxy not implemented",
                    httplib.INTERNAL_SERVER_ERROR: "Internal server error on the remote server",
                    httplib.BAD_GATEWAY: "Bad gateway",
                    httplib.SERVICE_UNAVAILABLE: "Service unavailable",
                    httplib.GATEWAY_TIMEOUT: "Gateway timeout",
                }
                resource.extras[u'openness_score'] = 0
                if e.code in http_error_codes:
                    resource.extras[u'openness_score_reason'] = http_error_codes[e.code]
                else:
                    resource.extras[u'openness_score_reason'] = "URL unobtainable"
            except httplib.InvalidURL, e:
                resource.extras[u'openness_score'] = 0
                resource.extras[u'openness_score_reason'] = "Invalid URL"
            except urllib2.URLError, e:
                if isinstance(e.reason, socket.error):
                    # Socket errors considered temporary as could stem from a temporary
                    # network failure rather
                    resource.extras[u'openness_score'] = 0
                    resource.extras[u'openness_score_reason'] = "URL temporarily unavailable"
                else:
                    # Other URLErrors are generally permanent errors, eg unsupported
                    # protocol
                    resource.extras[u'openness_score'] = 0
                    resource.extras[u'openness_score_reason'] = "URL unobtainable"
            except Exception, e:
                resource.extras[u'openness_score'] = 0
                resource.extras[u'openness_score_reason'] = "Invalid URL"
                log.error("%s", e)
            else:
                headers = response.info()
                resource.extras[u'content_length'] = get_header(headers, 'content-length')
                ct = get_header(headers, 'content-type')
                if ct:
                    resource.extras[u'content_type'] = ct.split(';')[0]
                    resource.extras[u'openness_score'] = score_by_mime_type.get(resource.extras[u'content_type'], '-1')
                else:
                    resource.extras[u'content_type'] = None
                    resource.extras[u'openness_score'] = '0'
                resource.extras[u'openness_score_reason'] = openness_score_reason[resource.extras[u'openness_score']]
                if resource.extras[u'content_type'] != None:
                    if resource.format and resource.format.lower() not in [
                        resource.extras[u'content_type'].lower().split('/')[-1],
                        resource.extras[u'content_type'].lower().split('/'),
                    ]:
                        resource.extras[u'openness_score_reason'] = 'The format entered for the resource doesn\'t match the description from the web server'
                        resource.extras[u'openness_score'] = '0'
                    else:
                        if resource.extras[u'content_type'].lower() == 'text/csv' and resource.extras[u'content_length'] < '500000':
                            length, hash = hash_and_save(resource, response, size=1024*16)
                            if length == 0:
                                # Assume the head request is behaving correctly and not returning content. Make another request for the content
                                response = opener.open(urllib2.Request(url), timeout=url_timeout)
                                length, hash = hash_and_save(resource, response, size=1024*16)
                            if length:
                                dst_dir = os.path.join(config['ckan.qa_downloads'], package.name)
                                print dst_dir
                                if not os.path.exists(dst_dir):
                                    os.mkdir(dst_dir)
                                #import pdb; pdb.set_trace()
                                os.rename(
                                    os.path.join(config['ckan.qa_downloads'], 'download_%s'%os.getpid()),
                                    os.path.join(dst_dir, hash+'.csv'),
                                )
                              
                            print "Saved %s as %s" % (resource.url, resource.hash)
        # Set the failure count
        if resource.extras[u'openness_score'] == '0':
            # At this point save the pacakge and resource, and maybe try it again
            resource.extras['openness_score_failure_count'] = resource.extras.get('openness_score_failure_count', 0) + 1
        else:
            resource.extras['openness_score_failure_count'] = 0
        # String comparison
        if resource.extras[u'openness_score'] > openness_score:
            openness_score = resource.extras[u'openness_score']
    package.extras[u'openness_score_last_checked'] = datetime.datetime.now().isoformat()
    package.extras[u'openness_score'] = openness_score

def hash_and_save(resource, response, size=1024*16):
    resource_hash = hashlib.sha1()
    length = 0
    fp = open(
        os.path.join(config['ckan.qa_downloads'], 'download_%s'%os.getpid()),
        'wb',
    )
    try:
        chunk = response.read(size)
        while chunk: # EOF condition
            fp.write(chunk)
            length += len(chunk)
            resource_hash.update(chunk)
            chunk = response.read(size)
    except Exception, e:
        log.error('Could not generate hash %r. Error was %r', src, e)
        raise
    fp.close()
    resource.hash = resource_hash.hexdigest()
    return length, resource.hash
