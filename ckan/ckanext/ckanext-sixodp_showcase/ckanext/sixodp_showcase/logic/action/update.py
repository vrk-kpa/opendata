import logging

import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


def showcase_update(context, data_dict):

    # If get_uploader is available (introduced for IUploader in CKAN 2.5), use
    # it, otherwise use the default uploader.
    # https://github.com/ckan/ckan/pull/2510

    # schema images
    imgs = ['icon', 'featured_image', 'image_1', 'image_2', 'image_3']
    for image in imgs:
        if data_dict.get(image):
            try:
                upload = uploader.get_uploader('showcase', data_dict[image])
            except AttributeError:
                upload = uploader.Upload('showcase', data_dict[image])

            upload.update_data_dict(data_dict, image,
                                    image + '_upload', 'clear_' + image + '_upload')

            upload.upload(uploader.get_max_image_size())

    pkg = toolkit.get_action('package_update')(context, data_dict)

    return pkg
