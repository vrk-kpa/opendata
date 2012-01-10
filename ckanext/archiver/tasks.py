import os
import hashlib
import httplib
import requests
import json
import urllib
import urlparse
import tempfile
from datetime import datetime
from ckan.lib.celery_app import celery
from webstore_upload import upload_content
from webstore_upload import DATA_FORMATS as WEBSTORE_DATA_FORMATS

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
    httplib.GATEWAY_TIMEOUT: "Gateway timeout",
    httplib.METHOD_NOT_ALLOWED: "405 Method Not Allowed"
}

DATA_FORMATS = [ 
    'csv',
    'text/csv',
    'txt',
    'text/plain',
    'text/html',
    'html',
    'rdf',
    'text/rdf',
    'xml',
    'xls',
    'application/ms-excel',
    'application/vnd.ms-excel',    
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

class ArchiverError(Exception):
    pass
class DownloadError(Exception):
    pass
class LinkCheckerError(Exception):
    pass
class CkanError(Exception):
    pass


def download(context, resource, url_timeout=30,
             max_content_length=settings.MAX_CONTENT_LENGTH,
             data_formats=DATA_FORMATS):

    link_context = "{}"
    link_data = json.dumps({
        'url': resource['url'],
        'url_timeout': url_timeout
    })
    headers = json.loads(link_checker(link_context, link_data))

    resource_format = resource['format'].lower()
    ct = headers.get('content-type', '').lower()
    cl = headers.get('content-length')

    resource_changed = (resource.get('mimetype') != ct) or (resource.get('size') != cl)
    if resource_changed:
        resource['mimetype'] = ct
        resource['size'] = cl

    # make sure resource content-length does not exceed our maximum
    if cl and int(cl) >= max_content_length:
        if resource_changed: 
            _update_resource(context, resource) 
        # record fact that resource is too large to archive
        raise DownloadError("Content-length %s exceeds maximum allowed value %s" %
            (cl, max_content_length))                                                      

    # check that resource is a data file
    if not (resource_format in data_formats or ct.lower() in data_formats):
        if resource_changed: 
            _update_resource(context, resource) 
        raise DownloadError("Of content type %s, not downloading" % ct) 

    # get the resource and archive it
    res = requests.get(resource['url'], timeout = url_timeout)
    length, hash, saved_file = _save_resource(resource, res, max_content_length)

    # check that resource did not exceed maximum size when being saved
    # (content-length header could have been invalid/corrupted, or not accurate
    # if resource was streamed)
    #
    # TODO: remove partially archived file in this case
    if length >= max_content_length:
        if resource_changed: 
            _update_resource(context, resource) 
        # record fact that resource is too large to archive
        raise DownloadError("Content-length after streaming reached maximum allowed value of %s" % 
            max_content_length) 

    # update the resource metadata in CKAN if the resource has changed
    if resource.get('hash') != hash:
        resource['hash'] = hash
        try:
            # This may fail for archiver.update() as a result of the resource
            # not yet existing.
            _update_resource(context, resource)
        except:
            pass
        

    return {'length': length,
            'hash' : hash,
            'headers': headers,
            'saved_file': saved_file}


@celery.task(name = "archiver.clean")
def clean():
    """
    Remove all archived resources.
    """
    logger = clean.get_logger()
    logger.error("clean task not implemented yet")

@celery.task(name = "archiver.update")
def update(context, data):
    try:
        data = json.loads(data)
        context = json.loads(context)
        result = _update(context, data) 
        # Decide whether to trigger the upload task here in response to the update
        return result
    except Exception, e:
        update_task_status(context, {
            'entity_id': data['id'],
            'entity_type': u'resource',
            'task_type': 'archiver',
            'key': u'celery_task_id',
            'value': unicode(update.request.id),
            'error': '%s: %s' % (e.__class__.__name__,  unicode(e)),
            'stack': traceback.format_exc(),
            'last_updated': datetime.now().isoformat()
        })
        raise

def _update(context, data):
    """
    Link check and archive the given resource.

    Returns a JSON dict:

        {
            'resource': the updated resource dict,
            'file_path': path to archived file (if archive successful), or None
        }
    """
    logger = update.get_logger()
    rid = data.pop(u'revision_id')
    api_url = urlparse.urljoin(context['site_url'], 'api/action')

    # check that archive directory exists
    if not os.path.exists(settings.ARCHIVE_DIR):
        logger.info("Creating archive directory: %s" % settings.ARCHIVE_DIR)
        os.mkdir(settings.ARCHIVE_DIR)

    if not data:
        raise ArchiverError('Resource not found')

    result = None
    try:
        result = download(context, data)
        if result is None:
            raise Exception("Download failed")
    except Exception, downloaderr:
        if hasattr(settings, 'RETRIES') and settings.RETRIES:
            update.retry(args=(json.dumps(context), json.dumps(data)), exc=downloaderr)
        else:
            print downloaderr
            return

    # Check here whether we want to upload this content to webstore before 
    # archiving
    if settings.UPLOAD_TO_WEBSTORE and settings.WEBSTORE_URL:
        content_type = result['headers'].get('content-type', '')
        if content_type in WEBSTORE_DATA_FORMATS or context['format'] in WEBSTORE_DATA_FORMATS:
            # If this fails, for instance if webstore is down, then we should force the task
            # to retry in 3 minutes (default value for countdown in retry(...)).
            try:
                context['webstore_url'] = settings.WEBSTORE_URL            
                logger.info("Attempting to upload content to webstore: %s" % context['webstore_url'])                        
                upload_content( context, data, result )
            except Exception, eUpload:
                logger.error( eUpload )
                if hasattr(settings, 'RETRIES') and settings.RETRIES:                
                    data[u'revision_id'] = rid # put this back as we'll need it next time
                    update.retry(args=(json.dumps(context), json.dumps(data)), exc=e)

    logger.info("Attempting to archive resource: %s" % data['url'])
    file_path = archive_resource(context, data, logger, result)

    return json.dumps({
        'resource': data,
        'file_path': file_path
    })


@celery.task(name = "archiver.link_checker")
def link_checker(context, data):
    """
    Check that the resource's url is valid, and accepts a HEAD request.

    Returns a json dict of the headers of the request
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
        raise LinkCheckerError("Invalid url scheme")
    # check that query string is valid
    # see: http://trac.ckan.org/ticket/318
    # TODO: check urls with a better validator? 
    #       eg: ll.url (http://www.livinglogic.de/Python/url/Howto.html)?
    elif any(['/' in parsed_url.query, ':' in parsed_url.query]):
        raise LinkCheckerError("Invalid URL")
    else:
        # Send a head request
        try:
            res = requests.head(url, timeout = url_timeout)
            headers = res.headers
        except ValueError, ve:
            raise LinkCheckerError("Invalid URL")
        if res.error:
            if res.status_code in HTTP_ERROR_CODES:
                error_message = HTTP_ERROR_CODES[res.status_code]
            else:
                error_message = "URL unobtainable"
            raise LinkCheckerError(error_message)

    return json.dumps(headers)


def archive_resource(context, resource, logger, result=None, url_timeout = 30):
    """
    Archive the given resource.
    """
    if result['length']:
        dir = os.path.join(settings.ARCHIVE_DIR, resource['id'])
        if not os.path.exists(dir):
            os.mkdir(dir)
        # try to get a file name from the url
        parsed_url = urlparse.urlparse(resource.get('url'))
        try:
            file_name = parsed_url.path.split('/')[-1] or 'resource'
        except:
            file_name = "resource"
        saved_file = os.path.join(dir, file_name)
        os.rename(result['saved_file'], saved_file)

        # update the resource object: set cache_url and cache_last_updated
        if context.get('cache_url_root'):
            cache_url = urlparse.urljoin(
                context['cache_url_root'], '%s/%s' % (resource['id'], file_name)
            )
            if resource.get('cache_url') != cache_url:
                resource['cache_url'] = cache_url
                resource['cache_last_updated'] = datetime.now().isoformat()
                _update_resource(context, resource)

    return saved_file


def _save_resource(resource, response, max_file_size, chunk_size = 1024*16):
    """
    Write the response content to disk.

    Returns a tuple:

        (file length: int, content hash: string, saved file path: string)
    """
    resource_hash = hashlib.sha1()
    length = 0
    saved_file = None

    #tmp_resource_file = os.path.join(settings.ARCHIVE_DIR, 'archive_%s' % os.getpid())
    fd, tmp_resource_file_path = tempfile.mkstemp()
 
    with open(tmp_resource_file_path, 'wb') as fp:
        for chunk in response.iter_content(chunk_size = chunk_size, decode_unicode=False):
            fp.write(chunk)
            length += len(chunk)
            resource_hash.update(chunk)

            if length >= max_file_size:
                break

    os.close(fd)

    content_hash = unicode(resource_hash.hexdigest())
    return length, content_hash, tmp_resource_file_path


def _update_resource(context, resource):
    """
    Use CKAN API to update the given resource.
    If cannot update, records this fact in the task_status table.

    Returns the content of the response. 
    
    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action')
    resource['last_modified'] = datetime.now().isoformat()
    post_data = json.dumps(resource)
    print api_url + '/resource_update'
    res = requests.post(
        api_url + '/resource_update', post_data,
        headers = {'Authorization': context['apikey'],
                   'Content-Type': 'application/json'}
    )
    
    if res.status_code == 200:
        return res.content
    else:
        raise CkanError('ckan failed to update resource, status_code (%s)' 
                        % res.status_code)


def update_task_status(context, data):
    """
    Use CKAN API to update the task status. The data parameter
    should be a dict representing one row in the task_status table.
    
    Returns the content of the response. 
    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action')
    res = requests.post(
        api_url + '/task_status_update', json.dumps(data),
        headers = {'Authorization': context['apikey'],
                   'Content-Type': 'application/json'}
    )
    if res.status_code == 200:
        return res.content
    else:
        raise CkanError('ckan failed to update task_status, status_code (%s), error %s'  % (res.status_code, res.content))


