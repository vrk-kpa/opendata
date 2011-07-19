"""
Score packages on Sir Tim Bernes-Lee's five stars of openness based on mime-type
"""
import datetime
from db import get_resource_result
from ckanext.qa.lib.log import log

openness_score_reason = {
    '-1': 'unscorable content type',
    '0': 'not obtainable',
    '1': 'obtainable via web page',
    '2': 'machine readable format',
    '3': 'open and standardized format',
    '4': 'ontologically represented',
    '5': 'fully Linked Open Data as appropriate',
}

mime_types_scores = {
    '1': [
        'text/html',
        'text/plain',
    ],
    '2': [
        'application/vnd.ms-excel',
        'application/vnd.ms-excel.sheet.binary.macroenabled.12',
        'application/vnd.ms-excel.sheet.macroenabled.12',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ],
    '3': [
        'text/csv',
        'application/json',
        'text/xml',
    ],
    '4': [
        'application/rdf+xml',
        'application/xml',
    ],
    '5': [],
}

score_by_mime_type = {}
for score, mime_types in mime_types_scores.items():
    for mime_type in mime_types:
        score_by_mime_type[mime_type] = score

def package_score(package, results_file):
    openness_score = '0'
    for resource in package.resources:
        archive_result = get_resource_result(results_file, resource.id)
        if not archive_result:
            # set a default message if no archive result for this resource
            # TODO: Should this happen? We should be archiving GET request failures anyway, 
            #       so should this just throw an error?
            resource.extras[u'openness_score'] = '0'
            resource.extras[u'openness_score_reason'] = u"URL unobtainable"
        elif not bool(archive_result['success']):
            resource.extras[u'openness_score'] = '0'
            resource.extras[u'openness_score_reason'] = archive_result['message']
        else:
            ct = archive_result['content_type']
            resource.extras[u'content_length'] = archive_result['content_length']
            if ct:
                resource.extras[u'content_type'] = ct.split(';')[0]
                resource.extras[u'openness_score'] = score_by_mime_type.get(resource.extras[u'content_type'], '-1')
            else:
                resource.extras[u'content_type'] = None
                resource.extras[u'openness_score'] = '0'
            resource.extras[u'openness_score_reason'] = openness_score_reason[resource.extras[u'openness_score']]

            if ct:
                if resource.format and resource.format.lower() not in [
                    resource.extras[u'content_type'].lower().split('/')[-1],
                    resource.extras[u'content_type'].lower().split('/'),
                ]:
                    resource.extras[u'openness_score_reason'] = \
                        'The format entered for the resource doesn\'t match the description from the web server'
                    resource.extras[u'openness_score'] = '0'

        # Set the failure count
        if resource.extras[u'openness_score'] == '0':
            # At this point save the pacakge and resource, and maybe try it again
            resource.extras['openness_score_failure_count'] = \
                resource.extras.get('openness_score_failure_count', 0) + 1
        else:
            resource.extras['openness_score_failure_count'] = 0
        # String comparison
        if resource.extras[u'openness_score'] > openness_score:
            openness_score = resource.extras[u'openness_score']

        log.info('Finished QA analysis of resource: %s' % resource.url)

    package.extras[u'openness_score_last_checked'] = datetime.datetime.now().isoformat()
    package.extras[u'openness_score'] = openness_score
