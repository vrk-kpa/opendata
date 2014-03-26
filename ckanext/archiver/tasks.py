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
import copy

from requests.packages import urllib3

from ckan.lib.celery_app import celery

try:
    from ckanext.archiver import settings
except ImportError:
    from ckanext.archiver import default_settings as settings


ALLOWED_SCHEMES = set(('http', 'https', 'ftp'))

# NB Be very careful changing these status strings. They are also used in
# ckanext-qa tasks.py.
LINK_STATUSES__BROKEN = ('URL invalid', 'URL request failed', 'Download error')
LINK_STATUSES__NOT_SURE = ('Chose not to download', 'Download failure',
                           'System error during archival')
LINK_STATUSES__OK = ('Archived successfully',)
LINK_STATUSES__ALL = LINK_STATUSES__BROKEN + LINK_STATUSES__NOT_SURE + \
                     LINK_STATUSES__OK

USER_AGENT = 'ckanext-archiver'
CONFIG_LOADED = False

def load_config():
    config_filepath = os.environ.get('CKAN_INI') or '/var/ckan/ckan.ini'
    if not config_filepath:
        raise Exception("Configuration file not specified in CKAN_INI")

    import paste.deploy
    config_abs_path = os.path.abspath(config_filepath)
    conf = paste.deploy.appconfig('config:' + config_abs_path)
    import ckan
    ckan.config.environment.load_environment(conf.global_conf,
            conf.local_conf)

    global CONFIG_LOADED
    CONFIG_LOADED = True
    print "config loaded"

def register_translator():
    # Register a translator in this thread so that
    # the _() functions in logic layer can work
    from paste.registry import Registry
    from pylons import translator
    from ckan.lib.cli import MockTranslator
    global registry
    registry=Registry()
    registry.prepare()
    global translator_obj
    translator_obj=MockTranslator()
    registry.register(translator, translator_obj)

class ArchiverError(Exception):
    pass
class ArchiverErrorBeforeDownloadStarted(ArchiverError):
    pass
class DownloadException(ArchiverError):
    pass
class ArchiverErrorAfterDownloadStarted(ArchiverError):
    def __init__(self, msg, url_redirected_to=None):
        super(ArchiverError, self).__init__(msg)
        self.url_redirected_to=url_redirected_to
class DownloadError(ArchiverErrorAfterDownloadStarted):
    pass
class ArchiveError(ArchiverErrorAfterDownloadStarted):
    pass
class ChooseNotToDownload(ArchiverErrorAfterDownloadStarted):
    pass
class LinkCheckerError(ArchiverError):
    pass
class LinkInvalidError(LinkCheckerError):
    pass
class LinkHeadRequestError(LinkCheckerError):
    pass
