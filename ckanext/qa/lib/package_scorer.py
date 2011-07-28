"""
Score packages on Sir Tim Bernes-Lee's five stars of openness based on mime-type
"""
import datetime
import mimetypes
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
        'text',
        'html',
    ],
    '2': [
        'application/vnd.ms-excel',
        'application/vnd.ms-excel.sheet.binary.macroenabled.12',
        'application/vnd.ms-excel.sheet.macroenabled.12',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls',
    ],
    '3': [
        'text/csv',
        'application/json',
        'text/xml',
        'csv',
        'xml',
        'json',
    ],
    '4': [
        'application/rdf+xml',
        'application/xml',
        'xml',
        'rdf',
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
            cl = archive_result['content_length']
            ct = archive_result['content_type']

            if archive_result['success'] == 'True':
                # also get format from resource and by guessing from file extension
                format = resource.get('format', '').lower()
                file_type = mimetypes.guess_type(resource.get('url'))[0] 

                # content-type takes priority for scoring
                if ct:
                    openness_score = score_by_mime_type.get(ct, '-1')
                elif file_type:
                    openness_score = score_by_mime_type.get(file_type, '-1')
                elif format:
                    openness_score = score_by_mime_type.get(format, '-1')
                
                reason = openness_score_reason[openness_score]

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
    if not 'openness_score_last_checked' in [e['key'] for e in package_extras]:
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
