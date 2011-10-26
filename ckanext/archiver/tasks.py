import os
import hashlib
import httplib
import requests
import json
import urllib
import urlparse
import copy
from datetime import datetime
from celery.task import task
from celery.execute import send_task

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

DATA_FORMATS = [ 
    'csv',
    'text/csv',
    'txt',
    'text/plain'
    'rdf',
    'text/rdf',
    'xml',
    'xls',
    'application/ms-excel',
    'application/xls',
    'text/xml',
    'tar',
    'application/x-tar',
    'zip',
    'application/zip'
    'gz',
    'application/gzip',
    'application/x-gzip'
]


@task(name = "archiver.clean")
def clean():
    """
    Remove all archived resources.
    """
    logger = clean.get_logger()
    logger.error("clean task not implemented yet")


@task(name = "archiver.update")
def update(context, data):
    """
    Link check and archive the given resource.

    Returns a JSON dict:

        {
            'task_status': dict representing a row in the CKAN task status table,
            'resource': the updated resource dict,
            'file_path': path to archived file (if archive successful), or None
        }
    """
    logger = update.get_logger()
    context = json.loads(context)
    data = json.loads(data)
    data.pop('revision_id')
    api_url = urlparse.urljoin(context['site_url'], 'api/action')

    # check that archive directory exists
    if not os.path.exists(settings.ARCHIVE_DIR):
        logger.info("Creating archive directory: %s" % settings.ARCHIVE_DIR)
        os.mkdir(settings.ARCHIVE_DIR)

    if not data:
        logger.error("Error: Resource not found: %s" % data['id'])
        task_status = {
            'entity_id': data['id'],
            'entity_type': u'resource',
            'task_type': u'archiver',
            'key': u'result',
            'value': u'resource not found',
            'state': u'fail'
        }
        update_success, error_msg = _update_task_status(context, [task_status])
        if not update_success:
            logger.error("Could not update task status: %s" % error_msg)
        return

    logger.info("Attempting to archive resource: %s" % data['url'])
    task_result, file_path = archive_resource(context, data, logger)

    update_success, error_msg = _update_task_status(context, task_result)
    if not update_success:
        logger.error("Could not update task status: %s" % error_msg)

    # call the webstorer if archiving was successful and a webstore url is given
    if file_path and context.get('webstore_url'):   
        data['resource_id'] = data['id']
        data['file_path'] = file_path
        webstorer_task = send_task('webstorer.upload', [json.dumps(context), json.dumps(data)])

        # update task status table with task ID of webstorer task
        webstorer_task_status = {
            'entity_id': data['id'],
            'entity_type': u'resource',
            'task_type': u'archiver',
            'key': u'celery_task_id',
            'value': webstorer_task.task_id,
            'last_updated': datetime.now().isoformat()
        }
        update_success, error_msg = _update_task_status(context, webstorer_task_status)
        if not update_success:
            logger.error("Could not update task status: %s" % error_msg)

    return json.dumps({
        'task_status': task_result,
        'resource': data,
        'file_path': file_path
    })


@task(name = "archiver.link_checker")
def link_checker(context, data):
    """
    Check that the resource's url is valid, and accepts a HEAD request.

    Returns a json dict:

        {   
            'success': True/False,
            'error_message': string containing any error message (empty if no error),
            'headers': dict containing HEAD request headers
        }
    """
    data = json.loads(data)
    url_timeout = data.get('url_timeout', 30)

    success = True
    error_message = ''
    headers = {}

    # Find out if it has unicode characters, and if it does, quote them 
    # so we are left with an ascii string
    try:
        url = data['url'].decode('ascii')
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
        success = False
        error_message = "Invalid url scheme"
    # check that query string is valid
    # see: http://trac.ckan.org/ticket/318
    # TODO: check urls with a better validator? 
    #       eg: ll.url (http://www.livinglogic.de/Python/url/Howto.html)?
    elif any(['/' in parsed_url.query, ':' in parsed_url.query]):
        success = False
        error_message = "Invalid URL"
    else:
        # Send a head request
        try:
            res = requests.head(url, timeout = url_timeout)
            headers = res.headers
        except ValueError, ve:
            success = False
            error_message = "Invalid URL"

        if res.error:
            success = False
            if res.status_code in HTTP_ERROR_CODES:
                error_message = HTTP_ERROR_CODES[res.status_code]
            else:
                error_message = "URL unobtainable"

    return json.dumps({
        'success': success,
        'error_message': error_message,
        'headers': headers
    })


