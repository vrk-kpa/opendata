'''
Score datasets on Sir Tim Berners-Lee\'s five stars of openness
'''
import datetime
import json
import requests
import urlparse
import os
import re
import traceback

import ckan.lib.celery_app as celery_app
from ckanext.dgu.lib.formats import Formats
from ckanext.qa.sniff_format import sniff_file_format
from ckanext.archiver.model import Archival, Status

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

def _update_task_status(context, data, log):
    """
    Use CKAN API to update the task status. The data parameter
    should be a dict representing one row in the task_status table, or a list
    of such dicts.

    Returns the content of the response.
    """
    global CONFIG_LOADED
    if not CONFIG_LOADED:
        load_config()
        register_translator()

    import ckan.model as model
    from ckanext.qa.model import QATask

    if isinstance(data, dict):
        q = QATask.create(data)
        model.Session.add(q)
        model.Session.commit()
    elif isinstance(data, list):
        for payload in data:
            q = QATask.create(payload)
            model.Session.add(q)
        model.Session.commit()

    log.info('Task status updated ok')


def _task_status_data(resource_id, result):
    now = datetime.datetime.now().isoformat()
    data = {
            'entity_id': resource_id,
            'entity_type': u'resource',
            'task_type': 'qa',
            'key': u'status',
            'value': result['openness_score'],
            'error': json.dumps({
                'reason': result['openness_score_reason'],
                'format': result['format'],
                'is_broken': result['is_broken'],
                'archiver_status': result['archiver_status'],
                }),
            'last_updated': now
        }
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
            log.info('Res score: %s format:%s broken:%s url:"%s"', result.get('openness_score'), result.get('format'), result.get('is_broken'), resource['url'])
            _update_task_status(context, _task_status_data(resource['id'], result), log)
            log.info('CKAN updated with openness score')
        update_search_index(context, package['id'], log)
    except Exception, e:
        log.error('Exception occurred during QA update: %s: %s', e.__class__.__name__,  unicode(e))
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
        raise

def get_qa_format(resource_id):
    global CONFIG_LOADED
    if not CONFIG_LOADED:
        load_config()
        register_translator()

    import ckan.model as model
    from ckanext.qa.model import QATask

    q = QATask.get_for_resource(resource_id)
    if not q:
        return ''
    return q.format

def resource_score(context, data, log):
    """
    Score resource on Sir Tim Berners-Lee\'s five stars of openness.

    context - how this plugin can call the CKAN API to get more info and
              save the results.
              is a dict with keys: 'site_url', 'site_user_apikey'
    data - details of the resource that is to be scored
           is JSON dict with keys: 'package', 'position', 'id', 'format', 'url', 'is_open'

    Returns a dict with keys:

        'openness_score': score (int)
        'openness_score_reason': the reason for the score (string)
        'format': format of the data (display_name string)
        'is_broken': whether the link is considered broken or not (bool)
        'archiver_status': the raw error message from the archiver (string)

    """
    score = 0
    score_reason = ''
    format_ = None
    is_broken = None

    try:
        score_reasons = [] # a list of strings detailing how we scored it
        assert set(context.keys()) >= set(('site_url', 'site_user_apikey')), \
               'Context missing keys. Has: %s' % context.keys()
        archival = Archival.get_for_resource(resource_id=data['id'])

        score, format_, is_broken = score_if_link_broken(context, archival, data, score_reasons, log)
        if score == None:
            # we don't want to take the publisher's word for it, in case the link
            # is only to a landing page, so highest priority is the sniffed type
            score, format_ = score_by_sniffing_data(context, archival, data,
                                         score_reasons, log)
            if score == None:
                # Fall-backs are user-given data
                score, format_ = score_by_url_extension(data, score_reasons, log)
                if score == None:
                    score, format_ = score_by_format_field(data, score_reasons, log)
                    if score == None:
                        log.warning('Could not score resource: "%s" with url: "%s"',
                                    data.get('id'), data.get('url'))
                        score_reasons.append('Could not understand the file format, therefore score is 1.')
                        score = 1
                        if format_ == None:
                            # use any previously stored format value for this resource
                            format_ = get_qa_format(data['id'])
        score_reason = ' '.join(score_reasons)
        format_ = format_ or None
    except Exception, e:
        log.error('Unexpected error while calculating openness score %s: %s\nException: %s', e.__class__.__name__,  unicode(e), traceback.format_exc())
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
        'format': format_,
        'is_broken': is_broken,
        'archiver_status': archival.status
    }

    return result

def broken_link_error_message(archival):
    '''Given an archival for a broken link, it returns a helpful
    error message (string) describing the attempts.'''
    def format_date(date):
        if date:
            return date.strftime('%d/%m/%Y')
        else:
            return ''
    messages = ['File could not be downloaded.',
                'Reason: %s.' % archival.status,
                'Error details: %s.' % archival.reason,
                'Attempted on %s.' % format_date(archival.last_updated)]
    last_success = format_date(archival.last_success)
    if archival.failure_count == 1:
        if last_success:
            messages.append('This URL worked the previous time: %s.' % last_success)
        else:
            messages.append('This was the first attempt.')
    else:
        messages.append('Tried %s times since %s.' % \
                        (archiver_status['failure_count'],
                         format_date(archival.first_failure)))
        if last_success:
            messages.append('This URL last worked on: %s.' % last_success)
        else:
            messages.append('This URL has not worked in the history of this tool.')
    return ' '.join(messages)