class LinkHeadMethodNotSupported(LinkCheckerError):
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
             max_content_length=settings.MAX_CONTENT_LENGTH,
             method='GET'):
    '''Given a resource, tries to download it.

    Params:
      resource - dict of the resource

    Exceptions from tidy_url may be propagated:
       LinkInvalidError if the URL is invalid

    If there is an error performing the download, raises:
       DownloadException - connection problems etc.
       DownloadError - HTTP status code is an error or 0 length

    If download is not suitable (e.g. too large), raises:
       ChooseNotToDownload

    If the basic GET fails then it will try it with common API
    parameters (SPARQL, WMS etc) to get a better response.

    Returns a dict of results of a successful download:
      length, hash, headers, saved_file, url_redirected_to
    Updates the resource values for: mimetype, size, hash
    '''

    log = update.get_logger()

    url = resource['url']

    url = tidy_url(url)

    if (resource.get('resource_type') == 'file.upload' and
        not url.startswith('http')):
        url = context['site_url'].rstrip('/') + url

    # start the download - just get the headers
    # May raise DownloadException
    method_func = {'GET': requests.get, 'POST': requests.post}[method]
    res = convert_requests_exceptions(method_func, url, timeout=url_timeout)
    url_redirected_to = res.url if url != res.url else None
    if not res.ok: # i.e. 404 or something
        raise DownloadError('Server reported status error: %s %s' % \
                            (res.status_code, res.reason),
                            url_redirected_to)
    log.info('GET succeeded. Content headers: %r', res.headers)

    # record headers
    content_type = _clean_content_type(res.headers.get('content-type', '').lower())
    content_length = res.headers.get('content-length')
    resource_changed = False
    if resource.get('mimetype') != content_type:
        resource_changed = True
        resource['mimetype'] = content_type

    # this is to store the size in case there is an error, but the real size check
    # is done after downloading the data file, with its real length
    if content_length is not None and (resource.get('size') != content_length):
        resource_changed = True
        resource['size'] = content_length

    # make sure resource content-length does not exceed our maximum
    if content_length:
        try:
            content_length = int(content_length)
        except ValueError:
            # if there are multiple Content-Length headers, requests
            # will return all the values, comma separated
            if ',' in content_length:
                try:
                    content_length = int(content_length.split(',')[0])
                except ValueError:
                    pass
    if isinstance(content_length, int) and \
       int(content_length) >= max_content_length:
            if resource_changed:
                _update_resource(context, resource, log)
            # record fact that resource is too large to archive
            log.warning('Resource too large to download: %s > max (%s). Resource: %s %r',
                     content_length, max_content_length, resource['id'], url)
            raise ChooseNotToDownload("Content-length %s exceeds maximum allowed value %s" %
                                      (content_length, max_content_length),
                                      url_redirected_to)

    # continue the download - the response body
    def get_content():
        return res.content
    content = convert_requests_exceptions(get_content)

    if response_is_an_api_error(content):
        raise DownloadError('Server content contained an API error message: %s' % \
                            content[:250],
                            url_redirected_to)

    if len(content) > max_content_length:
        raise ChooseNotToDownload("Content-length %s exceeds maximum allowed value %s" %
                                  (content_length, max_content_length),
                                  url_redirected_to)

    try:
        length, hash, saved_file_path = _save_resource(resource, res, max_content_length)
    except ChooseNotToDownload, e:
        raise ChooseNotToDownload(str(e), url_redirected_to)
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
                                  max_content_length,
                                  url_redirected_to)

    # zero length (or just one byte) indicates a problem too
    if length < 2:
        if resource_changed:
            _update_resource(context, resource, log)
        # record fact that resource is zero length
        log.warning('Resource found was length %i - not archiving. Resource: %s %r',
                 length, resource['id'], url)
        raise DownloadError("Content-length after streaming was %i" % length,
                            url_redirected_to)

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
            'hash': hash,
            'headers': res.headers,
            'saved_file': saved_file_path,
            'url_redirected_to': url_redirected_to,
            'request_type': method}


@celery.task(name="archiver.clean")
def clean():
    """
    Remove all archived resources.
    """
    log = clean.get_logger()
    log.error("clean task not implemented yet")

@celery.task(name="archiver.update")
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
        if os.environ.get('DEBUG'):
            raise
        # Any problem at all is recorded in task_status and then reraised
        log.error('Error occurred during archiving resource: %s\nResource: %r',
                  e, data)
        raise

