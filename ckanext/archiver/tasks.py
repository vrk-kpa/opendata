import os
import hashlib
import httplib
import requests
import json
import urllib
import urlparse
import StringIO
import copy
from celery.task import task

try:
    from ckanext.archiver import settings
except ImportError:
    from ckanext.archiver import default_settings as settings

HTTP_ERROR_CODES = {
    httplib.MULTIPLE_CHOICES: "300 Multiple Choices not implemented",
    httplib.USE_PROXY: "305 Use Proxy not implemented",
    httplib.INTERNAL_SERVER_ERROR: "Internal server error on the remote server",
    httplib.BAD_GATEWAY: "Bad gateway",
    httplib.SERVICE_UNAVAILABLE: "Service unavailable",
    httplib.GATEWAY_TIMEOUT: "Gateway timeout"
}


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
    api_url = urlparse.urljoin(settings.CKAN_URL, 'api/action')

    # check that archive directory exists
    if not os.path.exists(settings.ARCHIVE_DIR):
        logger.info("Creating archive directory: %s" % settings.ARCHIVE_DIR)
        os.mkdir(settings.ARCHIVE_DIR)

    if package_id:
        post_data = json.dumps({'id': package_id})
        res = requests.post(api_url + '/package_show', post_data)
        package = json.loads(res.content).get('result')

        if package:
            packages = [package]
        else:
            logger.error("Error: Package not found: %s" % package_id)
    else:
        post_data = {}
        if limit:
            post_data['limit'] = limit
            logger.info("Limiting results to %d packages" % limit)
        post_data = json.dumps(post_data)
        res = requests.post(api_url + '/current_package_list_with_resources', post_data)
        packages = json.loads(res.content).get('result')

    logger.info("Total packages to update: %d" % len(packages))
    if not packages:
        return

    task_results = []

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
                task_results.extend(archive_resource(resource, package['name'], logger))

    update_success, error_msg = _update_task_status(task_results)
    if not update_success:
        logger.error("Could not update task status: %s" % error_msg)


def archive_resource(resource, package_name, logger, url_timeout = 30):
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
        return _make_status_messages(resource, "Invalid url scheme")
    # check that query string is valid
    # see: http://trac.ckan.org/ticket/318
    # TODO: check urls with a better validator? 
    #       eg: ll.url (http://www.livinglogic.de/Python/url/Howto.html)?
    elif any(['/' in parsed_url.query, ':' in parsed_url.query]):
        return _make_status_messages(resource, "Invalid URL")
    else:
        # Send a head request
        try:
            res = requests.head(url, timeout = url_timeout)
        except ValueError, ve:
            return _make_status_messages(resource, "Invalid URL")

        if res.error:
            if res.status_code in HTTP_ERROR_CODES:
                return _make_status_messages(resource, HTTP_ERROR_CODES[res.status_code])
            else:
                return _make_status_messages(resource, "URL unobtainable")
            return

        resource_format = resource['format'].lower()
        ct = res.headers.get('content-type', '').lower()
        cl = res.headers.get('content-length')
        dst_dir = os.path.join(settings.ARCHIVE_DIR, package_name)

        # make sure resource does not exceed our maximum content size
        if cl >= str(settings.MAX_CONTENT_LENGTH):
            return _make_status_messages(resource, "Content-length exceeds maximum allowed value")

        # try to archive csv files
        if(resource_format == 'csv' or resource_format == 'text/csv' or
           (ct and ct.lower() == 'text/csv')):
                logger.info("Resource identified as CSV file, attempting to archive")

                res = requests.get(url, timeout = url_timeout)
                length, hash = _save_resource(resource, res, dst_dir)

                hash_updated, error_msg = _set_resource_hash(resource, hash)
                if not hash_updated:
                    logger.error("Could not update resource hash: %s" % error_msg)

                logger.info("Archive finished. Saved %s to %s with hash %s" % (resource['url'], dst_dir, hash))
                return _make_status_messages(resource, 'ok', True, ct, cl)
        else:
            return _make_status_messages(resource, 'unrecognised content type', False, ct, cl)


def _save_resource(resource, response, dir, size=1024*16):
    resource_hash = hashlib.sha1()
    length = 0

    tmp_resource_file = os.path.join(settings.ARCHIVE_DIR, 'archive_%s' % os.getpid())
    fp = open(tmp_resource_file, 'wb')

    content = StringIO.StringIO(response.content)
    chunk = content.read(size)
    while chunk: 
        fp.write(chunk)
        length += len(chunk)
        resource_hash.update(chunk)
        chunk = content.read(size)
    fp.close()

    content_hash = unicode(resource_hash.hexdigest())

    # if some data was successfully written to the temp resource file, rename it and
    # add it to the target directory
    if length:
        if not os.path.exists(dir):
            os.mkdir(dir)
        os.rename(tmp_resource_file, os.path.join(dir, content_hash + '.csv'))

    return length, content_hash

def _set_resource_hash(resource, hash):
    """
    Use CKAN API to change the hash value of the given resource.
    Returns a tuple: (True if update was successful, response from server)
    """
    api_url = urlparse.urljoin(settings.CKAN_URL, 'api/action')
    resource['hash'] = hash
    post_data = json.dumps(resource)
    res = requests.post(
        api_url + '/resource_update', post_data,
        headers = {'Authorization': settings.API_KEY}
    )
    return res.status_code == 200, res.content

def _make_status_messages(resource, message, success=False, 
                          content_type=None, content_length=None):
    """
    Return a list of dicts, where each dict is a row in the task_status table.
    """
    messages = []
    entity_type = u'resource'
    task_type = u'archiver'
    task_state = u'success' if success else u'fail'

    status = {
        'entity_id': resource['id'],
        'entity_type': entity_type,
        'task_type': task_type,
        'key': u'result',
        'value': message,
        'state': task_state
    }
    messages.append(status)

    if content_type:
        ct = copy.deepcopy(status)
        ct['key'] = u'content_type'
        ct['value'] = unicode(content_type)
        messages.append(ct)

    if content_length:
        cl = copy.deepcopy(status)
        cl['key'] = u'content_length'
        cl['value'] = unicode(content_length)
        messages.append(cl)

    return messages

def _update_task_status(data):
    api_url = urlparse.urljoin(settings.CKAN_URL, 'api/action')

    # data must be in a json encoded dict 
    post_data = json.dumps({'data': data})

    res = requests.post(
        api_url + '/task_status_update_many', post_data,
        headers = {'Authorization': settings.API_KEY}
    )
    return res.status_code == 200, res.content
