from ckan import plugins, model
from ckan.plugins import toolkit
from ckan.common import c, request, _

from ckanext.ytp.common.converters import to_list_json, is_url, convert_to_tags_string, string_join
from ckanext.ytp.common.tools import add_translation_modify_schema, add_languages_modify, add_languages_show, add_translation_show_schema

import logging
from ckanext.ytp.common import tools
from ckanext.ytp.common.helpers import get_dict_tree_from_json
from sqlalchemy.sql.expression import or_
from ckan.lib.dictization import model_dictize
from ckan.logic import auth
from ckanext.harvest.model import HarvestObject
from ckan.lib.navl.dictization_functions import missing, Invalid

import ckan.new_authz as authz

log = logging.getLogger(__name__)


def set_to_value(preset_value):
    def method(value, context):
        return preset_value
    return method


def static_value(preset_value):
    def method(value, context):
        return preset_value
    return method


def service_charge_validator(key, data, errors, context):
    """Validates the fields related to service charge.

    If the service has a charge, then the user must also supply either the pricing information URL or a description of the service pricing or both."""

    # Get the value for the service charge radio field
    service_charge_value = data.get(key)

    if service_charge_value is missing or service_charge_value is None or service_charge_value == '':
        # At least one of the service charge values must be selected
        raise Invalid(_('Service charge must be supplied'))
    elif service_charge_value == 'yes':
        # Check if the service has a charge
        # Get the pricing information url and service price description values from the data (the key is a tuple)
        pricing_url_value = data.get(('pricing_information_url',))
        service_price_value = data.get(('service_price_description',))

        if ((pricing_url_value is missing or pricing_url_value is None or pricing_url_value == '') and
                (service_price_value is missing or service_price_value is None or service_price_value == '')):
            # If both the pricing information url and the service price description fields are empty, show an error message
            raise Invalid(_('If there is a service charge, you must supply either the pricing information web address for this service or a description of ' +
                            'the service pricing or both'))
    return service_charge_value


def target_groups_validator(key, data, errors, context):
    """Validates the target groups field.

    At least one of the main target groups needs to be selected."""

    target_groups_value = data.get(key)
    if target_groups_value is missing or target_groups_value is None or target_groups_value == '':
        raise Invalid(_('At least one of the main target groups must to be selected'))
    return target_groups_value


