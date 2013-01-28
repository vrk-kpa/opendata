'''
Score datasets on Sir Tim Berners-Lee\'s five stars of openness
based on mime-type.
'''
import datetime
import json
import requests
import urlparse
import os
import re

from pylons import config

import ckan.lib.celery_app as celery_app
from ckanext.dgu.lib.formats import Formats, VAGUE_MIME_TYPES
from ckanext.qa.sniff_format import sniff_file_format
from ckanext.archiver.tasks import get_status as get_archiver_status, ArchiverError
from ckanext.archiver.lib import get_cached_resource_filepath

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
    should be a dict representing one row in the task_status table, or a list
    of such dicts.

    Returns the content of the response.
    """
    if isinstance(data, list):
        func = '/task_status_update_many'
        payload = {'data': data}
    elif isinstance(data, dict):
        func = '/task_status_update'
        payload = data
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + func
    res = requests.post(
        api_url, json.dumps(payload),
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
    ]
    return data

@celery_app.celery.task(name="qa.package")
def update_package(context, data):
    """
    Given a package, calculates an openness score for each of its resources.
    It is more efficient to call this than 'update' for each resource.

    context - how this plugin can call the CKAN API to get more info and
              save the results.
              is a JSON dict with keys: 'site_url', 'apikey'
    data - package dict (includes its resources)

    Returns None
    """
    log = update_package.get_logger()
    try:
        package = json.loads(data)
        context = json.loads(context)

        log.info('Openness scoring package %s (%i resources)', package['name'], len(package['resources']))
        for resource in package['resources']:
            resource['is_open'] = package['isopen']
            resource['package'] = package['name']
            result = resource_score(context, resource, log)
            log.info('Openness scoring: \n%r\n%r\n%r\n\n', result, resource, context)
            _update_task_status(context, _task_status_data(resource['id'], result), log)
            log.info('CKAN updated with openness score')
        update_search_index(context, package['id'], log)
    except Exception, e:
        log.error('Exception occurred during QA update: %s: %s', e.__class__.__name__,  unicode(e))
        _update_task_status(context, {
            'entity_id': package['id'],
            'entity_type': u'resource',
            'task_type': 'qa',
            'key': u'celery_task_id',
            'value': unicode(update.request.id),
            'error': '%s: %s' % (e.__class__.__name__,  unicode(e)),
            'last_updated': datetime.datetime.now().isoformat()
        }, log)
        raise

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
    """
    log = update.get_logger()
    try:
        resource = json.loads(data)
        context = json.loads(context)

        result = resource_score(context, resource, log)
        log.info('Openness scoring: \n%r\n%r\n%r\n\n', result, resource, context)
        _update_task_status(context, _task_status_data(resource['id'], result), log)
        log.info('CKAN updated with openness score')
        package = resource.get('package')
        if package:
            update_search_index(context, resource['package'], log)
        else:
            log.warning('Resource not connected to a package. Res: %r', resource)
        return json.dumps(result)
    except Exception, e:
        log.error('Exception occurred during QA update: %s: %s', e.__class__.__name__,  unicode(e))
        _update_task_status(context, {
            'entity_id': resource['id'],
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

    """
    score = 0
    score_reason = ''

    try:
        score_reasons = [] # a list of strings detailing how we scored it

        # we don't want to take the publisher's word for it, in case the link
        # is only to a landing page, so highest priority is the sniffed type
        score = score_by_sniffing_data(context, data, score_reasons, log)
        if score == None:
            # Fall-backs are user-given data
            score = score_by_url_extension(data, score_reasons, log)
            if score == None:
                score = score_by_format_field(data, score_reasons, log)
                if score == None:
                    log.warning('Could not score resource: "%s" with url: "%s"',
                                data.get('id'), data.get('url'))
                    score_reasons.append('Could not understand the file format, therefore score is 1.')
                    score = 1
        score_reason = ' '.join(score_reasons)
    except Exception, e:
        log.error('Unexpected error while calculating openness score %s: %s', e.__class__.__name__,  unicode(e))
        score_reason = "Unknown error: %s" % str(e)
        if os.environ.get('DEBUG'):
            raise

    # Even if we can get the link, we should still treat the resource
    # as having a score of 0 if the license isn't open.
    #
    # It is important we do this check after the link check, otherwise
    # the link checker won't get the chance to see if the resource
    # is broken.
    if score > 0 and not data.get('is_open'):
        score_reason = 'License not open'
        score = 0

    log.info('Score: %s Reason: %s', score, score_reason)

    result = {
        'openness_score': score,
        'openness_score_reason': score_reason,
    }

    return result

def broken_link_error_message(archiver_status):
    '''Given an archiver_status for a broken link, it returns a helpful
    error message (string) describing the attempts.'''
    messages = ['File could not be downloaded.',
                'Reason: %s.' % archiver_status['value'],
                'Error details: %s.' % archiver_status['reason']]
    def format_date(iso_date):
        if iso_date:
            return datetime.datetime(*map(int, re.split('[^\d]', iso_date)[:-1])).\
                   strftime('%d/%m/%Y')
        else:
            return ''
    if 'last_updated' in archiver_status:
        # (older versions of archiver don't return this one)
        messages.append('Attempted on %s.' % format_date(archiver_status['last_updated']))
    last_success = format_date(archiver_status['last_success'])
    if archiver_status['failure_count'] in (1, '1'):
        if last_success:
            messages.append('This URL worked the previous time: %s.' % last_success)
        else:
            messages.append('This was the first attempt.')
    else:
        messages.append('Tried %s times since %s.' % \
                        (archiver_status['failure_count'],
                         format_date(archiver_status['first_failure'])))
        if last_success:
            messages.append('This URL last worked on: %s.' % last_success)
        else:
            messages.append('This URL has not worked in the history of this tool.')
    return ' '.join(messages)

def score_by_sniffing_data(context, data, score_reasons, log):
    archiver_status = get_archiver_status(context, data['id'], log)
    if archiver_status['value'] in ('URL invalid', 'URL request failed', 'Download error'):
        # Score 0 since we are sure the link is currently broken
        score_reasons.append(broken_link_error_message(archiver_status))
        return 0

    # Link is not broken so analyse the cached file
    filepath = data.get('cache_filepath')
    if filepath and not os.path.exists(filepath):
        score_reasons.append('Cache filepath does not exist: "%s".' % filepath)
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
            # No cache_url
            if archiver_status['value'] == 'Chose not to download':
                score_reasons.append('File was not downloaded deliberately. Reason: %s. Using other methods to determine file openness.' % \
                                     archiver_status['reason'])
                return None
            elif archiver_status['value'] in ('Download failure', 'System error during archival'):
                score_reasons.append('A system error occurred during downloading this file. Reason: %s. Using other methods to determine file openness.' % \
                                     archiver_status['reason'])
                return None
            elif archiver_status['value']:
                score_reasons.append('Downloading this file failed. A system error occurred determining the reason for the error: %s Using other methods to determine file openness.' % \
                                     archiver_status['value'])
                return None
            else:
                score_reasons.append('This file had not been downloaded at the time of scoring it.')
                return None
                
    
def score_by_url_extension(data, score_reasons, log):
    formats_by_extension = Formats.by_extension()
    extension_variants_ = extension_variants(data['url'].strip())
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
              Formats.by_extension().get(format_field.lower()) or \
              Formats.by_reduced_name().get(Formats.reduce(format_field))
    if not format_:
        score_reasons.append('Format field "%s" does not correspond to a known format.' % format_field)
        return None
    score = format_['openness']
    score_reasons.append('Format field "%s" receives score: %s.' % \
                         (format_field, score))
    return score

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

def update_search_index(context, package_id, log):
    '''
    Tells CKAN to update its search index for a given package dict.
    '''
    api_url = urlparse.urljoin(context['site_url'], 'api/action') + '/search_index_update'
    data = {'id': package_id}
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
        log.error('ckan failed to update search index, status_code (%s), error %s. Maybe the API key or site URL are wrong?.\ncontext: %r\ndata: %r\nres: %r\nres.error: %r\napi_url: %r'
                        % (res.status_code, content, context, data, res, res.error, api_url))
        raise CkanError('ckan failed to update search index, status_code (%s), error %s'
                        % (res.status_code, content))
    log.info('Task status updated ok')
