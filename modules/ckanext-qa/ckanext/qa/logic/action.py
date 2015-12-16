import logging

import ckan.plugins as p
from ckanext.archiver.model import Archival
from ckanext.qa.model import QA, aggregate_qa_for_a_dataset

log = logging.getLogger(__name__)
_ = p.toolkit._


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
    return_dict = {
        'name': pkg.name,
        'title': pkg.title,
        'id': res.id
        }
    return_dict['archival'] = archival.as_dict()
    return_dict.update(qa.as_dict())
    return return_dict


@p.toolkit.side_effect_free
def qa_package_openness_show(context, data_dict):
    '''
    Returns the QA score for a package, aggregating the
    scores of its resources.
    '''
    model = context['model']
    session = context['session']
    p.toolkit.check_access('qa_package_openness_show', context, data_dict)

    dataset_id = p.toolkit.get_or_bust(data_dict, 'id')
    dataset = session.query(model.Package).get(dataset_id)
    if not dataset:
        raise p.toolkit.ObjectNotFound

    qa_objs = QA.get_for_package(dataset.id)
    qa_dict = aggregate_qa_for_a_dataset(qa_objs)
    return qa_dict
