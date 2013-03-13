import os
import hashlib
import httplib
import requests
import json
import urllib
import urlparse
import tempfile
import traceback
import shutil
from datetime import datetime

from ckan.lib.celery_app import celery

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

DEFAULT_DATA_FORMATS = [ 
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
    'application/x-gzip',
    'application/octet-stream'
]

class ArchiverError(Exception):
    pass
class DownloadError(Exception):
    pass
class ChooseNotToDownload(Exception):
    pass
class LinkCheckerError(Exception):
    pass
class LinkInvalidError(LinkCheckerError):
    pass
class LinkHeadRequestError(LinkCheckerError):
    pass
class CkanError(Exception):
    pass

def _clean_content_type(ct):
    # For now we should remove the charset from the content type and 
    # handle it better, differently, later on.
    if 'charset' in ct:
        return ct[:ct.index(';')]
    return ct

def download(context, resource, url_timeout=30,
             max_content_length=settings.MAX_CONTENT_LENGTH,
             data_formats=DEFAULT_DATA_FORMATS):
    '''Given a resource, tries to download it.

    If the size or format is not acceptable for download then
    ChooseNotToDownload is raised.

    If there is an error performing the download then
    DownloadError is raised.
    '''
    
    log = update.get_logger()
    
    url = resource['url']

    if (resource.get('resource_type') == 'file.upload' and
        not url.startswith('http')):
        url = context['site_url'].rstrip('/') + url

    link_context = "{}"
    link_data = json.dumps({
        'url': url,
        'url_timeout': url_timeout
    })

    headers = json.loads(link_checker(link_context, link_data))

    resource_format = resource['format'].lower()
    ct = _clean_content_type( headers.get('content-type', '').lower() )
    cl = headers.get('content-length') 

    resource_changed = False

    if resource.get('mimetype') != ct:
        resource_changed = True
        resource['mimetype'] = ct

    # this is to store the size in case there is an error, but the real size check
    # is done after dowloading the data file, with its real length
    if cl is not None and (resource.get('size') != cl):
        resource_changed = True
        resource['size'] = cl

    # make sure resource content-length does not exceed our maximum
    if cl and int(cl) >= max_content_length:
        if resource_changed: 
            _update_resource(context, resource, log)
        # record fact that resource is too large to archive
        log.warning('Resource too large to download: %s > max (%s). Resource: %s %r',
                 cl, max_content_length, resource['id'], url)
        raise ChooseNotToDownload("Content-length %s exceeds maximum allowed value %s" %
            (cl, max_content_length))                                                      

    # check that resource is a data file
    if data_formats != 'all' and not (resource_format in data_formats or ct.lower() in data_formats):
        if resource_changed: 
            _update_resource(context, resource, log)
        log.info('Resource wrong type to download: %s / %s. Resource: %s %r',
                 resource_format, ct.lower(), resource['id'], url)
        raise ChooseNotToDownload('Of content type "%s" which is not a recognised data file for download' % ct) 

    # get the resource and archive it
    try:
        res = requests.get(url, timeout=url_timeout)
    except requests.exceptions.ConnectionError, e:
        raise DownloadError('Connection error: %s' % e)
    except requests.exceptions.HTTPError, e:
        raise DownloadError('Invalid HTTP response: %s' % e)
    except requests.exceptions.Timeout, e:
        raise DownloadError('Connection timed out after %ss' % url_timeout)
    except requests.exceptions.TooManyRedirects, e:
        raise DownloadError('Too many redirects')
    except requests.exceptions.RequestException, e:
        raise DownloadError('Error downloading: %s' % e)
    except Exception, e:
        raise DownloadError('Error with the download: %s' % e)

    if not res.ok:
        raise DownloadError('Download failed with status code: %s' % res.status_code)

    length, hash, saved_file = _save_resource(resource, res, max_content_length)

    # check if resource size changed
    if unicode(length) != resource.get('size'):
        resource_changed = True
        resource['size'] = unicode(length)

    # check that resource did not exceed maximum size when being saved
    # (content-length header could have been invalid/corrupted, or not accurate
    # if resource was streamed)
    #
    # TODO: remove partially archived file in this case
    if length >= max_content_length:
        if resource_changed: 
            _update_resource(context, resource, log)
        # record fact that resource is too large to archive
        log.warning('Resource found to be too large to archive: %s > max (%s). Resource: %s %r',
                 length, max_content_length, resource['id'], url)
        raise ChooseNotToDownload("Content-length after streaming reached maximum allowed value of %s" % 
            max_content_length)         

    # zero length usually indicates a problem too
    if length == 0:
        if resource_changed: 
            _update_resource(context, resource, log)
        # record fact that resource is zero length
        log.warning('Resource found was zero length - not archiving. Resource: %s %r',
                 resource['id'], url)
        raise DownloadError("Content-length after streaming was zero")

    # update the resource metadata in CKAN if the resource has changed
    if resource.get('hash') != hash:
        resource['hash'] = hash
        try:
            # This may fail for archiver.update() as a result of the resource
            # not yet existing, but is necessary for dependant extensions.
            _update_resource(context, resource, log)
        except:
            pass

    log.info('Resource downloaded: id=%s url=%r cache_filename=%s length=%s hash=%s',
             resource['id'], url, saved_file, length, hash)

    return {'length': length,
            'hash' : hash,
            'headers': headers,
            'saved_file': saved_file}


