# -*- coding: utf-8 -*-

import six
from ckan.lib.navl.validators import (not_empty)

from ckanext.sixodp_showcase.logic.validators import (convert_package_name_or_id_to_id_for_type_apiset)
from ckanext.showcase.logic.validators import (convert_package_name_or_id_to_id_for_type_showcase)


def showcase_apiset_association_create_schema():
    schema = {
        'package_id': [not_empty, six.text_type,
                       convert_package_name_or_id_to_id_for_type_apiset],
        'showcase_id': [not_empty, six.text_type,
                        convert_package_name_or_id_to_id_for_type_showcase]
    }
    return schema


def showcase_apiset_association_delete_schema():
    return showcase_apiset_association_create_schema()


def showcase_apiset_list_schema():
    schema = {
        'showcase_id': [not_empty, six.text_type,
                        convert_package_name_or_id_to_id_for_type_showcase]
    }
    return schema


def apiset_showcase_list_schema():
    schema = {
        'package_id': [not_empty, six.text_type,
                       convert_package_name_or_id_to_id_for_type_showcase]
    }
    return schema
