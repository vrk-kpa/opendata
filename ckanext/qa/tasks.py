'''
Score datasets on Sir Tim Berners-Lee\'s five stars of openness
based on mime-type.
'''
import datetime
import json
import requests
import urlparse
import ckan.lib.celery_app as celery_app
from ckanext.archiver.tasks import link_checker, LinkCheckerError


class QAError(Exception):
    pass


class CkanError(Exception):
    pass

# Description of each score, used elsewhere
OPENNESS_SCORE_REASON = {
    0: 'Not obtainable',
    1: 'Obtainable via web page',
    2: 'Machine readable format',
    3: 'Open and standardized format',
    4: 'Ontologically represented',
    5: 'Fully Linked Open Data as appropriate',
}

# mime types, file extensions and what you'd put in the 'format' field
# along with their score
MIME_TYPE_SCORE = {
    'text/plain': 1,
    'text': 1,
    'txt': 1,
    'text/html': 1,
    'application/pdf': 1,
    'pdf': 1,
    'zip': 1,
    'application/x-compressed': 1,
    'application/x-zip-compressed': 1,
    'application/zip': 1,
    'multipart/x-zip': 1,
    'word': 1,
    'doc': 1,
    'docx': 1,
    'application/msword': 1,
    'ppt': 1,
    'pptx': 1,
    'application/mspowerpoint': 1,
    'application/powerpoint': 1,
    'application/vnd.ms-powerpoint': 1,
    'application/x-mspowerpoint': 1,
    'application/excel': 2,
    'application/x-excel': 2,
    'application/x-msexcel': 2,
    'application/vnd.ms-excel': 2,
    'application/vnd.ms-excel.sheet.binary.macroenabled.12': 2,
    'application/vnd.ms-excel.sheet.macroenabled.12': 2,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 2,
    'xls': 2,
    'xlsx': 2,
    'excel': 2,
    'shp': 2,
    'text/csv': 3,
    'application/json': 3,
    'text/x-json': 3,
    'application/xml': 3,
    'text/xml': 3,
    'rss': 3,
    'text/rss+xml': 3,
    'csv': 3,
    'csv / zip': 3,
    'csv.zip': 3,
    'ods': 3,
    'application/vnd.oasis.opendocument.spreadsheet': 3,
    'xml': 3,
    'json': 3,
    'wms': 3,
    'kml': 3,
    'application/vnd.google-earth.kml+xml': 3,
    'netcdf': 3,
    'cdf': 3,
    'application/netcdf': 3,
    'application/rdf+xml': 4,
    'rdf': 4,
}

# These content-types are ambiguous, so don't infer what
# type the file is.
GENERAL_PURPOSE_CONTENT_TYPES = set(('application/octet-stream',))

def _update_task_status(context, data, log):
    """
    Use CKAN API to update the task status. The data parameter
    should be a dict representing one row in the task_status table.

    Returns the content of the response.
    """
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/task_status_update'
    res = requests.post(
        api_url, json.dumps(data),
        headers={'Authorization': context['apikey'],
                 'Content-Type': 'application/json'}
    )
    if res.status_code == 200:
        return res.content
    else:
        try:
            content = res.content
        except:
            content = '<could not read request content to discover error>'
        log.error('ckan failed to update task_status, status_code (%s), error %s. Maybe the API key or site URL are wrong?.\ncontext: %r\ndata: %r\nres: %r\nres.error: %r\napi_url: %r'
                        % (res.status_code, content, context, data, res, res.error, api_url))
        raise CkanError('ckan failed to update task_status, status_code (%s), error %s'
                        % (res.status_code, content))
    log.info('Task status updated ok')


def _task_status_data(id, result):
    now = datetime.datetime.now().isoformat()
    data = [
        {
            'entity_id': id,
            'entity_type': u'resource',
            'task_type': 'qa',
            'key': u'openness_score',
            'value': result['openness_score'],
            'last_updated': now
        },
        {
            'entity_id': id,
            'entity_type': u'resource',
            'task_type': 'qa',
            'key': u'openness_score_reason',
            'value': result['openness_score_reason'],
            'last_updated': now
        },
        {
            'entity_id': id,
            'entity_type': u'resource',
            'task_type': 'qa',
            'key': u'openness_score_failure_count',
            'value': result['openness_score_failure_count'],
            'last_updated': now
        },
    ]
    if 'openness_score_last_success' in result:
        data.append(
        {
            'entity_id': id,
            'entity_type': u'resource',
            'task_type': 'qa',
            'key': u'openness_score_last_success',
            'value': result['openness_score_last_success'],
            'last_updated': now
        })
    return data
        
