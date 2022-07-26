from ckanext.showcase.logic.validators import convert_package_name_or_id_to_id_for_type


def convert_package_name_or_id_to_id_for_type_apiset(package_name_or_id,
                                                     context):
    return convert_package_name_or_id_to_id_for_type(package_name_or_id,
                                                     context,
                                                     package_type='apiset')