def archive_resource(context, resource, logger, url_timeout = 30):
    """
    Archive the given resource.

    Returns a tuple:

        (task status: dict, path to saved file: string or None)
    """
    link_context = "{}"
    link_data = json.dumps({
        'url': resource['url'],
        'url_timeout': url_timeout
    })
    link_status = json.loads(link_checker(link_context, link_data))
    if not link_status['success']:
        return _task_status(resource, link_status['error_message']), None

    resource_format = resource['format'].lower()
    ct = link_status['headers'].get('content-type', '').lower()
    cl = link_status['headers'].get('content-length')
    dst_dir = os.path.join(settings.ARCHIVE_DIR, resource['id'])

    resource_changed = (resource.get('mimetype') != ct) or (resource.get('size') != cl)
    if resource_changed:
        resource['mimetype'] = ct
        resource['size'] = cl

    # make sure resource content-length does not exceed our maximum
    if cl >= str(settings.MAX_CONTENT_LENGTH):
        if resource_changed: 
            _update_resource(context, resource) 
        # record fact that resource is too large to archive
        error_msg = "Content-length exceeds maximum allowed value"
        return _task_status(resource, error_msg, False, ct, cl), None

    # check that resource is a data file
    if not (resource_format in DATA_FORMATS or ct.lower() in DATA_FORMATS):
        if resource_changed: 
            _update_resource(context, resource) 
        return _task_status(resource, 'unrecognised content type', False, ct, cl), None

    # get the resource and archive it
    logger.info("Resource identified as data file, attempting to archive")
    res = requests.get(resource['url'], timeout = url_timeout)
    length, hash, saved_file = _save_resource(resource, res, dst_dir, settings.MAX_CONTENT_LENGTH)

    # check that resource did not exceed maximum size when being saved
    # (content-length header could have been invalid/corrupted, or not accurate
    # if resource was streamed)
    #
    # TODO: remove partially archived file in this case
    if length >= settings.MAX_CONTENT_LENGTH:
        if resource_changed: 
            _update_resource(context, resource) 
        # record fact that resource is too large to archive
        error_msg = "Content-length exceeds maximum allowed value"
        return _task_status(resource, error_msg, False, ct, cl), None

    # TODO: check length != 0 and that saved_file != None

    # update the resource metadata in CKAN
    resource['hash'] = hash
    resource_updated, error_msg = _update_resource(context, resource)
    if not resource_updated:
        logger.error("Could not update resource: %s" % error_msg)

    logger.info("Archiver finished. Saved %s to %s" % (resource['id'], dst_dir))
    return _task_status(resource, 'ok', True, ct, cl), saved_file


def _save_resource(resource, response, dir, max_file_size, chunk_size = 1024*16):
    """
    Write the response content to disk.

    Returns a tuple:

        (file length: int, content hash: string, saved file path: string)
    """
    resource_hash = hashlib.sha1()
    length = 0
    saved_file = None

    tmp_resource_file = os.path.join(settings.ARCHIVE_DIR, 'archive_%s' % os.getpid())
    fp = open(tmp_resource_file, 'wb')

    for chunk in response.iter_content(chunk_size = chunk_size):
        fp.write(chunk)
        length += len(chunk)
        resource_hash.update(chunk)

        if length >= max_file_size:
            break

    fp.close()
    content_hash = unicode(resource_hash.hexdigest())

    # if some data was successfully written to the temp resource file, rename it and
    # add it to the target directory
    if length:
        if not os.path.exists(dir):
            os.mkdir(dir)
        # try to get a file name from the url
        parsed_url = urlparse.urlparse(resource.get('url'))
        try:
            file_name = parsed_url.path.split('/')[-1] or 'resource'
        except:
            file_name = "resource"
        saved_file = os.path.join(dir, file_name)
        os.rename(tmp_resource_file, saved_file)

    return length, content_hash, saved_file

def _update_resource(context, resource):
    """
    Use CKAN API to update the given resource.
    If cannot update, records this fact in the task_status table.

    Returns a tuple: 
    
        (was update successful?: bool, response from server: requests.Response)
    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action')
    resource['last_modified'] = datetime.now().isoformat()
    post_data = json.dumps(resource)
    res = requests.post(
        api_url + '/resource_update', post_data,
        headers = {'Authorization': context['apikey']}
    )

    if res.status_code == 200:
        return True, res.content
    else:
        _update_task_status(context, _task_status(
            resource, "Could not update resource: %s" % res.content, False
        ))
        return False, res.content

def _task_status(resource, message, success=False, content_type=None, content_length=None):
    """
    Return a dict representing a row in the task_status table.
    """
    return {
        'entity_id': resource['id'],
        'entity_type': u'resource',
        'task_type': u'archiver',
        'key': u'result',
        'value': message,
        'state': u'success' if success else u'fail',
        'last_updated': datetime.now().isoformat()
    }

def _update_task_status(context, data):
    """
    Use CKAN API to update the task status. The data parameter
    should be a dict representing one row in the task_status table.
    
    Returns a tuple:
        
        (response status code: int, response content)
    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action')
    res = requests.post(
        api_url + '/task_status_update', json.dumps(data),
        headers = {'Authorization': context['apikey']}
    )
    return res.status_code == 200, res.content