@celery_app.celery.task(name="qa.update")
def update(context, data):
    """
    Given a resource, calculates an openness score.

    context - how this plugin can call the CKAN API with the results
              is JSON dict with keys: 'site_url', 'apikey'
    data - details of the resource that is to be scored
           is JSON dict with keys: 'package', 'position', 'id', 'format', 'url', 'is_open'
    
    Returns a JSON dict with keys:

        'openness_score': score (int)
        'openness_score_reason': the reason for the score (string)
        'openness_score_failure_count': the number of consecutive times that
                                        this resource has returned a score of 0
    """
    log = update.get_logger()
    try:
        data = json.loads(data)
        context = json.loads(context)

        result = resource_score(context, data, log)
        log.info('Openness scoring: \n%r\n%r\n%r\n\n', result, data, context)
        
        task_status_data = _task_status_data(data['id'], result)

        api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/task_status_update_many'
        response = requests.post(
            api_url,
            json.dumps({'data': task_status_data}),
            headers={'Authorization': context['apikey'],
                     'Content-Type': 'application/json'}
        )
        if not response.ok:
            err = 'ckan failed to update task_status, error %s\nurl=%r' \
                  % (response.error, api_url)
            log.error(err)
            raise CkanError(err)
        elif response.status_code != 200:
            err = 'ckan failed to update task_status, status_code (%s), error %s\nurl=%s' \
                  % (response.status_code, response.content, api_url)
            log.error(err)
            raise CkanError(err)
        log.info('CKAN updated with openness score')
        return json.dumps(result)
    except Exception, e:
        log.error('Exception occurred during QA update: %s: %s', e.__class__.__name__,  unicode(e))
        _update_task_status(context, {
            'entity_id': data['id'],
            'entity_type': u'resource',
            'task_type': 'qa',
            'key': u'celery_task_id',
            'value': unicode(update.request.id),
            'error': '%s: %s' % (e.__class__.__name__,  unicode(e)),
            'last_updated': datetime.datetime.now().isoformat()
        }, log)
        raise

def get_existing_openness_info(key, context, data, log):
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/task_status_show'
    response = requests.post(
        api_url,
        json.dumps({'entity_id': data['id'], 'task_type': 'qa',
                    'key': key}),
        headers={'Authorization': context['apikey'],
                 'Content-Type': 'application/json'}
    )
    if response.status_code == 404 and json.loads(response.content)['success'] == False:
        log.info('Could not get %s - must be a new resource.' % key)
        value = 0
    elif response.error:
        log.error('Error getting %s. Error=%r\napi_url=%r\ncode=%r\ncontent=%r',
                  key, response.error, api_url, response.status_code, response.content)
        raise QAError('Error getting %s' % key)
    elif json.loads(response.content)['success']:
        result = json.loads(response.content)['result'].get('value', '0')
        try:
            value = int(result)
        except ValueError, e:
            log.warning('Non integer value for %s: %r', key, result)
            value = 0
    else:
        log.error('Error getting %s. Status=%r Error=%r\napi_url=%r',
                  key, response.status_code, response.content, api_url)
        raise QAError('Error getting %s' % key)
    return value

def resource_score(context, data, log):
    """
    Score resources on Sir Tim Berners-Lee\'s five stars of openness
    based on mime-type.

    returns a dict with keys:

        'openness_score': score (int)
        'openness_score_reason': the reason for the score (string)
        'openness_score_failure_count': the number of consecutive times that
                                        this resource has returned a score of 0
        
    """
    score = 0
    score_reason = ''

    # get info about previous scorings from the task status table if they exist
    score_failure_count = get_existing_openness_info('openness_score_failure_count',
                                                     context, data, log)

    try:
        headers = json.loads(link_checker("{}", json.dumps(data)))
        score_reason = 'Request succeeded.'
        ct = headers.get('content-type')

        # ignore charset if exists (just take everything before the ';')
        if ct and ';' in ct:
            ct = ct.split(';')[0]

        # also get format from resource and by guessing from file extension
        extension = None
        for try_extension in extension_variants(data['url']):
            if try_extension.lower() in MIME_TYPE_SCORE:
                extension = try_extension

        # format field gives the best clue
        format = data.get('format', '').lower()

        # we don't want to take the publisher's word for it, in case the link
        # is only to a landing page, so highest priority is the content-type
        if ct and ct not in GENERAL_PURPOSE_CONTENT_TYPES:
            score = MIME_TYPE_SCORE.get(ct)
            score_reason += ' Content-Type header "%s".' % ct
        elif extension:
            score = MIME_TYPE_SCORE.get(extension)
            score_reason += ' URL extension "%s".' % extension
        elif format:
            score = MIME_TYPE_SCORE.get(format.lower())
            score_reason += ' Format field "%s".' % format

        if score == None:
            log.warning('Could not score format type: "%s"',
                     ct or extension or format)
            score_reason += ' No corresponding score is available for this format.'
            score = 0

    except LinkCheckerError, e:
        score_reason = str(e)
    except Exception, e:
        log.error('Unexpected error while calculating openness score %s: %s', e.__class__.__name__,  unicode(e))
        score_reason = "Unknown error: %s" % str(e)

    # Even if we can get the link, we should still treat the resource
    # as having a score of 0 if the license isn't open.
    #
    # It is important we do this check after the link check, otherwise
    # the link checker won't get the chance to see if the resource
    # is broken.
    if score > 1 and not data.get('is_open'):
        score_reason = 'License not open'
        score = 0

    if score == 0:
        score_failure_count += 1
    else:
        score_failure_count = 0

    result = {
        'openness_score': score,
        'openness_score_reason': score_reason,
        'openness_score_failure_count': score_failure_count,
    }

    # If success, record the date of that
    if score > 0:
        result['openness_score_last_success'] = datetime.datetime.now().isoformat()

    return result

def extension_variants(url):
    '''
    Returns a list of extensions, in order of which would more
    significant.
    
    >>> extension_variants('http://dept.gov.uk/coins.data.1996.csv.zip')
    ['csv.zip', 'zip']
    '''
    split_url = url.split('.')
    results = []
    for number_of_sections in [2, 1]:
        if len(split_url) > number_of_sections:
            results.append('.'.join(split_url[-number_of_sections]))
    return results
