'''
Score datasets on Sir Tim Berners-Lee\'s five stars of openness
based on mime-type.
'''
import datetime
import json
import requests
import urlparse
import os

from pylons import config

import ckan.lib.celery_app as celery_app
from ckanext.dgu.lib.formats import Formats, VAGUE_MIME_TYPES
from ckanext.qa.sniff_format import sniff_file_format

class QAError(Exception):
    pass

class QAOperationError(Exception):
    pass

class CkanError(Exception):
    pass

# Description of each score, used elsewhere
OPENNESS_SCORE_REASON = {
    0: 'Not obtainable or license is not open',
    1: 'Obtainable via web page',
    2: 'Machine readable format',
    3: 'Open and standardized format',
    4: 'Ontologically represented',
    5: 'Fully Linked Open Data as appropriate',
}

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

    context - how this plugin can call the CKAN API to get more info and
              save the results.
              is a JSON dict with keys: 'site_url', 'apikey'
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

def get_task_status_value(key, default, context, data, log):
    '''Gets a value from the task_status table. If the key isn\'t there,
    it returns the "default" value.'''
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
        return default
    elif response.error:
        log.error('Error getting %s. Error=%r\napi_url=%r\ncode=%r\ncontent=%r',
                  key, response.error, api_url, response.status_code, response.content)
        raise QAError('Error getting %s' % key)
    elif json.loads(response.content)['success']:
        return json.loads(response.content)['result'].get('value')
    else:
        log.error('Error getting %s. Status=%r Error=%r\napi_url=%r',
                  key, response.status_code, response.content, api_url)
        raise QAError('Error getting %s' % key)
    return value

def resource_score(context, data, log):
    """
    Score resource on Sir Tim Berners-Lee\'s five stars of openness.

    context - how this plugin can call the CKAN API to get more info and
              save the results.
              is a JSON dict with keys: 'site_url', 'apikey'
    data - details of the resource that is to be scored
           is JSON dict with keys: 'package', 'position', 'id', 'format', 'url', 'is_open'

    Returns a dict with keys:

        'openness_score': score (int)
        'openness_score_reason': the reason for the score (string)
        'openness_score_failure_count': the number of consecutive times that
                                        this resource has returned a score of 0
        
    """
    score = 0
    score_reason = ''

    # get info about previous scorings from the task status table if they exist
    # = get_task_status_value('openness_score_failure_count',
    #                         context, data, log) or '0'
    score_failure_count = get_task_status_value('openness_score_failure_count',
                                                '0', context, data, log) or '0'
    try:
        score_failure_count = int(score_failure_count)
    except ValueError, e:
        log.warning('Non integer value for score_failure_count: %r',
                    score_failure_count)
        score_failure_count = 0

    try:
        score_reasons = [] # a list of strings detailing how we scored it
        
        # we don't want to take the publisher's word for it, in case the link
        # is only to a landing page, so highest priority is the sniffed type
        score = score_by_sniffing_data(data, score_reasons, log)
        if score == None:
            # Fall-backs are user-given data
            score = score_by_url_extension(data, score_reasons, log)
            if score == None:
                score = score_by_format_field(data, score_reasons, log)
                if score == None:
                    log.warning('Could not score resource: "%s" with url: "%s"',
                                data.get('id'), data.get('url'))
                    score_reasons.append('No openness can be determined, therefore score is 0.')
                    score = 0
        score_reason = ' '.join(score_reasons)
    except Exception, e:
        log.error('Unexpected error while calculating openness score %s: %s', e.__class__.__name__,  unicode(e))
        score_reason = "Unknown error: %s" % str(e)
        #raise #JUST FOR TEST

    log.info('Score: %s Reason: %s', score, score_reason)

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

def score_by_sniffing_data(data, score_reasons, log):
    try:
        filepath = get_cached_resource_filepath(data)
    except QAOperationError, e:
        log.error(e)
        sniffed_format = None
        score_reasons.append('Operational error occurred when accessing cached copy of the data, so cannot determine format from the contents.')
        return None
    else:
        if filepath:
            sniffed_format = sniff_file_format(filepath, log)
            if sniffed_format:
                score_reasons.append('Content of file appeared to be format "%s" which receives openness score: %s.' % (sniffed_format['display_name'], sniffed_format['openness']))
                return sniffed_format['openness']
            else:
                score_reasons.append('The format of the file was not recognised from its contents.')
                return None
        else:
            score_reasons.append('Cached copy of the data not currently available so cannot determine format from the contents.')
            return None
    
def score_by_url_extension(data, score_reasons, log):
    formats_by_extension = Formats.by_extension()
    extension_variants_ = extension_variants(data['url'])
    if not extension_variants_:
        score_reasons.append('Could not determine a file extension in the URL.')
        return None
    for extension in extension_variants_:
        if extension.lower() in formats_by_extension:
            format_ = Formats.by_extension().get(extension.lower())
            score = format_['openness']
            score_reasons.append('URL extension "%s" relates to format "%s" and receives score: %s.' % (extension, format_['display_name'], score))
            return score
        score_reasons.append('URL extension "%s" is an unknown format.' % extension)
    return None

def score_by_format_field(data, score_reasons, log):
    format_field = data.get('format', '')
    if not format_field:
        score_reasons.append('Format field is blank.')
        return None
    format_ = Formats.by_display_name().get(format_field) or \
              Formats.by_extension().get(format_field.lower())
    if not format_:
        score_reasons.append('Format field "%s" does not correspond to a known format.')
        return None
    score = format_['openness']
    score_reasons.append('Format field "%s" receives score: %s.' % \
                         (format_field, score))
    return score
    
    
def get_cached_resource_filepath(data):
    '''Returns the filepath of the cached resource data file, calculated
    from its cache_url.

    Returns None if the resource has no cache.
    
    May raise QAOperationError for fatal errors.
    '''
    cache_url = data.get('cache_url')
    if not cache_url:
        return None
    if not cache_url.startswith(config['ckan.cache_url_root']):
        raise QAOperationError('Resource cache_url (%s) doesn\'t match the cache_url_root (%s)' % \
                      (cache_url, config['ckan.cache_url_root']))
    archive_dir = config['ckanext-archiver.archive_dir']
    if config['ckan.cache_url_root'].endswith('/') and not archive_dir.endswith('/'):
        archive_dir += '/'
    filepath = cache_url.replace(config['ckan.cache_url_root'],
                                 archive_dir)
    if not os.path.exists(filepath):
        raise QAOperationError('Local cache file does not exist: %s' % filepath)
    return filepath
    
def extension_variants(url):
    '''
    Returns a list of extensions, in order of which would more
    significant.
    
    >>> extension_variants('http://dept.gov.uk/coins.data.1996.csv.zip')
    ['csv.zip', 'zip']
    >>> extension_variants('http://dept.gov.uk/data.csv?callback=1')
    ['csv']
    '''
    url = url.split('?')[0] # get rid of params
    url = url.split('/')[-1] # get rid of path - leaves filename
    split_url = url.split('.')
    results = []
    for number_of_sections in [2, 1]:
        if len(split_url) > number_of_sections:
            results.append('.'.join(split_url[-number_of_sections:]))
    return results

