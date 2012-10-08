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
import datetime

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

class ArchiverError(Exception):
    pass
class DownloadError(ArchiverError):
    pass
class ArchiveError(ArchiverError):
    pass
class ChooseNotToDownload(ArchiverError):
    pass
class LinkCheckerError(ArchiverError):
    pass
class LinkInvalidError(LinkCheckerError):
    pass
class LinkHeadRequestError(LinkCheckerError):
    pass
class CkanError(ArchiverError):
    pass

def _clean_content_type(ct):
    # For now we should remove the charset from the content type and 
    # handle it better, differently, later on.
    if 'charset' in ct:
        return ct[:ct.index(';')]
    return ct

def download(context, resource, url_timeout=30,
             max_content_length=settings.MAX_CONTENT_LENGTH):
    '''Given a resource, tries to download it.

    If the size or format is not acceptable for download then
    ChooseNotToDownload is raised.

    Params:
      resource - dict of the resource

    Exceptions from link_checker may be propagated:
       LinkInvalidError if the URL is invalid
       LinkHeadRequestError if HEAD request fails

    If there is an error performing the download, raises:
       DownloadError

    If download is not suitable (e.g. too large), raises:
       ChooseNotToDownload
    
    Returns a dict of results of a successful download:
      length, hash, headers, saved_file
    Updates the resource values for: mimetype, size, hash
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
    log.info('GET succeeded. Content starts: %r', res.content[:10])

    length, hash, saved_file_path = _save_resource(resource, res, max_content_length)
    log.info('Resource saved. Length: %s File: %s', length, saved_file_path)

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

    # zero length (or just one byte) indicates a problem too
    if length < 2:
        if resource_changed: 
            _update_resource(context, resource, log)
        # record fact that resource is zero length
        log.warning('Resource found was length %i - not archiving. Resource: %s %r',
                 length, resource['id'], url)
        raise DownloadError("Content-length after streaming was %i" % length)

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
             resource['id'], url, saved_file_path, length, hash)

    return {'length': length,
            'hash' : hash,
            'headers': headers,
            'saved_file': saved_file_path}


@celery.task(name = "archiver.clean")
def clean():
    """
    Remove all archived resources.
    """
    log = clean.get_logger()
    log.error("clean task not implemented yet")

@celery.task(name = "archiver.update")
def update(context, data):
    '''
    Archive a resource.

    Params:
      data - resource_dict
             e.g. {
                   "revision_id": "2bc8ed56-8900-431a-b556-2417f309f365",
                   "id": "842062b2-e146-4c5f-80e8-64d072ad758d"}
                   "content_length": "35731",
                   "hash": "",
                   "description": "",
                   "format": "",
                   "url": "http://www.justice.gov.uk/publications/companywindingupandbankruptcy.htm",
                   "openness_score_failure_count": "0",
                   "content_type": "text/html",
                   "openness_score": "1",
                   "openness_score_reason": "obtainable via web page",
                   "position": 0,
    '''
    log = update.get_logger()
    log.info('Starting update task: %r', data)
    try:
        data = json.loads(data)
        context = json.loads(context)
        result = _update(context, data) 
        return result
    except Exception, e:
        # Any problem at all is recorded in task_status and then reraised
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
            'last_updated': datetime.datetime.now().isoformat()
        }, log)
        raise

def _update(context, resource):
    """
    Link check and archive the given resource.
    Records result in the task_status key='status'.
    If successful, updates the resource with the cache_url & hash etc.

    Params:
      resource - resource dict

    Should only raise on a fundamental error:
      ArchiverError
      CkanError

    Returns a JSON dict, ready to be returned from the celery task giving a
    success status:
        {
            'resource': the updated resource dict,
            'file_path': path to archived file (if archive successful), or None
        }
    If not successful, returns None.
    """
    log = update.get_logger()

    resource.pop(u'revision_id', None)
    if not resource:
        raise ArchiverError('Resource not found')

    # check that archive directory exists
    if not os.path.exists(settings.ARCHIVE_DIR):
        log.info("Creating archive directory: %s" % settings.ARCHIVE_DIR)
        os.mkdir(settings.ARCHIVE_DIR)

    # Get current task_status
    status = get_status(context, resource['id'], log)
    def _save_status(has_passed, status_txt, exception, status, resource_id):
        # NB the values of status_txt are used in ckanext-qa tasks.py,
        #    so if you change them here, change them there too.
        last_success = status.get('last_success', '')
        first_failure = status.get('first_failure', '')
        failure_count = status.get('failure_count', 0)
        if has_passed:
            last_success = datetime.datetime.now().isoformat()
            first_failure = ''
            failure_count = 0
            reason = ''
        else:
            if not first_failure:
                first_failure = datetime.datetime.now().isoformat()
            failure_count += 1
            reason = '%s' % exception
        save_status(context, resource_id, status_txt,
                    reason,
                    last_success, first_failure,
                    failure_count, log)        

    log.info("Attempting to download resource: %s" % resource['url'])
    result = None
    try:
        result = download(context, resource)
        if result is None:
            raise ArchiverError("Download failed")
    except LinkInvalidError, e:
        log.info('URL invalid: %r, %r', e, e.args)
        _save_status(False, 'URL invalid', e, status, resource['id'])
        return
    except LinkHeadRequestError, e:
        log.info('Link head request error: %s', e.args)
        _save_status(False, 'URL request failed', e, status, resource['id'])
        return
    except DownloadError, e:
        log.info('Download failed: %r, %r', e, e.args)
        _save_status(False, 'Download error', e, status, resource['id'])
        return
    except ChooseNotToDownload, e:
        log.info('Download not carried out: %r, %r', e, e.args)
        _save_status(False, 'Chose not to download', e, status, resource['id'])
        return
    except Exception, downloaderr:
        log.error('Uncaught download failure: %r, %r', downloaderr, downloaderr.args)
        _save_status(False, 'Download failure', e, status, resource['id'])
        return

    log.info('Attempting to archive resource')
    try:
        file_path = archive_resource(context, resource, log, result)
    except ArchiveError, e:
        log.error('System error during archival: %r, %r', e, e.args)
        _save_status(False, 'System error during archival', e, status, resource['id'])
        return

    # Success
    _save_status(True, 'Archived successfully', '', status, resource['id'])
    return json.dumps({
        'resource': resource,
        'file_path': file_path
    })


@celery.task(name = "archiver.link_checker")
def link_checker(context, data):
    """
    Check that the resource's url is valid, and accepts a HEAD request.

    data is a JSON dict describing the link:
        { 'url': url,
          'url_timeout': url_timeout }

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
            if res.error or res.status_code >= 400:
                if res.status_code in HTTP_ERROR_CODES:
                    error_message = 'Server returned error: %s' % HTTP_ERROR_CODES[res.status_code]
                else:
                    error_message = "URL unobtainable: Server returned HTTP %s" % res.status_code
                raise LinkHeadRequestError(error_message)
    return json.dumps(headers)

def archive_resource(context, resource, log, result=None, url_timeout=30):
    """
    Archive the given resource. Moves the file from the temporary location
    given in download() and updates the resource with the link to it.

    Params:
       result - result of the download(), containing keys: length, saved_file

    If there is a failure, raises ArchiveError.
    
    Updates resource keys: cache_url, cache_last_updated, cache_filepath
    Returns
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
        resource['cache_filepath'] = saved_file
        
        # update the resource object: set cache_url and cache_last_updated
        if context.get('cache_url_root'):
            cache_url = urlparse.urljoin(
                context['cache_url_root'], '%s/%s' % (resource['id'], file_name)
            )
            if resource.get('cache_url') != cache_url:
                resource['cache_url'] = cache_url
                resource['cache_last_updated'] = datetime.datetime.now().isoformat()
                log.info('Updating resource with cache_url=%s', cache_url)
                _update_resource(context, resource, log)
            else:
                log.info('Not updating resource since cache_url is unchanged: %s',
                          cache_url)
        else:
            log.warning('Not saved cache_url because no value for cache_url_root in config')
            raise ArchiveError('No value for cache_url_root in config')

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

    Params:
      context - dict containing 'apikey' and 'site_url'
      resource - dict of the resource containing

    Returns the content of the response. 
    
    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/resource_update'
    resource['last_modified'] = datetime.datetime.now().isoformat()
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
    Use CKAN API to update the task status.

    Params:
      context - dict containing 'site_url', 'site_user_apikey'
      data - dict representing one row in the task_status table:
               entity_id, entity_type, task_type, key, value,
               error, stack, last_updated

    May raise CkanError if the request fails.
    
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
    log.info('Task status updated ok: %s=%s', key, value)

def get_task_status(key, context, resource_id, log):
    '''Gets a row from the task_status table as a dict including keys:
       'value', 'error', 'stack'
    If the key isn\'t there, returns None.'''
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/task_status_show'
    response = requests.post(
        api_url,
        json.dumps({'entity_id': resource_id, 'task_type': 'archiver',
                    'key': key}),
        headers={'Authorization': context['apikey'],
                 'Content-Type': 'application/json'}
    )
    if response.content:
        try:
            res_dict = json.loads(response.content)
        except ValueError, e:
            raise CkanError('CKAN response not JSON: %s', response.content)
    else:
        res_dict = {}
    if response.status_code == 404 and res_dict['success'] == False:
        return None
    elif response.error:
        log.error('Error getting %s. Error=%r\napi_url=%r\ncode=%r\ncontent=%r',
                  key, response.error, api_url, response.status_code, response.content)
        raise CkanError('Error getting %s' % key)
    elif res_dict['success']:
        result = res_dict['result']
    else:
        log.error('Error getting %s. Status=%r Error=%r\napi_url=%r',
                  key, response.status_code, response.content, api_url)
        raise CkanError('Error getting %s' % key)
    return result

