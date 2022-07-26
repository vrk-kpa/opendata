import logging

import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit
from ckan.lib.navl.dictization_functions import validate

from ckanext.sixodp_showcase.model import ShowcaseApisetAssociation
import ckanext.showcase.logic.converters as showcase_converters
import ckanext.showcase.logic.schema as showcase_schema
from ckanext.sixodp_showcase.logic.schema import (showcase_apiset_association_create_schema)


convert_package_name_or_id_to_title_or_name = \
    showcase_converters.convert_package_name_or_id_to_title_or_name
showcase_package_association_create_schema = \
    showcase_schema.showcase_package_association_create_schema
showcase_admin_add_schema = showcase_schema.showcase_admin_add_schema

log = logging.getLogger(__name__)


def showcase_create(context, data_dict):
    '''Upload the image and continue with package creation.'''

    # force type to 'showcase'
    data_dict['type'] = 'showcase'

    # If get_uploader is available (introduced for IUploader in CKAN 2.5), use
    # it, otherwise use the default uploader.
    # https://github.com/ckan/ckan/pull/2510
    try:
        upload = uploader.get_uploader('showcase')
    except AttributeError:
        upload = uploader.Upload('showcase')

    # schema images
    imgs = ['icon', 'featured_image', 'image_1', 'image_2', 'image_3']
    for image in imgs:
        if data_dict.get(image):
            upload.update_data_dict(data_dict, image,
                                    image + '_upload', 'clear_' + image + '_upload')

            upload.upload(uploader.get_max_image_size())

    pkg = toolkit.get_action('package_create')(context, data_dict)

    return pkg


def showcase_apiset_association_create(context, data_dict):
    '''Create an association between a showcase and a apiset.

    :param showcase_id: id or name of the showcase to associate
    :type showcase_id: string

    :param package_id: id or name of the package to associate
    :type package_id: string
    '''

    toolkit.check_access('ckanext_sixodp_showcase_apiset_association_create',
                         context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(
        data_dict, showcase_apiset_association_create_schema(), context)

    if errors:
        raise toolkit.ValidationError(errors)

    package_id, showcase_id = toolkit.get_or_bust(validated_data_dict,
                                                  ['package_id',
                                                   'showcase_id'])

    if ShowcaseApisetAssociation.exists(package_id=package_id,
                                        showcase_id=showcase_id):
        raise toolkit.ValidationError(
            "ShowcaseApisetAssociation with package_id '{0}' and showcase_id '{1}' already exists.".format(package_id,
                                                                                                           showcase_id),
            error_summary=u"The dataset, {0}, is already in the showcase".format(
                showcase_converters.convert_apiset_name_or_id_to_title_or_name(package_id, context)))

    # create the association
    return ShowcaseApisetAssociation.create(package_id=package_id,
                                            showcase_id=showcase_id)
