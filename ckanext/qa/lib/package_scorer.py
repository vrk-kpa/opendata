"""
Score packages on Sir Tim Bernes-Lee's five stars of openness based on mime-type
"""
import datetime
from db import get_resource_result
from ckan.logic.action import update
from ckan import model
from ckanext.qa.lib.log import log

# Use this specific author so that these revisions can be filtered out of
# normal RSS feeds that cover significant package changes. See DGU#982.
MAINTENANCE_AUTHOR = u'okfn_maintenance'

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
    package_extras = package.get('extras', [])
    package_openness_score = '0'

    for resource in package.get('resources'):
        log.info("Checking resource: %s" % resource['url'])
        archive_result = get_resource_result(results_file, resource['id'])

        openness_score = u'0'
        openness_score_failure_count = int(
            resource.get('openness_score_failure_count', 0)
        )

        if not archive_result:
            # set a default message if no archive result for this resource
            reason = u"URL unobtainable"
        else:
            reason = archive_result['message']
            ct = archive_result['content_type']
            cl = archive_result['content_length']

            if archive_result['success'] == 'True':
                openness_score = score_by_mime_type.get(ct, '-1')
                reason = openness_score_reason[openness_score]

                if ct:
                    if resource['format'] and resource['format'].lower() not in [
                        ct.lower().split('/')[-1], ct.lower().split('/'),
                    ]:
                        reason = u'The format entered for the resource doesn\'t ' + \
                            u'match the description from the web server'
                        openness_score = u'0'

        # Set the failure count
        if openness_score == '0':
            openness_score_failure_count += 1
        # update package openness score
        if openness_score > package_openness_score:
            package_openness_score = openness_score

        # update the resource
        context = {
            'id': resource['id'], 'model': model, 'session': model.Session, 
            'user': MAINTENANCE_AUTHOR, 'extras_as_string': True
        }
        resource[u'openness_score'] = openness_score
        resource[u'openness_score_reason'] = reason
        resource[u'openness_score_failure_count'] = unicode(openness_score_failure_count)
        update.resource_update(context, resource)
        log.info('Score for resource: %s (%s)' % (openness_score, reason))

    # package openness score
    if not 'openness_score' in [e['key'] for e in package_extras]:
        package_extras.append({
            'key': u'openness_score',
            'value': package_openness_score
        })
    else:
        for e in package_extras:
            if e['key'] == 'openness_score':
                e['value'] = package_openness_score

    # package openness score last checked
    if not 'openness_score' in [e['key'] for e in package_extras]:
        package_extras.append({
            'key': u'openness_score_last_checked',
            'value': datetime.datetime.now().isoformat()
        })
    else:
        for e in package_extras:
            if e['key'] == 'openness_score_last_checked':
                e['value'] = datetime.datetime.now().isoformat()
    
    context = {
        'id': package['id'], 'model': model, 'session': model.Session, 
        'user': MAINTENANCE_AUTHOR, 'extras_as_string': True
    }
    package['extras'] = package_extras
    update.package_update(context, package)
    log.info('Finished QA analysis of package: %s (score = %s)' 
        % (package['name'], package_openness_score))
