import logging
import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions

from ckanext.sixodp_showcase.logic.schema import (showcase_apiset_association_delete_schema)
from ckanext.sixodp_showcase.model import (ShowcaseApisetAssociation)


validate = ckan.lib.navl.dictization_functions.validate

log = logging.getLogger(__name__)


def showcase_apiset_association_delete(context, data_dict):
    '''Delete an association between a showcase and a apiset.

    :param showcase_id: id or name of the showcase in the association
    :type showcase_id: string

    :param package_id: id or name of the apiset in the association
    :type package_id: string
    '''

    model = context['model']

    toolkit.check_access('ckanext_sixodp_showcase_apiset_association_delete',
                         context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(
        data_dict, showcase_apiset_association_delete_schema(), context)

    if errors:
        raise toolkit.ValidationError(errors)

    package_id, showcase_id = toolkit.get_or_bust(validated_data_dict,
                                                  ['package_id',
                                                   'showcase_id'])

    showcase_apiset_association = ShowcaseApisetAssociation.get(
        package_id=package_id, showcase_id=showcase_id)

    if showcase_apiset_association is None:
        raise toolkit.ObjectNotFound(
            "ShowcaseApisetAssociation with package_id '{0}' and showcase_id '{1}' doesn't exist.".format(package_id,
                                                                                                          showcase_id))

    # delete the association
    showcase_apiset_association.delete()
    model.repo.commit()
