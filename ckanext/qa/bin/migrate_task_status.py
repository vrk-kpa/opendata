'''
Tool to migrate QA data from the TaskStatus table to the QA table.

You could just rerun the QA to populate the new QA table, but you'd miss key
information - resources that are no longer available but had the format
detected in the past.
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
TODAY = datetime.datetime.now()

# NB put no CKAN imports here, or logging breaks


def migrate(options):
    from ckan import model
    from ckanext.archiver.model import Archival
    from ckanext.qa.model import QA

    resources = common.get_resources(state='active',
                                     publisher_ref=options.publisher,
                                     resource_id=options.resource,
                                     dataset_name=options.dataset)
    stats = StatsList()
    widgets = ['Resources: ', Percentage(), ' ', Bar(), ' ', ETA()]
    progress = ProgressBar(widgets=widgets)
    for res in progress(resources):
        # Gather the details of QA from TaskStatus
        # to fill all properties of QA apart from:
        # * package_id
        # * resource_id
        fields = {}
        qa_task_status = model.Session.query(model.TaskStatus)\
                                    .filter_by(entity_id=res.id)\
                                    .filter_by(task_type='qa')\
                                    .filter_by(key='status')\
                                    .first()
        if not qa_task_status:
            add_stat('No QA data', res, stats)
            continue
        qa_error = json.loads(qa_task_status.error)
        fields['openness_score'] = int(qa_task_status.value)
        fields['openness_score_reason'] = qa_error['reason']
        fields['format'] = qa_error['format']
        qa_date = qa_task_status.last_updated
        # NB qa_task_status.last_updated appears to be 1hr ahead of the revision
        # time, so some timezone nonesense going on. Can't do much.
        archival = Archival.get_for_resource(res.id)
        if not archival:
            print add_stat('QA but no Archival data', res, stats)
            continue
        archival_date = archival.updated
        # the state of the resource was as it was archived on the date of
        # the QA update but we only know when the latest archival was. So
        # if it was archived before the QA update thenwe know that was the
        # archival, otherwise we don't know when the relevant archival was.
        if archival_date and qa_date >= archival_date:
            fields['archival_timestamp'] = archival_date
            fields['updated'] = archival_date
            fields['created'] = archival_date
            # Assume the resource URL archived was the one when the
            # archival was done (it may not be if the URL was queued and
            # there was significant delay before it was archived)
            get_resource_as_at = archival_date
        else:
            # This is common for when a resource is created and qa runs just
            # before archiver and you get:
            # "This file had not been downloaded at the time of scoring it."
            # Just put sensible datetimes since we don't really know the exact
            # ones
            fields['archival_timestamp'] = qa_date
            fields['updated'] = qa_date
            fields['created'] = qa_date
            get_resource_as_at = qa_date
        res_rev = model.Session.query(model.ResourceRevision).\
            filter_by(id=res.id).\
            filter(model.ResourceRevision.revision_timestamp < get_resource_as_at).\
            order_by(model.ResourceRevision.revision_timestamp.desc()).\
            first()
        fields['resource_timestamp'] = res_rev.revision_timestamp

        # Compare with any existing data in the Archival table
        qa = QA.get_for_resource(res.id)
        if qa:
            changed = None
            for field, value in fields.items():
                if getattr(qa, field) != value:
                    if options.write:
                        setattr(qa, field, value)
                    changed = True
            if not changed:
                add_stat('Already exists correctly in QA table', res, stats)
                continue
            add_stat('Updated in QA table', res, stats)
        else:
            qa = QA.create(res.id)
            if options.write:
                for field, value in fields.items():
                    setattr(qa, field, value)
                model.Session.add(qa)
            add_stat('Added to QA table', res, stats)

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
    usage = """Tool to migrate QA data from TaskStatus to QA table

    usage: %prog [options] <ckan.ini>
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-w", "--write",
                      action="store_true", dest="write",
                      help="write the changes")
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
    # Setup logging to print debug out for local only
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.WARNING)
    localLogger = logging.getLogger(__name__)
    localLogger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    localLogger.addHandler(handler)
    migrate(options)