@celery.task(name = "archiver.clean")
def clean():
    """
    Remove all archived resources.
    """
    log = clean.get_logger()
    log.error("clean task not implemented yet")

@celery.task(name = "archiver.update")
def update(context, data):
    log = update.get_logger()
    log.info('Starting update task: %r', data)
    try:
        data = json.loads(data)
        context = json.loads(context)
        result = _update(context, data) 
        return result
    except ArchiverError, e:
        log.error('Archive error during update: %s\nResource: %s',
                  e, data)
    except Exception, e:
        log.error('Error occurred during archiving resource: %s\nResource: %r',
                  e, data)
        update_task_status(context, {
            'entity_id': data['id'],
            'entity_type': u'resource',
            'task_type': 'archiver',
            'key': u'celery_task_id',
            'value': unicode(update.request.id),
            'error': '%s: %s' % (e.__class__.__name__,  unicode(e)),
            'stack': traceback.format_exc(),
            'last_updated': datetime.now().isoformat()
        }, log)
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
    log = update.get_logger()
    data.pop(u'revision_id', None)

    # check that archive directory exists
    if not os.path.exists(settings.ARCHIVE_DIR):
        log.info("Creating archive directory: %s" % settings.ARCHIVE_DIR)
        os.mkdir(settings.ARCHIVE_DIR)

    if not data:
        raise ArchiverError('Resource not found')

    if hasattr(settings, 'DATA_FORMATS') and settings.DATA_FORMATS:
        data_formats = settings.DATA_FORMATS
    else:
        data_formats = DEFAULT_DATA_FORMATS

    log.info("Attempting to download resource: %s" % data['url'])
    result = None
    try:
        result = download(context, data, data_formats=data_formats)
        if result is None:
            raise ArchiverError("Download failed")
    except DownloadError, downloaderr:
        log.info('Download failed: %r, %r', downloaderr, downloaderr.args)
        return
    except ChooseNotToDownload, e:
        log.info('Download not carried out: %r, %r', e, e.args)
        return
    except Exception, downloaderr:
        log.info('Download failure: %r, %r', downloaderr, downloaderr.args)
        return

    log.info("Attempting to archive resource: %s" % data['url'])
    file_path = archive_resource(context, data, log, result)

    return json.dumps({
        'resource': data,
        'file_path': file_path
    })