def _update(context, resource):
    """
    Link check and archive the given resource.
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
    def _save_status(has_passed, status_txt, exception, status, resource_id, url_redirected_to=None):
        assert status_txt in LINK_STATUSES__ALL, status_txt
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
                    reason, url_redirected_to,
                    last_success, first_failure,
                    failure_count, log)

    log.info("Attempting to download resource: %s" % resource['url'])
    result = None
    download_error = 0
    try:
        result = download(context, resource)
    except LinkInvalidError, e:
        download_error = 'URL invalid'
        try_as_api = False
    except DownloadException, e:
        download_error = 'Download error'
        try_as_api = True
    except DownloadError, e:
        download_error = 'Download error'
        try_as_api = True
    except ChooseNotToDownload, e:
        download_error = 'Chose not to download'
        try_as_api = False
    except Exception, e:
        if os.environ.get('DEBUG'):
            raise
        log.error('Uncaught download failure: %r, %r', e, e.args)
        _save_status(False, 'Download failure', e, status, resource['id'])
        return

    if download_error:
        log.info('GET error: %s - %r, %r "%s"', download_error, e, e.args, resource.get('url'))
        # api_request DISABLED temporarily while fixed
        #if try_as_api:
        #    result = api_request(context, resource)
        #    download_error = not result

        if not try_as_api or download_error:
            extra_args = [e.url_redirected_to] if 'url_redirected_to' in e else []
            _save_status(False, download_error, e, status, resource['id'],
                         *extra_args)
            return

    log.info('Attempting to archive resource')
    try:
        file_path = archive_resource(context, resource, log, result)
    except ArchiveError, e:
        log.error('System error during archival: %r, %r', e, e.args)
        _save_status(False, 'System error during archival', e, status, resource['id'], result['url_redirected_to'])
        return

    # Success
    _save_status(True, 'Archived successfully', '', status, resource['id'],
                 result['url_redirected_to'])
    return json.dumps({
        'resource': resource,
        'file_path': file_path
    })


@celery.task(name="archiver.link_checker")
def link_checker(context, data):
    """
    Check that the resource's url is valid, and accepts a HEAD request.

    Redirects are not followed - they simple return 'location' in the headers.

    data is a JSON dict describing the link:
        { 'url': url,
          'url_timeout': url_timeout }

    Raises LinkInvalidError if the URL is invalid
    Raises LinkHeadRequestError if HEAD request fails
    Raises LinkHeadMethodNotSupported if server says HEAD is not supported

    Returns a json dict of the headers of the request
    """
    log = update.get_logger()
    data = json.loads(data)
    url_timeout = data.get('url_timeout', 30)

    error_message = ''
    headers = {'User-Agent': USER_AGENT}

    url = tidy_url(data['url'])

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
        if res.status_code == 405:
            # this suggests a GET request may be ok, so proceed to that
            # in the download
            raise LinkHeadMethodNotSupported()
        if not res.ok or res.status_code >= 400:
            error_message = 'Server returned HTTP error status: %s %s' % \
                (res.status_code, res.reason)
            raise LinkHeadRequestError(error_message)
    return json.dumps(headers)

def tidy_url(url):
    '''
    Given a URL it does various checks before returning a tidied version
    suitable for calling.

    It may raise LinkInvalidError if the URL has a problem.
    '''

    # Find out if it has unicode characters, and if it does, quote them
    # so we are left with an ascii string
    try:
        url = url.decode('ascii')
    except:
        parts = list(urlparse.urlparse(url))
        parts[2] = urllib.quote(parts[2].encode('utf-8'))
        parts[1] = urllib.quote(parts[1].encode('utf-8'))
        url = urlparse.urlunparse(parts)
    url = str(url)

    # strip whitespace from url
    # (browsers appear to do this)
    url = url.strip()

    # Use urllib3 to parse the url ahead of time, since that is what
    # requests uses, but when it does it during a GET, errors are not
    # caught well
    try:
        parsed_url = urllib3.util.parse_url(url)
    except urllib3.exceptions.LocationParseError, e:
        raise LinkInvalidError('URL parsing failure: %s' % e)

    # Check we aren't using any schemes we shouldn't be
    if not parsed_url.scheme in ALLOWED_SCHEMES:
        raise LinkInvalidError('Invalid url scheme. Please use one of: %s' % \
                               ' '.join(ALLOWED_SCHEMES))

    if not parsed_url.host:
        raise LinkInvalidError('URL parsing failure - did not find a host name')

    return url

def archive_resource(context, resource, log, result=None, url_timeout=30):
    """
    Archive the given resource. Moves the file from the temporary location
    given in download() and updates the resource with the link to it.

    Params:
       result - result of the download(), containing keys: length, saved_file

    If there is a failure, raises ArchiveError.

    Updates resource keys: cache_url, cache_last_updated, cache_filepath
    Returns: cache_filepath
    """
    if result['length']:
        relative_archive_path = os.path.join(resource['id'][:2], resource['id'])
        archive_dir = os.path.join(settings.ARCHIVE_DIR, relative_archive_path)
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        # try to get a file name from the url
        parsed_url = urlparse.urlparse(resource.get('url'))
        try:
            file_name = parsed_url.path.split('/')[-1] or 'resource'
            file_name = file_name.strip() # trailing spaces cause problems
        except:
            file_name = "resource"
        saved_file = os.path.join(archive_dir, file_name)
        shutil.move(result['saved_file'], saved_file)
        log.info('Going to do chmod: %s', saved_file)
        try:
            os.chmod(saved_file, 0644) # allow other users to read it
        except Exception, e:
            log.error('chmod failed %s: %s', saved_file, e)
            raise
        log.info('Archived resource as: %s', saved_file)
        previous_cache_filepath = resource.get('cache_filepath')
        resource['cache_filepath'] = saved_file

        # update the resource object: set cache_url and cache_last_updated
        if context.get('cache_url_root'):
            cache_url = urlparse.urljoin(
                context['cache_url_root'], '%s/%s' % (relative_archive_path, file_name)
            )
            if resource.get('cache_url') != cache_url:
                resource['cache_url'] = cache_url
                resource['cache_last_updated'] = datetime.datetime.now().isoformat()
                log.info('Updating resource with cache_url=%s', cache_url)
                _update_resource(context, resource, log)
            elif resource.get('cache_filepath') != previous_cache_filepath:
                log.info('Updating just cache_filepath for resource with cache_url=%s', cache_url)
                _update_resource(context, resource, log)
            else:
                log.info('Not updating resource since cache_url is unchanged: %s',
                          cache_url)
        else:
            log.warning('Not saved cache_url because no value for cache_url_root in config')
            raise ArchiveError('No value for cache_url_root in config')

        return saved_file


def _save_resource(resource, response, max_file_size, chunk_size=1024*16):
    """
    Write the response content to disk.

    Returns a tuple:

        (file length: int, content hash: string, saved file path: string)
    """
    resource_hash = hashlib.sha1()
    length = 0

    #tmp_resource_file = os.path.join(settings.ARCHIVE_DIR, 'archive_%s' % os.getpid())
    fd, tmp_resource_file_path = tempfile.mkstemp()

    with open(tmp_resource_file_path, 'wb') as fp:
        for chunk in response.iter_content(chunk_size=chunk_size, decode_unicode=False):
            fp.write(chunk)
            length += len(chunk)
            resource_hash.update(chunk)

            if length >= max_file_size:
                raise ChooseNotToDownload(
                    "Content length %s exceeds maximum allowed value %s" %
                    (length, max_file_size))

    os.close(fd)

    content_hash = unicode(resource_hash.hexdigest())
    return length, content_hash, tmp_resource_file_path


def _update_resource(context, resource, log):
    """
    Use CKAN API to update the given resource.
    If cannot update, records this fact in the task_status table.

    Params:
      context - dict containing 'site_user_apikey' and 'site_url'
      resource - dict of the resource containing

    Returns the content of the response.

    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/resource_update'
    resource['last_modified'] = datetime.datetime.now().isoformat()
    post_data = json.dumps(resource)
    res = requests.post(
        api_url, post_data,
        headers={'Authorization': context['site_user_apikey'],
                 'Content-Type': 'application/json',
                 'User-Agent': USER_AGENT}
    )

    if res.status_code == 200:
        log.info('Resource updated OK: %s', resource['id'])
        return res.content
    else:
        try:
            content = res.content
        except:
            content = '<could not read request content to discover error>'
        log.error('ckan failed to update resource, status_code (%s), error %s. Maybe the API key or site URL are wrong?.\ncontext: %r\nresource: %r\nres: %r\npost_data: %r\napi_url: %r'
                        % (res.status_code, content, context, resource, res, post_data, api_url))
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
    global CONFIG_LOADED
    if not CONFIG_LOADED:
        load_config()
        register_translator()

    import ckan.model as model
    from ckanext.archiver.model import ArchiveTask

    old = ArchiveTask.get_for_resource(data.get('entity_id'))
    if old:
        model.Session.delete(old)
    a = ArchiveTask.create(data)
    model.Session.add(a)
    model.Session.commit()

    log.info('Task status updated ok: %r', data)


