"""
Score datasets on Sir Tim Bernes-Lee's five stars of openness based on mime-type.
"""
from datetime import datetime
import mimetypes
import json
import requests
import urlparse
from celery.task import task
from ckanext.archiver.tasks import link_checker, LinkCheckerError

class QAError(Exception):
    pass

class CkanError(Exception):
    pass

OPENNESS_SCORE_REASON = {
    -1: 'unscorable content type',
    0: 'not obtainable',
    1: 'obtainable via web page',
    2: 'machine readable format',
    3: 'open and standardized format',
    4: 'ontologically represented',
    5: 'fully Linked Open Data as appropriate',
}

MIME_TYPE_SCORE = {
    'text/html': 1,
    'text/plain': 1,
    'text': 1,
    'html': 1,
    'application/vnd.ms-excel': 2,
    'application/vnd.ms-excel.sheet.binary.macroenabled.12': 2,
    'application/vnd.ms-excel.sheet.macroenabled.12': 2,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 2,
    'xls': 2,
    'text/csv': 3,
    'application/json': 3,
    'text/xml': 3,
    'csv': 3,
    'xml': 3,
    'json': 3,
    'application/rdf+xml': 4,
    'application/xml': 4,
    'xml': 4,
    'rdf': 4
}


def _update_task_status(context, data):
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
        raise CkanError('ckan failed to update task_status, status_code (%s), error %s' 
                        % (res.status_code, res.content))


def _task_status_data(dataset_id, dataset_score_result):
    data = [{
        'entity_id': dataset_id,
        'entity_type': u'package',
        'task_type': 'qa',
        'key': u'openness_score',
        'value': dataset_score_result['openness_score'],
        'last_updated': datetime.now().isoformat()
    }]
    for resource_score in dataset_score_result.get('resource_scores'):
        data.extend([
            {
                'entity_id': resource_score['resource_id'],
                'entity_type': u'resource',
                'task_type': 'qa',
                'key': u'openness_score',
                'value': resource_score['openness_score'],
                'last_updated': datetime.now().isoformat()
            },
            {
                'entity_id': resource_score['resource_id'],
                'entity_type': u'resource',
                'task_type': 'qa',
                'key': u'openness_score_reason',
                'value': resource_score['openness_score_reason'],
                'last_updated': datetime.now().isoformat()
            },
            {
                'entity_id': resource_score['resource_id'],
                'entity_type': u'resource',
                'task_type': 'qa',
                'key': u'openness_score_failure_count',
                'value': resource_score['openness_score_failure_count'],
                'last_updated': datetime.now().isoformat()
            },
        ])
    return data


@task(name = "qa.update")
def update(context, data):
    """
    Score datasets on Sir Tim Bernes-Lee's five stars of openness based on mime-type.
    
    Returns a JSON dict with keys:

        'openness_score': score for dataset (int)
        'resource_scores': resource score dict for each resource in dataset (list)
    """
    try:
        data = json.loads(data)
        context = json.loads(context)
        result = dataset_score(context, data)

        task_status_data = _task_status_data(data['id'], result)

        api_url = urlparse.urljoin(context['site_url'], 'api/action')
        response = requests.post(
            api_url + '/task_status_update_many', 
            json.dumps({'data': task_status_data}),
            headers = {'Authorization': context['apikey'],
                       'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            raise CkanError('ckan failed to update task_status, status_code (%s), error %s' 
                            % (response.status_code, response.content))

        return json.dumps(result)
    except Exception, e:
        _update_task_status(context, {
            'entity_id': data['id'],
            'entity_type': u'package',
            'task_type': 'qa',
            'key': u'celery_task_id',
            'error': '%s: %s' % (e.__class__.__name__,  unicode(e)),
            'last_updated': datetime.now().isoformat()
        })
        raise


def resource_score(context, data):
    """
    Score resources on Sir Tim Bernes-Lee's five stars of openness based on mime-type.

    returns a dict with keys:

        'resource_id': id (int) 
        'openness_score': score (int)
        'openness_score_reason': the reason for the score (string)
        'openness_score_failure_count': the number of consecutive times this resource has returned a score of 0

    Raises the following exceptions:

    """
    score = 0
    score_reason = ""
    score_failure_count = 0

    # TODO: get failure count from task status table if exists

    try:
        headers = json.loads(link_checker("{}", json.dumps(data)))

        cl = headers.get('content_length')
        ct = headers.get('content_type')

        # also get format from resource and by guessing from file extension
        format = data.get('format', '').lower()
        file_type = mimetypes.guess_type(data['url'])[0] 

        # file type takes priority for scoring
        if file_type:
            score = MIME_TYPE_SCORE.get(file_type, -1)
        elif ct:
            score = MIME_TYPE_SCORE.get(ct, -1)
        elif format:
            score = MIME_TYPE_SCORE.get(format, -1)
        
        score_reason = OPENNESS_SCORE_REASON[score]

        # check for mismatches between content-type, file_type and format
        # ideally they should all agree
        if not ct:
            # TODO: use the todo extension to flag this issue
            pass
        else:
            allowed_formats = [ct.lower().split('/')[-1], ct.lower().split('/')]
            allowed_formats.append(ct.lower())
            if format not in allowed_formats:
                # TODO: use the todo extension to flag this issue
                pass
            if file_type != ct:
                # TODO: use the todo extension to flag this issue
                pass

    except LinkCheckerError, e:
        score_reason = str(e)

    if score == 0:
        score_failure_count += 1

    return {
        'resource_id': data['id'],
        'openness_score': score,
        'openness_score_reason': score_reason,
        'openness_score_failure_count': score_failure_count
    }


def dataset_score(context, data):
    """
    Score datasets on Sir Tim Bernes-Lee's five stars of openness based on mime-type.
    
    Returns a dict with keys:

        'openness_score': score for dataset (int)
        'resource_scores': resource score dict for each resource in dataset (list)
    """
    score = 0
    resource_scores = []

    for resource in data.get('resources'):
        r = resource_score(context, resource)
        if r['openness_score'] > score:
            score = r['openness_score']
        resource_scores.append(r)

    return {'openness_score': score, 'resource_scores': resource_scores}

