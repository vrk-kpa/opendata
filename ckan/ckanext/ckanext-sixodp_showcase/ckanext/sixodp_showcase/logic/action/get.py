import sqlalchemy

import ckan.plugins.toolkit as toolkit
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.navl.dictization_functions import validate

from ckanext.showcase.logic.schema import package_showcase_list_schema
from ckanext.sixodp_showcase.logic.schema import showcase_apiset_list_schema
from ckanext.showcase.model import ShowcasePackageAssociation
from ckanext.sixodp_showcase.model import ShowcaseApisetAssociation

from ckan.logic import NotAuthorized
import logging
log = logging.getLogger(__name__)

_select = sqlalchemy.sql.select
_and_ = sqlalchemy.and_


@toolkit.side_effect_free
def showcase_list(context, data_dict):
    '''Return a list of all showcases in the site.'''

    toolkit.check_access('ckanext_showcase_list', context, data_dict)

    model = context["model"]

    q = model.Session.query(model.Package) \
        .filter(model.Package.type == 'showcase') \
        .filter(model.Package.state == 'active')

    # Showcase includes private showcases by default, but those can be excluded with include_private = false
    if data_dict.get('include_private') == 'false':
        q = q.filter(model.Package.private == False) # Noqa

    showcase_list = []
    for pkg in q.all():
        showcase_list.append(model_dictize.package_dictize(pkg, context))

    return showcase_list


@toolkit.side_effect_free
def package_showcase_list(context, data_dict):
    '''List showcases associated with a package.

    :param package_id: id or name of the package
    :type package_id: string

    :rtype: list of dictionaries
    '''

    toolkit.check_access('ckanext_package_showcase_list', context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(data_dict,
                                           package_showcase_list_schema(),
                                           context)

    if errors:
        raise toolkit.ValidationError(errors)

    # get a list of showcase ids associated with the package id
    showcase_id_list = ShowcasePackageAssociation.get_showcase_ids_for_package(
        validated_data_dict['package_id'])

    showcase_list = []
    if showcase_id_list is not None:
        for showcase_id in showcase_id_list:
            try:
                showcase = toolkit.get_action('package_show')(context,
                                                              {'id': showcase_id})
                showcase_list.append(showcase)
            except NotAuthorized:
                pass

    return showcase_list


@toolkit.side_effect_free
def showcase_apiset_list(context, data_dict):
    '''List packages associated with a showcase.

    The context variable is passed forward as a copy to avoid unexpected side effects

    :rtype: list of package dictionaries
    '''

    toolkit.check_access('ckanext_showcase_package_list', context.copy(), data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(data_dict,
                                           showcase_apiset_list_schema(),
                                           context.copy())

    if errors:
        raise toolkit.ValidationError(errors)

    # get a list of package ids associated with showcase id
    pkg_id_list = ShowcaseApisetAssociation.get_apiset_ids_for_showcase(
        validated_data_dict['showcase_id'])

    pkg_list = []
    if pkg_id_list:
        # for each package id, get the package dict and append to list if
        # active
        id_list = []
        for pkg_id in pkg_id_list:
            id_list.append(pkg_id[0])
        q = ' OR '.join(['id:{0}'.format(x) for x in id_list])
        _pkg_list = toolkit.get_action('package_search')(
            context,
            {'q': q, 'rows': 100})
        pkg_list = _pkg_list['results']
    return pkg_list
