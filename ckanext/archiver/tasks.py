import os
import hashlib
import httplib
import socket
import urllib
import urllib2
import urlparse
from celery.task import task
from ckan.logic.action import get
from ckan import model

try:
    from ckanext.archiver import settings
except ImportError:
    from ckanext.archiver import default_settings as settings

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


@task(name = "archiver.clean")
def clean():
    """
    Remove all archived resources.
    """
    logger = clean.get_logger()
    logger.error("clean task not implemented yet")


@task(name = "archiver.update")
def update(package_id = None, limit = None):
    logger = update.get_logger()

    # load pylons
    from paste.deploy import appconfig
    from ckan.config.environment import load_environment
    conf = appconfig('config:%s' % settings.CKAN_CONFIG)
    load_environment(conf.global_conf, conf.local_conf)

    # check that archive directory exists
    if not os.path.exists(settings.ARCHIVE_DIR):
        logger.info("Creating archive directory: %s" % settings.ARCHIVE_DIR)
        os.mkdir(settings.ARCHIVE_DIR)

    context = {'model': model, 'session': model.Session,  'user': settings.ARCHIVE_USER}
    data = {}

    if package_id:
        data['id'] = package_id
        package = get.package_show(context, data)
        if package:
            packages = [package]
        else:
            logger.error("Error: Package not found: %s" % package_id)
    else:
        if limit:
            data['limit'] = limit
            logger.info("Limiting results to %d packages" % limit)
        packages = get.current_package_list_with_resources(context, data)

    logger.info("Total packages to update: %d" % len(packages))
    if not packages:
        return

    for package in packages:
        resources = package.get('resources', [])
        if not len(resources):
            logger.info("Package %s has no resources - skipping" % package['name'])
        else:
            logger.info("Checking package: %s (%d resource(s))" % 
                (package['name'], len(resources))
            )
            for resource in resources:
                logger.info("Attempting to archive resource: %s" % resource['url'])
                archive_resource.delay(resource, package['name'])


@task(name = "archiver.archive_resource")
def archive_resource(resource, package_name, url_timeout=30):
    logger = archive_resource.get_logger()

    # Find out if it has unicode characters, and if it does, quote them 
    # so we are left with an ascii string
    url = resource['url']
    try:
        url = url.decode('ascii')
    except:
        parts = list(urlparse.urlparse(url))
        parts[2] = urllib.quote(parts[2].encode('utf-8'))
        url = urlparse.urlunparse(parts)
    url = str(url)
    # parse url
    parsed_url = urlparse.urlparse(url)
    # Check we aren't using any schemes we shouldn't be
    allowed_schemes = ['http', 'https', 'ftp']
    if not parsed_url.scheme in allowed_schemes:
        update_task_status.delay(resource['id'], "Invalid url scheme")
    # check that query string is valid
    # see: http://trac.ckan.org/ticket/318
    # TODO: check urls with a better validator? 
    #       eg: ll.url (http://www.livinglogic.de/Python/url/Howto.html)?
    elif any(['/' in parsed_url.query, ':' in parsed_url.query]):
        update_task_status.delay(resource['id'], "Invalid URL")
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
                update_task_status.delay(resource['id'], http_error_codes[e.code])
            else:
                update_task_status.delay(resource['id'], "URL unobtainable")
        except httplib.InvalidURL, e:
            update_task_status.delay(resource['id'], "Invalid URL")
        except urllib2.URLError, e:
            if isinstance(e.reason, socket.error):
                # Socket errors considered temporary as could stem from a temporary
                # network failure rather
                update_task_status.delay(resource['id'], "URL temporarily unavailable")
            else:
                # Other URLErrors are generally permanent errors, eg unsupported
                # protocol
                update_task_status.delay(resource['id'], "URL unobtainable")
        except Exception, e:
            update_task_status.delay(resource['id'], "Invalid URL")
            logger.error("%s" % e)
        else:
            headers = response.info()
            resource_format = resource['format'].lower()
            ct = get_header(headers, 'content-type')
            cl = get_header(headers, 'content-length')
            dst_dir = os.path.join(settings.ARCHIVE_DIR, package_name)

            # make sure resource does not exceed our maximum content size
            if cl >= str(settings.MAX_CONTENT_LENGTH):
                # TODO: make sure that this is handled properly by the QA command.
                update_task_status.delay(resource['id'], "Content-length exceeds maximum allowed value")
                logger.info("Could not archive %s: exceeds maximum content-length" % resource['url'])
                return

            # try to archive csv files
            if(resource_format == 'csv' or resource_format == 'text/csv' or
               (ct and ct.lower() == 'text/csv')):
                    logger.info("Resource identified as CSV file, attempting to archive")
                    # Assume the head request is behaving correctly and not 
                    # returning content. Make another request for the content
                    response = opener.open(urllib2.Request(url), timeout=url_timeout)
                    length, hash = hash_and_save(settings.ARCHIVE_DIR, resource, response, size = 1024*16)
                    if length:
                        if not os.path.exists(dst_dir):
                            os.mkdir(dst_dir)
                        os.rename(
                            os.path.join(settings.ARCHIVE_DIR, 'archive_%s' % os.getpid()),
                            os.path.join(dst_dir, hash + '.csv'),
                        )
                    update_task_status.delay(resource['id'], 'ok', True, ct, cl, hash)
                    logger.info("Archive success. Saved %s to %s with hash %s" % (resource['url'], dst_dir, hash))
            else:
                update_task_status.delay(resource['id'], 'unrecognised content type', False, ct, cl)
                logger.info("Can not archive this content-type: %s" % ct)


def hash_and_save(archive_folder, resource, response, size=1024*16):
    return 0, 0


@task(name = "archiver.update_task_status")
def update_task_status(*args):
    logger = update_task_status.get_logger()
