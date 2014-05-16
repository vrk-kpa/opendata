import logging

import ckan.plugins as p
from ckan.lib.search import index_for
from ckanext.archiver.model import Archival
from ckanext.qa.model import QA

log = logging.getLogger(__name__)
_ = p.toolkit._


def search_index_update(context, data_dict):
    '''
    Tells CKAN to update its search index for a given package.

    This is needed because the QA value (and archiver is_broken) is added to
    the search index by other extensions (like ckanext-dgu).  TODO: Probably
    better to create a notification that another extension (like ckanext-dgu)
    can trigger it itself.
    '''
    model = context['model']
    #session = context['session']
    #user = context.get('user')
    p.toolkit.check_access('search_index_update', context, data_dict)

    pkg_dict = p.toolkit.get_action('package_show')(
        {'model': model, 'ignore_auth': True, 'validate': False,
         'use_cache': False},
        data_dict)

    indexer = index_for('package')
    indexer.update_dict(pkg_dict)

    log.info('Search index updated for: %s', pkg_dict['name'])


@p.toolkit.side_effect_free
def qa_resource_show(context, data_dict):
    '''
    Returns the QA and Archival information for a package or resource.
    '''
    model = context['model']
    session = context['session']
    #user = context.get('user')
    #p.toolkit.check_access('qa_resource_show', context, data_dict)

    res_id = p.toolkit.get_or_bust(data_dict, 'id')
    res = session.query(model.Resource).get(res_id)
    if not res:
        raise p.toolkit.ObjectNotFound

    archival = Archival.get_for_resource(res_id)
    qa = QA.get_for_resource(res_id)
    pkg = res.resource_group.package
    return {'name': pkg.name,
            'title': pkg.title,
            'id': res.id,
            'archival_updated': archival.updated.isoformat() if archival and archival.updated else None,
            'archival_is_broken': archival.is_broken if archival else None,
            'archival_reason': archival.reason if archival else None,
            'archival_url_redirected_to': archival.url_redirected_to if archival else None,
            'openness_score': qa.openness_score if qa else None,
            'openness_score_reason': qa.openness_score_reason if qa else None,
            'updated': qa.updated.isoformat() if qa and qa.updated else None,
            'format': qa.format if qa else None,
            }


@p.toolkit.side_effect_free
def qa_package_broken_show(context, data_dict):
    '''
    Returns the Archival is_broken information for a package, aggregating
    across its resources.

    is_broken - True (all), 'some', False or None (not sure)
    '''
    model = context['model']
    session = context['session']
    #user = context.get('user')
    #p.toolkit.check_access('qa_package_broken_show', context, data_dict)

    pkg_id = p.toolkit.get_or_bust(data_dict, 'id')
    pkg = session.query(model.Package).get(pkg_id)
    if not pkg:
        raise p.toolkit.ObjectNotFound

    if pkg.resources:
        # Are any broken?
        any_resources_broken = False
        any_resources_ok = False
        for archival in Archival.get_for_package(pkg_id):
            if archival.is_broken is True:
                any_resources_broken = True
            elif archival.is_broken is False:
                any_resources_ok = True
        if any_resources_broken and any_resources_ok:
            is_broken = 'some'  # i.e. some broken
        elif any_resources_broken:
            is_broken = True  # all broken
        elif any_resources_ok:
            is_broken = False  # all ok
        else:
            is_broken = None  # not sure / not recorded
    else:
        is_broken = False
    return {'name': pkg.name,
            'title': pkg.title,
            'id': pkg.id,
            'archival_is_broken': is_broken,
            }


@p.toolkit.side_effect_free
def qa_package_openness_show(context, data_dict):
    '''
    Returns the QA score for a package, aggregating the
    scores of its resources.
    '''
    model = context['model']
    session = context['session']
    #user = context.get('user')
    #p.toolkit.check_access('qa_package_openness_show', context, data_dict)

    pkg_id = p.toolkit.get_or_bust(data_dict, 'id')
    pkg = session.query(model.Package).get(pkg_id)
    if not pkg:
        raise p.toolkit.ObjectNotFound

    if pkg.resources:
        # Aggregate openness score
        best_score = None
        best_score_reason = None
        latest_update = None
        for qa in QA.get_for_package(pkg_id):
            if best_score is None or qa.openness_score > best_score:
                best_score = qa.openness_score
                best_score_reason = qa.openness_score_reason
            if not latest_update or qa.updated > latest_update:
                latest_update = qa.updated
    else:
        best_score = 0
        best_score_reason = 'Dataset has no resources.'
        latest_update = None
    return {'name': pkg.name,
            'title': pkg.title,
            'id': pkg.id,
            'openness_score': best_score,
            'openness_score_reason': best_score_reason,
            'updated': latest_update.isoformat() if latest_update else None,
            }
