"""
Archive package resources
"""
import hashlib
import httplib
import os
import socket
import urllib
import urllib2
import urlparse
from db import archive_result
import logging

# Max content-length of archived files, larger files will be ignored
MAX_CONTENT_LENGTH = 500000

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

def archive_resource(archive_folder, db_file, resource, package_name, url_timeout=30):
    log = logging.getLogger('qa')
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
        archive_result(db_file, resource.id, "Invalid scheme")
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
            if e.code in http_error_codes:
                archive_result(db_file, resource.id, http_error_codes[e.code])
            else:
                archive_result(db_file, resource.id, "URL unobtainable")
        except httplib.InvalidURL, e:
            archive_result(db_file, resource.id, "Invalid URL")
        except urllib2.URLError, e:
            if isinstance(e.reason, socket.error):
                # Socket errors considered temporary as could stem from a temporary
                # network failure rather
                archive_result(db_file, resource.id, "URL temporarily unavailable")
            else:
                # Other URLErrors are generally permanent errors, eg unsupported
                # protocol
                archive_result(db_file, resource.id, "URL unobtainable")
        except Exception, e:
            archive_result(db_file, resource.id, "Invalid URL")
            log.error("%s", e)
        else:
            headers = response.info()
            ct = get_header(headers, 'content-type')
            cl = get_header(headers, 'content-length')
            if ct:
                if ct.lower() == 'text/csv' and cl < str(MAX_CONTENT_LENGTH):
                    length, hash = hash_and_save(archive_folder, resource, response, size=1024*16)
                    if length == 0:
                        # Assume the head request is behaving correctly and not 
                        # returning content. Make another request for the content
                        response = opener.open(urllib2.Request(url), timeout=url_timeout)
                        length, hash = hash_and_save(archive_folder, resource, response, size=1024*16)
                    if length:
                        dst_dir = os.path.join(archive_folder, package_name)
                        log.info('archive folder: %s' % dst_dir)
                        if not os.path.exists(dst_dir):
                            os.mkdir(dst_dir)
                        os.rename(
                            os.path.join(archive_folder, 'archive_%s'%os.getpid()),
                            os.path.join(dst_dir, hash+'.csv'),
                        )
                    archive_result(db_file, resource.id, 'ok', True, ct, cl)
                    log.info("Saved %s as %s" % (resource.url, hash))

def hash_and_save(archive_folder, resource, response, size=1024*16):
    log = logging.getLogger('qa')
    resource_hash = hashlib.sha1()
    length = 0
    fp = open(
        os.path.join(archive_folder, 'archive_%s'%os.getpid()),
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
        log.error('Could not generate hash. Error was %r', e)
        raise
    fp.close()
    resource.hash = resource_hash.hexdigest()
    return length, resource.hash