@celery.task(name = "archiver.link_checker")
def link_checker(context, data):
    """
    Check that the resource's url is valid, and accepts a HEAD request.

    Raises LinkInvalidError if the URL is invalid
    Raises LinkHeadRequestError if HEAD request fails

    Returns a json dict of the headers of the request
    """
    log = update.get_logger()
    data = json.loads(data)
    url_timeout = data.get('url_timeout', 30)

    success = True
    error_message = ''
    headers = {}

    # Find out if it has unicode characters, and if it does, quote them 
    # so we are left with an ascii string
    url = data['url']
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
        raise LinkInvalidError("Invalid url scheme")
    # check that query string is valid
    # see: http://trac.ckan.org/ticket/318
    # TODO: check urls with a better validator? 
    #       eg: ll.url (http://www.livinglogic.de/Python/url/Howto.html)?
    elif any(['/' in parsed_url.query, ':' in parsed_url.query]):
        raise LinkInvalidError("Invalid URL")
    else:
        # Send a head request
        try:
            res = requests.head(url, timeout=url_timeout)
            headers = res.headers
        except httplib.InvalidURL, ve:
            log.error("Could not make a head request to %r, error is: %s. Package is: %r. This sometimes happens when using an old version of requests on a URL which issues a 301 redirect. Version=%s", url, ve, data.get('package'), requests.__version__)
            raise LinkHeadRequestError("Invalid URL or Redirect Link")
        except ValueError, ve:
            log.error("Could not make a head request to %r, error is: %s. Package is: %r.", url, ve, data.get('package'))
            raise LinkHeadRequestError("Could not make HEAD request")
        except requests.exceptions.ConnectionError, e:
            raise LinkHeadRequestError('Connection error: %s' % e)
        except requests.exceptions.HTTPError, e:
            raise LinkHeadRequestError('Invalid HTTP response: %s' % e)
        except requests.exceptions.Timeout, e:
            raise LinkHeadRequestError('Connection timed out after %ss' % url_timeout)
        except requests.exceptions.TooManyRedirects, e:
            raise LinkHeadRequestError('Too many redirects')
        except requests.exceptions.RequestException, e:
            raise LinkHeadRequestError('Error during request: %s' % e)
        except Exception, e:
            raise LinkHeadRequestError('Error with the request: %s' % e)
        else:
            if not res.ok or res.status_code >= 400:
                if res.status_code in HTTP_ERROR_CODES:
                    error_message = 'Server returned error: %s' % HTTP_ERROR_CODES[res.status_code]
                else:
                    error_message = "URL unobtainable: Server returned HTTP %s" % res.status_code
                raise LinkHeadRequestError(error_message)
    return json.dumps(headers)

def archive_resource(context, resource, log, result=None, url_timeout = 30):
    """
    Archive the given resource. Downloads the file and updates the
    resource with the link to it.
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
        shutil.move(result['saved_file'], saved_file)
        os.chmod(saved_file, 0644) # allow other users to read it
        log.info('Archived resource as: %s', saved_file)
        
        # update the resource object: set cache_url and cache_last_updated
        if context.get('cache_url_root'):
            cache_url = urlparse.urljoin(
                context['cache_url_root'], '%s/%s' % (resource['id'], file_name)
            )
            if resource.get('cache_url') != cache_url:
                resource['cache_url'] = cache_url
                resource['cache_last_updated'] = datetime.now().isoformat()
                log.info('Updating resource with cache_url=%s', cache_url)
                _update_resource(context, resource, log)
            else:
                log.info('Not updating resource since cache_url is unchanged: %s',
                          cache_url)
        else:
            log.warning('Not updated resource because no value for cache_url_root')

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


def _update_resource(context, resource, log):
    """
    Use CKAN API to update the given resource.
    If cannot update, records this fact in the task_status table.

    Returns the content of the response. 
    
    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/resource_update'
    resource['last_modified'] = datetime.now().isoformat()
    post_data = json.dumps(resource)
    res = requests.post(
        api_url, post_data,
        headers = {'Authorization': context['apikey'],
                   'Content-Type': 'application/json'}
    )
    
    if res.status_code == 200:
        log.info('Resource updated OK: %s', resource['id'])
        return res.content
    else:
        try:
            content = res.content
        except:
            content = '<could not read request content to discover error>'
        log.error('ckan failed to update resource, status_code (%s), error %s. Maybe the API key or site URL are wrong?.\ncontext: %r\nresource: %r\nres: %r\nres.error: %r\npost_data: %r\napi_url: %r'
                        % (res.status_code, content, context, resource, res, res.error, post_data, api_url))
        raise CkanError('ckan failed to update resource, status_code (%s), error %s'  % (res.status_code, content))

def update_task_status(context, data, log):
    """
    Use CKAN API to update the task status. The data parameter
    should be a dict representing one row in the task_status table.
    
    Returns the content of the response. 
    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/task_status_update'
    post_data = json.dumps(data)
    res = requests.post(
        api_url, post_data,
        headers = {'Authorization': context['site_user_apikey'],
                   'Content-Type': 'application/json'}
    )
    if res.status_code == 200:
        log.info('Task status updated OK')
        return res.content
    else:
        try:
            content = res.content
        except:
            content = '<could not read request content to discover error>'
        log.error('ckan failed to update task_status, status_code (%s), error %s. Maybe the API key or site URL are wrong?.\ncontext: %r\ndata: %r\nres: %r\nres.error: %r\npost_data: %r\napi_url: %r'
                        % (res.status_code, content, context, data, res, res.error, post_data, api_url))
        raise CkanError('ckan failed to update task_status, status_code (%s), error %s'  % (res.status_code, content))