def score_if_link_broken(context, archival, data, score_reasons, log):
    '''
    Looks to see if the archiver said it was broken, and if so, writes to
    the score_reasons and returns a score.

    data - resource dict

    Return values:
      * Returns a tuple: (score, format_, is_broken)
      * score is an integer or None if it cannot be determined
      * format_ is the display_name or None
      * is_broken is a boolean
    '''
    if archival.is_broken:
        # Score 0 since we are sure the link is currently broken
        score_reasons.append(broken_link_error_message(archival))
        format_ = get_qa_format(data['id'])
        log.info('Archiver says link is broken. Previous format: %r' % format_)
        return (0, format_, True)
    return (None, None, False)

def score_by_sniffing_data(context, archival, data, score_reasons, log):
    '''
    Looks inside a data file\'s contents to determine its format and score.

    It adds strings to score_reasons list about how it came to the conclusion.

    Return values:
      * It returns a tuple: (score, format_display_name)
      * If it cannot work out the format then format_display_name is None
      * If it cannot score it, then score is None
    '''
    # Analyse the cached file
    filepath = data.get('cache_filepath')
    if filepath and not os.path.exists(filepath):
        score_reasons.append('Cache filepath does not exist: "%s".' % filepath)
        return (None, None)
    else:
        if filepath:
            sniffed_format = sniff_file_format(filepath, log)
            if sniffed_format:
                score_reasons.append('Content of file appeared to be format "%s" which receives openness score: %s.' % (sniffed_format['display_name'], sniffed_format['openness']))
                return sniffed_format['openness'], sniffed_format['display_name']
            else:
                score_reasons.append('The format of the file was not recognised from its contents.')
                return (None, None)
        else:
            # No cache_url
            if archival.status_id == Status.by_text('Chose not to download'):
                score_reasons.append('File was not downloaded deliberately. Reason: %s. Using other methods to determine file openness.' % \
                                     archival.reason)
                return (None, None)
            elif archival.is_broken is None and archival.status_id:
                # i.e. 'Download failure' or 'System error during archival'
                score_reasons.append('A system error occurred during downloading this file. Reason: %s. Using other methods to determine file openness.' % \
                                     archival.reason)
                return (None, None)
            else:
                score_reasons.append('This file had not been downloaded at the time of scoring it.')
                return (None, None)


def score_by_url_extension(data, score_reasons, log):
    '''
    Looks at the URL for a resource to determine its format and score.

    It adds strings to score_reasons list about how it came to the conclusion.

    Return values:
      * It returns a tuple: (score, format_display_name)
      * If it cannot work out the format then format_display_name is None
      * If it cannot score it, then score is None
    '''
    formats_by_extension = Formats.by_extension()
    extension_variants_ = extension_variants(data['url'].strip())
    if not extension_variants_:
        score_reasons.append('Could not determine a file extension in the URL.')
        return (None, None)
    for extension in extension_variants_:
        if extension.lower() in formats_by_extension:
            format_ = Formats.by_extension().get(extension.lower())
            score = format_['openness']
            score_reasons.append('URL extension "%s" relates to format "%s" and receives score: %s.' % (extension, format_['display_name'], score))
            return score, format_['display_name']
        score_reasons.append('URL extension "%s" is an unknown format.' % extension)
    return (None, None)

def score_by_format_field(data, score_reasons, log):
    '''
    Looks at the format field of a resource to determine its format and score.

    It adds strings to score_reasons list about how it came to the conclusion.

    Return values:
      * It returns a tuple: (score, format_display_name)
      * If it cannot work out the format then format_display_name is None
      * If it cannot score it, then score is None
    '''
    format_field = data.get('format', '')
    if not format_field:
        score_reasons.append('Format field is blank.')
        return (None, None)
    format_ = Formats.by_display_name().get(format_field) or \
              Formats.by_extension().get(format_field.lower()) or \
              Formats.by_reduced_name().get(Formats.reduce(format_field))
    if not format_:
        score_reasons.append('Format field "%s" does not correspond to a known format.' % format_field)
        return (None, None)
    score = format_['openness']
    score_reasons.append('Format field "%s" receives score: %s.' % \
                         (format_field, score))
    return (score, format_['display_name'])

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
    try:
        res = requests.post(
            api_url, json.dumps(data),
            headers={'Authorization': context['apikey'],
                     'Content-Type': 'application/json',
                     'User-Agent': USER_AGENT}
        )
    except requests.exceptions.RequestException, e:
        log.error('ckan failed to get the search index updated, error %r.\ncontext: %r\ndataset: %r\napi_url: %r'
                        % (e.args, context, package_id, api_url))
        raise CkanError('ckan failed to get the search index updated, error %s'
                        % e)

    if res.status_code == 200:
        log.info('..Search Index updated')
        return res.content
    else:
        try:
            content = res.content
        except:
            content = '<could not read request content to discover error>'
        log.error('ckan failed to update search index, status_code (%s), error %s. Maybe the API key or site URL are wrong?.\ncontext: %r\ndata: %r\nres: %r\napi_url: %r'
                        % (res.status_code, content, context, data, res, api_url))
        raise CkanError('ckan failed to update search index, status_code (%s), error %s'
                        % (res.status_code, content))