class YTPServiceForm(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)

    _localized_fields = ['title', 'notes', 'alternative_title', 'usage_requirements',  # 1
                         'service_provider_other', 'service_class',  # 2
                         'pricing_information_url', 'service_price_description', 'processing_time_estimate',  # 3
                         'service_main_usage', 'decisions_and_documents_electronic_where', 'communicate_service_digitally_how']  # 3

    # optional text fields
    _text_fields = ['alternative_title', 'usage_requirements',  # 1
                    'service_provider_other', 'service_class',  # 2
                    'processing_time_estimate',  # 3
                    'service_main_usage', 'average_service_time_estimate', 'remote_service_duration_per_customer',
                    'decisions_and_documents_electronic_where', 'communicate_service_digitally_how']  # 3
    _radio_fields = ['service_region',  # 1
                     'remote_service', 'decisions_and_documents_electronic',  # 3
                     'communicate_service_digitally']  # 3
    _select_fields = ['service_cluster', 'production_type']  # 1

    _custom_text_fields = _text_fields + _radio_fields + _select_fields

    def update_config(self, config):
        toolkit.add_public_directory(config, '/var/www/resources')
        toolkit.add_resource('public/javascript/', 'ytp_service_js')
        toolkit.add_template_directory(config, 'templates')

        toolkit.add_resource('../common/public/javascript/', 'ytp_common_js')
        toolkit.add_template_directory(config, '../common/templates')

    # IDatasetForm #

    def _modify_package_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_to_extras = toolkit.get_converter('convert_to_extras')

        schema = add_translation_modify_schema(schema)
        schema = add_languages_modify(schema, self._localized_fields)

        for text_field in self._custom_text_fields:
            schema.update({text_field: [ignore_missing, unicode, convert_to_extras]})

        schema.update({'collection_type': [set_to_value(u'Public Service'), unicode, convert_to_extras]})
        schema.update({'extra_information': [ignore_missing, is_url, to_list_json, convert_to_extras]})
        schema.update({'municipalities': [ignore_missing, convert_to_tags_string('municipalities')]})
        schema.update({'target_groups': [target_groups_validator, convert_to_tags_string('target_groups')]})
        schema.update({'life_situations': [ignore_missing, convert_to_tags_string('life_situations')]})

        # Make the following fields mandatory
        schema.update({'decisions_and_documents_electronic': [unicode, convert_to_extras]})
        schema.update({'communicate_service_digitally': [unicode, convert_to_extras]})

        # Apply the service_charge_validator to the service charge field
        schema.update({'service_charge': [service_charge_validator, unicode, convert_to_extras]})
        schema.update({'pricing_information_url': [is_url, unicode, convert_to_extras]})
        schema.update({'service_price_description': [unicode, convert_to_extras]})

        # Service channels
        resources_schema = schema.get('resources')
        resources_schema.update({'url': [ignore_missing, unicode]})

        # Remove tags from the form's data model
        del schema['tag_string']

        return schema

    def create_package_schema(self):
        schema = super(YTPServiceForm, self).create_package_schema()
        return self._modify_package_schema(schema)

    def update_package_schema(self):
        schema = super(YTPServiceForm, self).update_package_schema()
        return self._modify_package_schema(schema)

    def show_package_schema(self):
        schema = super(YTPServiceForm, self).show_package_schema()

        ignore_missing = toolkit.get_validator('ignore_missing')
        convert_from_extras = toolkit.get_converter('convert_from_extras')

        schema = add_translation_show_schema(schema)
        schema = add_languages_show(schema, self._localized_fields)

        for text_field in self._custom_text_fields:
            schema.update({text_field: [convert_from_extras, ignore_missing]})

        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))
        schema.update({'collection_type': [static_value(u'Public Service')]})
        schema.update({'municipalities': [toolkit.get_converter('convert_from_tags')('municipalities'), string_join, ignore_missing]})
        schema.update({'target_groups': [toolkit.get_converter('convert_from_tags')('target_groups'), string_join, ignore_missing]})
        schema.update({'life_situations': [toolkit.get_converter('convert_from_tags')('life_situations'), string_join, ignore_missing]})

        schema.update({'service_charge': [convert_from_extras, ignore_missing]})
        schema.update({'pricing_information_url': [convert_from_extras, ignore_missing]})
        schema.update({'service_price_description': [convert_from_extras, ignore_missing]})

        # Do not show the tags
        del schema['tag_string']

        return schema

    def package_types(self):
        return ['service']

    def is_fallback(self):
        return False

    def new_template(self):
        return 'package/ytp/service/new.html'

    def package_form(self):
        return 'package/ytp/service/new_package_form.html'

    def setup_template_variables(self, context, data_dict):
        c.preselected_group = request.params.get('group', None)
        super(YTPServiceForm, self).setup_template_variables(context, data_dict)

    # # IAuthFunctions # #

    def _package_common(self, context, data_dict=None):
        if data_dict is None:
            data_dict = {}

        if data_dict and (data_dict.get('type', None) == 'service' or data_dict.get('collection_type', None) == u'Public Service'):
            result = self._can_create_service(context, data_dict)
            if result.get('success') is False:
                return result
            owner_organization = data_dict.get('owner_org', None)
            if owner_organization:
                organization = model.Group.get(owner_organization)
                if not organization:
                    return {'success': False, 'msg': _('Organization does not exist')}
                if organization.extras.get('public_adminstration_organization', None) != 'true':
                    return {'success': False, 'msg': _('Invalid organization type')}
        return None

    def _package_create(self, context, data_dict=None):
        result = self._package_common(context, data_dict)
        if result:
            return result

        return tools.get_original_method('ckan.logic.auth.create', 'package_create')(context, data_dict)

    def _package_update(self, context, data_dict=None):
        result = self._package_common(context, data_dict)
        if result:
            return result

        package = auth.get_package_object(context, data_dict)
        harvest_object_count = model.Session.query(HarvestObject) \
            .filter(HarvestObject.package_id == package.id) \
            .filter(HarvestObject.current == True) \
            .count()  # noqa

        if harvest_object_count > 0:
            return {'success': False, 'msg': _("Harvested datasets are read-only")}

        return tools.get_original_method('ckan.logic.auth.update', 'package_update')(context, data_dict)

    def _can_create_service(self, context, data_dict=None):
        log.debug("Can create service")
        if 'auth_user_obj' not in context:
            return {'success': False, 'msg': _("Login required")}
        user_object = context['auth_user_obj']
        query = model.Session.query(model.Member).filter(model.Member.table_name == "user").filter(model.Member.table_id == user_object.id) \
            .filter(model.Member.state == 'active').filter(or_(model.Member.capacity == 'admin', model.Member.capacity == 'editor'))
        if query.count() < 1:
            return {'success': False, 'msg': _('User %s is not part of any public organization')}

        group_ids = [member.group_id for member in query]

        for group in model.Session.query(model.Group).filter(model.Group.id.in_(group_ids)):
            if 'public_adminstration_organization' in group.extras and group.extras['public_adminstration_organization'] == 'true':
                return {'success': True}

        return {'success': False, 'msg': _('User %s is not part of any public organization')}

    def get_auth_functions(self):
        return {'package_create': self._package_create, 'package_update': self._package_update, 'can_create_service': self._can_create_service}

    # # ITemplateHelpers # #

    def _service_organizations(self):
        ''' modified from organization_list_for_user '''
        context = {'user': c.user}
        data_dict = {'permission': 'create_dataset'}
        user = context['user']

        toolkit.check_access('organization_list_for_user', context, data_dict)
        sysadmin = authz.is_sysadmin(user)

        orgs_q = model.Session.query(model.Group) \
            .filter(model.Group.is_organization == True) \
            .filter(model.Group.state == 'active')  # noqa

        if not sysadmin:
            # for non-Sysadmins check they have the required permission

            permission = data_dict.get('permission', 'edit_group')

            roles = authz.get_roles_with_permission(permission)

            if not roles:
                return []
            user_id = authz.get_user_id_for_username(user, allow_none=True)
            if not user_id:
                return []

            q = model.Session.query(model.Member) \
                .filter(model.Member.table_name == 'user') \
                .filter(model.Member.capacity.in_(roles)) \
                .filter(model.Member.table_id == user_id) \
                .filter(model.Member.state == 'active')

            group_ids = []
            for row in q.all():
                group_ids.append(row.group_id)

            if not group_ids:
                return []

            orgs_q = orgs_q.filter(model.Group.id.in_(group_ids))
            orgs_q = orgs_q.join(model.GroupExtra).filter(model.GroupExtra.key == u'public_adminstration_organization') \
                .filter(model.GroupExtra.value == u'true')  # YTP modification

        return model_dictize.group_list_dictize(orgs_q.all(), context)

    def get_helpers(self):
        return {'service_organization': self._service_organizations,
                'get_dict_tree_from_json': get_dict_tree_from_json}
