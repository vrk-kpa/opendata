"""
Score datasets on Sir Tim Bernes-Lee's five stars of openness based on mime-type.
"""
import datetime
import mimetypes
import json
import requests
import urlparse
from celery.task import task

class QAError(Exception):
    pass

class CkanError(Exception):
    pass

OPENNESS_SCORE_REASON = {
    '-1': 'unscorable content type',
    '0': 'not obtainable',
    '1': 'obtainable via web page',
    '2': 'machine readable format',
    '3': 'open and standardized format',
    '4': 'ontologically represented',
    '5': 'fully Linked Open Data as appropriate',
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


@task(name = "qa.update")
def update(context, data):
    logger = update.get_logger()

    try:
        data = json.loads(data)
        context = json.loads(context)
        result = dataset_score(context, data, logger)
        return json.dumps(result)
    except Exception, e:
        _update_task_status(context, {
            'entity_id': data['id'],
            'entity_type': u'resource',
            'task_type': 'qa',
            'key': u'celery_task_id',
            'error': '%s: %s' % (e.__class__.__name__,  unicode(e)),
            'last_updated': datetime.now().isoformat()
        })
        raise


def resource_score(context, data, logger):
    """
    Score resources on Sir Tim Bernes-Lee's five stars of openness based on mime-type.

    returns a dict with keys:

        'resource_id': id (int) 
        'openness_score': score (int)
        'openness_score_reason': the reason for the score (string)
        'openness_score_failure_count': the number of consecutive times this resource has returned a score of 0

    Raises the following exceptions:

    """
    id = data['id']
    score = 0
    score_reason = ""
    score_failure_count = 0

    # archive_result = get_resource_result(results_file, resource['id'])

    # if not archive_result:
    #     # set a default message if no archive result for this resource
    #     reason = u"URL unobtainable"
    # else:
    #     reason = archive_result['message']
    #     cl = archive_result['content_length']
    #     ct = archive_result['content_type']

    #     if archive_result['success'] == 'True':
    #         # also get format from resource and by guessing from file extension
    #         format = resource.get('format', '').lower()
    #         file_type = mimetypes.guess_type(resource.get('url'))[0] 

    #         # file type takes priority for scoring
    #         if file_type:
    #             openness_score = MIME_TYPE_SCORE.get(file_type, '-1')
    #         elif ct:
    #             openness_score = MIME_TYPE_SCORE.get(ct, '-1')
    #         elif format:
    #             openness_score = MIME_TYPE_SCORE.get(format, '-1')
            
    #         reason = OPENNESS_SCORE_REASON[openness_score]

    #         # check for mismatches between content-type, file_type and format
    #         # ideally they should all agree
    #         if not ct:
    #             # TODO: use the todo extension to flag this issue
    #             pass
    #         else:
    #             allowed_formats = [ct.lower().split('/')[-1], ct.lower().split('/')]
    #             allowed_formats.append(ct.lower())
    #             if format not in allowed_formats:
    #                 # TODO: use the todo extension to flag this issue
    #                 pass
    #             if file_type != ct:
    #                 # TODO: use the todo extension to flag this issue
    #                 pass

    # # Set the failure count
    # if openness_score == '0':
    #     openness_score_failure_count += 1
    # # update package openness score
    # if openness_score > package_openness_score:
    #     package_openness_score = openness_score

    # # update the resource
    # context = {
    #     'id': resource['id'], 'model': model, 'session': model.Session, 
    #     'user': MAINTENANCE_AUTHOR, 'extras_as_string': True
    # }
    # resource[u'openness_score'] = openness_score
    # resource[u'openness_score_reason'] = reason
    # resource[u'openness_score_failure_count'] = unicode(openness_score_failure_count)
    # update.resource_update(context, resource)
    # log.info('Score for resource: %s (%s)' % (openness_score, reason))

    return {
        'resource_id': id,
        'openness_score': score,
        'openness_score_reason': score_reason,
        'openness_score_failure_count': score_failure_count
    }


def dataset_score(context, data, logger):
    """
    Score datasets on Sir Tim Bernes-Lee's five stars of openness based on mime-type.
    
    Returns a dict with keys:

        'openness_score': score for dataset (int)
        'resource_scores': resource score dict for each resource in dataset (list)

    Raises the following exceptions:

    """
    score = 0
    resource_scores = []

    for resource in data.get('resources'):
        r = resource_score(context, resource, logger)
        if r['openness_score'] > score:
            score = r['openness_score']
        resource_scores.append(r)

    logger.info('Finished QA analysis of package: %s (score = %s)' 
        % (data.get('name'), score)
    )

    return {'openness_score': score, 'resource_scores': resource_scores}