def get_status(context, resource_id, log):
    '''Returns a dict of the current archiver 'status'.
    (task status value where key='status')

    May propagate CkanError if the request fails.
    '''
    task_status = get_task_status('status', context, resource_id, log)
    if task_status:
        status = json.loads(task_status['error']) \
                 if task_status['error'] else {}
        status['value'] = task_status['value']
        log.info('Previous status checked ok: %s', status)
    else:
        status = {'value': '', 'reason': '',
                 'last_success': '', 'first_failure': '', 'failure_count': 0}
        log.info('Previous status blank - using default: %s', status)
    return status

def save_status(context, resource_id, status, reason,
                last_success, first_failure, failure_count, log):
    '''Writes to the task status table the result of a an attempt to download
    the resource.

    May propagate a CkanError.
    '''
    now = datetime.datetime.now().isoformat()
    data = {
            'entity_id': resource_id,
            'entity_type': u'resource',
            'task_type': 'archiver',
            'key': u'status',
            'value': status,
            'error': json.dumps({
                'reason': reason,
                'last_success': last_success,
                'first_failure': first_failure,
                'failure_count': failure_count,
                }),
            'last_updated': now
        }
    
    update_task_status(context, data, log)
    log.info('Saved status: %r reason=%r last_success=%r first_failure=%r failure_count=%r',
             status, reason, last_success, first_failure, failure_count)