def get_status(context, resource_id, log):
    '''Returns a dict of the current archiver 'status'.
    (task status value where key='status')

    Result is dict with keys: value, reason, last_success, first_failure,
    failure_count, last_updated

    May propagate CkanError if the request fails.

    :param context: Dict including: site_url, site_user_apikey
    '''

    global CONFIG_LOADED
    if not CONFIG_LOADED:
        load_config()
        register_translator()

    import ckan.model as model
    from ckanext.archiver.model import ArchiveTask

    a = ArchiveTask.get_for_resource(resource_id)
    if a:
        status = {}
        status['last_updated'] = a.created
        status['value'] = a.response
        status['reason'] = a.reason
        status['last_updated'] = a.created.isoformat() if a.created else ''
        status['first_failure'] = a.first_failure.isoformat() if a.first_failure else ''
        status['failure_count'] = a.failure_count
        status['last_success'] = a.last_success.isoformat() if a.last_success else ''
        log.info('Archiver status (currently stored value): %s', status)
    else:
        status = {'value': '', 'reason': '',
                  'last_success': '', 'first_failure': '', 'failure_count': 0,
                  'last_updated': ''}
        log.info('Archiver status blank - using default: %s', status)
    return status

def save_status(context, resource_id, status, reason, url_redirected_to,
                last_success, first_failure, failure_count, log):
    '''Writes to the task status table the result of an attempt to download
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
                'url_redirected_to': url_redirected_to,
                }),
            'last_updated': now
        }

    update_task_status(context, data, log)
    log.info('Saved status: %r reason=%r last_success=%r first_failure=%r failure_count=%r',
             status, reason, last_success, first_failure, failure_count)

def convert_requests_exceptions(func, *args, **kwargs):
    '''
    Run a requests command, catching exceptions and reraising them as
    DownloadException. Status errors, such as 404 or 500 do not cause
    exceptions, instead exposed as not response.ok.
    e.g.
    >>> convert_requests_exceptions(requests.get, url, timeout=url_timeout)
    runs:
        res = requests.get(url, timeout=url_timeout)
    '''
    try:
        response = func(*args, **kwargs)
    except requests.exceptions.ConnectionError, e:
        raise DownloadException('Connection error: %s' % e)
    except requests.exceptions.HTTPError, e:
        raise DownloadException('Invalid HTTP response: %s' % e)
    except requests.exceptions.Timeout, e:
        raise DownloadException('Connection timed out after %ss' % kwargs.get('timeout', '?'))
    except requests.exceptions.TooManyRedirects, e:
        raise DownloadException('Too many redirects')
    except requests.exceptions.RequestException, e:
        raise DownloadException('Error downloading: %s' % e)
    except Exception, e:
        if os.environ.get('DEBUG'):
            raise
        raise DownloadException('Error with the download: %s' % e)
    return response

def ogc_request(context, resource, service, wms_version):
    original_url = url = resource['url']
    # Remove parameters
    url = url.split('?')[0]
    # Add WMS GetCapabilities parameters
    url += '?service=%s&request=GetCapabilities&version=%s' % (service, wms_version)
    resource['url'] = url
    # Make the request
    response = download(context, resource)
    # Restore the URL so that it doesn't get saved in the actual resource
    resource['url'] = original_url
    return response

def wms_1_3_request(context, resource):
    res = ogc_request(context, resource, 'WMS', '1.3')
    res['request_type'] = 'WMS 1.3'
    return res

def wms_1_1_1_request(context, resource):
    res = ogc_request(context, resource, 'WMS', '1.1.1')
    res['request_type'] = 'WMS 1.1.1'
    return res

def wfs_request(context, resource):
    res = ogc_request(context, resource, 'WFS', '2.0')
    res['request_type'] = 'WFS 2.0'
    return res

def api_request(context, resource):
    '''
    Tries making requests as if the resource is a well-known sort of API to try
    and get a valid response. If it does it returns the response, otherwise Archives the response and stores what sort of
    request elicited it.
    '''
    log = update.get_logger()
    # 'resource' holds the results of the download and will get saved. Only if
    # an API request is successful do we want to save the details of it.
    # However download() gets altered for these API requests. So only give
    # download() a copy of 'resource'.
    for api_request_func in wms_1_3_request, wms_1_1_1_request, wfs_request:
        resource_copy = copy.deepcopy(resource)
        try:
            download_dict = api_request_func(context, resource_copy)
        except ArchiverError, e:
            log.info('API %s error: %r, %r "%s"', api_request_func,
                     e, e.args, resource.get('url'))
            continue
        except Exception, e:
            if os.environ.get('DEBUG'):
                raise
            log.error('Uncaught API %s failure: %r, %r', api_request_func,
                      e, e.args)
            continue

        return download_dict

def response_is_an_api_error(response_body):
    '''Some APIs return errors as the response body, but HTTP status 200. So we
    need to check response bodies for these error messages.
    '''
    response_sample = response_body[:250]  # to allow for <?xml> and <!DOCTYPE> lines

    # WMS spec
    # e.g. https://map.bgs.ac.uk/ArcGIS/services/BGS_Detailed_Geology/MapServer/WMSServer?service=abc
    # <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    # <ServiceExceptionReport version="1.3.0"
    if '<ServiceExceptionReport' in response_sample:
        return True

    # This appears to be an alternative - I can't find the spec.
    # e.g. http://sedsh13.sedsh.gov.uk/ArcGIS/services/HS/Historic_Scotland/MapServer/WFSServer?service=abc
    # <ows:ExceptionReport version='1.1.0' language='en' xmlns:ows='http://www.opengis.net/ows'><ows:Exception exceptionCode='NoApplicableCode'><ows:ExceptionText>Wrong service type.</ows:ExceptionText></ows:Exception></ows:ExceptionReport>
    if '<ows:ExceptionReport' in response_sample:
        return True

