import logging

import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit


import ckanext.showcase.logic.converters as showcase_converters
import ckanext.showcase.logic.schema as showcase_schema


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
        if data_dict[image]:
            upload.update_data_dict(data_dict, image,
                                image+'_upload', 'clear_'+ image + '_upload')

            upload.upload(uploader.get_max_image_size())

    pkg = toolkit.get_action('package_create')(context, data_dict)

    return pkg