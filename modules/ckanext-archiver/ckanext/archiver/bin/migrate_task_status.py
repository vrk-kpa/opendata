'''
Tool to migrate archival data from the TaskStatus and Resource tables to
the Archival table.

'''

from optparse import OptionParser
import logging
import json
import datetime

import common
from running_stats import StatsList

# pip install 'ProgressBar==2.3'
from progressbar import ProgressBar, Percentage, Bar, ETA

START_OF_TIME = datetime.datetime(1980, 1, 1)
END_OF_TIME = datetime.datetime(9999, 12, 31)

# NB put no CKAN imports here, or logging breaks


def migrate(options):
    from ckan import model
    from ckanext.archiver.model import Archival, Status

    resources = common.get_resources(state='active',
                                     publisher_ref=options.publisher,
                                     resource_id=options.resource,
                                     dataset_name=options.dataset)
    stats = StatsList()
    widgets = ['Resources: ', Percentage(), ' ', Bar(), ' ', ETA()]
    progress = ProgressBar(widgets=widgets)
    for res in progress(resources):
        # Gather the details of archivals from TaskStatus and Resource
        # to fill all properties of Archival apart from:
        # * package_id
        # * resource_id
        fields = {}
        archiver_task_status = model.Session.query(model.TaskStatus)\
                                    .filter_by(entity_id=res.id)\
                                    .filter_by(task_type='archiver')\
                                    .filter_by(key='status')\
                                    .first()
        if archiver_task_status:
            ats_error = json.loads(archiver_task_status.error)
            fields['status_id'] = Status.by_text(archiver_task_status.value)
            fields['is_broken'] = Status.is_status_broken(fields['status_id'])
            fields['reason'] = ats_error['reason']
            fields['last_success'] = date_str_to_datetime_or_none(ats_error['last_success'])
            fields['first_failure'] = date_str_to_datetime_or_none(ats_error['first_failure'])
            fields['failure_count'] = int(ats_error['failure_count'])
            fields['url_redirected_to'] = ats_error['url_redirected_to']
            fields['updated'] = archiver_task_status.last_updated
        else:
            if not (res.cache_url
                    or res.extras.get('cache_filepath')
                    or res.hash
                    or res.size
                    or res.mimetype):
                add_stat('No archive data', res, stats)
                continue
            for field_name in ('status_id', 'is_broken', 'reason',
                               'last_success', 'first_failure',
                               'failure_count', 'url_redirected_to',
                               'updated', 'created'):
                fields[field_name] = None

        fields['cache_filepath'] = res.extras.get('cache_filepath')
        fields['cache_url'] = res.cache_url
        fields['hash'] = res.hash
        fields['size'] = res.size
        fields['mimetype'] = res.mimetype

        revisions_with_hash = model.Session.query(model.ResourceRevision)\
                .filter_by(id=res.id)\
                .order_by(model.ResourceRevision.revision_timestamp)\
                .filter(model.ResourceRevision.hash != '').all()
        if revisions_with_hash:
            # these are not perfect by not far off
            fields['created'] = revisions_with_hash[0].revision_timestamp
            fields['resource_timestamp'] = revisions_with_hash[-1].revision_timestamp
        else:
            fields['created'] = min(fields['updated'] or END_OF_TIME,
                                    fields['first_failure'] or END_OF_TIME,
                                    fields['last_success'] or END_OF_TIME)
            fields['resource_timestamp'] = max(
                fields['updated'] or START_OF_TIME,
                fields['first_failure'] or START_OF_TIME,
                fields['last_success'] or START_OF_TIME)

        # Compare with any existing data in the Archival table
        archival = Archival.get_for_resource(res.id)
        if archival:
            changed = None
            for field, value in fields.items():
                if getattr(archival, field) != value:
                    if options.write:
                        setattr(archival, field, value)
                    changed = True
            if not changed:
                add_stat('Already exists correctly in archival table', res, stats)
                continue
            add_stat('Updated in archival table', res, stats)
        else:
            archival = Archival.create(res.id)
            if options.write:
                for field, value in fields.items():
                    setattr(archival, field, value)
                model.Session.add(archival)
            add_stat('Added to archival table', res, stats)

    print 'Summary\n', stats.report()
    if options.write:
        model.repo.commit_and_remove()
        print 'Written'


def add_stat(outcome, res, stats, extra_info=None):
    try:
        # pre CKAN 2.3 model
        package_name = res.resource_group.package.name
    except AttributeError:
        # CKAN 2.3+ model
        package_name = res.package.name
    res_id = '%s %s' % (package_name, res.id[:4])
    if extra_info:
        res_id += ' %s' % extra_info
    return '\n' + stats.add(outcome, res_id)


def date_str_to_datetime_or_none(date_str):
    from ckan.lib.helpers import date_str_to_datetime
    if date_str:
        return date_str_to_datetime(date_str)
    return None

if __name__ == '__main__':
    usage = """Tool to migrate archival data from TaskStatus/Resource to Archival table

    usage: %prog [options] <ckan.ini>
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-w", "--write",
                      action="store_true", dest="write",
                      help="write the theme to the datasets")
    parser.add_option('-p', '--publisher', dest='publisher')
    parser.add_option('-d', '--dataset', dest='dataset')
    parser.add_option('-r', '--resource', dest='resource')
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments (%i)' % len(args))
    config_ini = args[0]
    print 'Loading CKAN config...'
    common.load_config(config_ini)
    common.register_translator()
    print 'Done'
    # Setup logging to print debug out for theme stuff only
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.WARNING)
    localLogger = logging.getLogger(__name__)
    localLogger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    localLogger.addHandler(handler)
    migrate(options)
