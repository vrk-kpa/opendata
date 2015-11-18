import logging

import ckan.logic as logic
import ckan.plugins as p
from ckan import model
from ckanext.archiver.model import Archival, aggregate_archivals_for_a_dataset

NotFound = logic.NotFound
_get_or_bust = logic.get_or_bust

log = logging.getLogger(__name__)


@p.toolkit.side_effect_free
def archiver_resource_show(context, data_dict=None):
    '''Return a details of the archival of a resource

    :param id: the id of the resource
    :type id: string

    :rtype: dictionary
    '''
    id_ = _get_or_bust(data_dict, 'id')
    archival = Archival.get_for_resource(id_)
    if archival is None:
        raise NotFound
    archival_dict = archival.as_dict()
    p.toolkit.check_access('archiver_resource_show', context, data_dict)
    return archival_dict


@p.toolkit.side_effect_free
def archiver_dataset_show(context, data_dict=None):
    '''Return a details of the archival of a dataset, aggregated across its
    resources.

    :param id: the name or id of the dataset
    :type id: string

    :rtype: dictionary
    '''
    id_ = _get_or_bust(data_dict, 'id')
    dataset = model.Package.get(id_)
    if not dataset:
        raise NotFound
    archivals = Archival.get_for_package(dataset.id)
    archival_dict = aggregate_archivals_for_a_dataset(archivals)
    p.toolkit.check_access('archiver_dataset_show', context, data_dict)
    return archival_dict
