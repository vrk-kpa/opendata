import os
import logging
import json
import urllib.request
import urllib.error
import urllib.parse
import datetime
import itertools
import flask
from ckan.common import _, c, request
from ckan.lib import helpers, i18n
from ckan.logic import get_action
from ckan import model
from ckan.plugins import toolkit
from ckanext.scheming.helpers import lang

log = logging.getLogger(__name__)

_LOCALE_ALIASES = {'en_GB': 'en'}


def _markdown(translation, length):
    return (helpers.markdown_extract(translation, extract_length=length)
            if length is not True and isinstance(length, int)
            else helpers.render_markdown(translation))


def get_field(obj_or_dict, field, default=None):
    if isinstance(obj_or_dict, dict):
        return obj_or_dict.get(field, default)
    elif hasattr(obj_or_dict, field):
        return getattr(obj_or_dict, field)
    elif hasattr(obj_or_dict, 'extras'):
        return obj_or_dict.extras.get(field, default)
    else:
        return default


def get_translation(translated):
    if isinstance(translated, str):
        translated = get_json_value(translated)

    if isinstance(translated, dict):
        if flask.has_request_context():
            language = i18n.get_lang()
        else:
            language = ''

        if language in translated:
            return translated[language]
        dialects = [lang for lang in translated
                    if lang.startswith(language)
                    or language.startswith(lang)]
        if dialects:
            return translated[dialects[0]]
    return None


def get_translated(data_dict, field):
    translated_variant = '%s_translated' % field
    translated = get_field(data_dict, translated_variant)
    if translated:
        return get_translation(translated) or get_field(data_dict, field)
    else:
        get_field(data_dict, field)


# Copied from core ckan to call overridden get_translated
def dataset_display_name(package_or_package_dict):
    if isinstance(package_or_package_dict, dict):
        return get_translated(package_or_package_dict, 'title') or \
            package_or_package_dict['name']
    else:
        # FIXME: we probably shouldn't use the same functions for
        # package dicts and real package objects
        return package_or_package_dict.title or package_or_package_dict.name


def group_title_by_id(group_id):
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    group_details = get_action('group_show')(context, {"id": group_id, 'include_users': False,
                                                       'include_dataset_count': False,
                                                       'include_groups': False,
                                                       'include_tags': False,
                                                       'include_followers': False})
    return get_translated(group_details, 'title')


# Copied from core ckan to call overridden get_translated
def resource_display_name(resource_dict):
    # TODO: (?) support resource objects as well
    name = get_translated(resource_dict, 'name')
    description = get_translated(resource_dict, 'description')
    if name:
        return name
    elif description:
        description = description.split('.')[0]
        max_len = 60
        if len(description) > max_len:
            description = description[:max_len] + '...'
        return description
    else:
        return _("Unnamed resource")


def extra_translation(values, field, markdown=False, fallback=None):
    """ Used as helper. Get correct translation from extras (values) for given field.
        If markdown is True uses markdown rendering for value. If markdown is number use markdown_extract with given value.
        If fallback is set then use fallback as value if value is empty.
        If fallback is function then call given function with `values`.
    """
    translation = get_translated(values, field)

    if not translation and fallback:
        translation = fallback(values) if hasattr(fallback, '__call__') else fallback

    return _markdown(translation, markdown) if markdown and translation else translation


def get_dict_tree_from_json(fileurl_variable_name):
    """ Parse a JSON file and return it for constructing UI trees. """

    file_url = toolkit.config.get(fileurl_variable_name, None)
    if file_url:
        return json.load(urllib.request.urlopen(file_url))
    else:
        return []


def render_date(datetime_):
    if not isinstance(datetime_, datetime.datetime):
        return None
    return "%02d.%02d.%02d" % (datetime_.day, datetime_.month, datetime_.year)


def service_database_enabled():
    return toolkit.config.get('ckanext.ytp.service_database_enabled', 'true') == 'true'


def get_json_value(value):
    """ Get value as JSON. If value is not in JSON format return the given value """
    try:
        return json.loads(value)
    except ValueError:
        return value


def get_tooltip_content_types(lang=None):
    """ Fetches the  """
    content_types_file = os.path.dirname(os.path.realpath(__file__)) + '/content_types.json'

    if not lang:
        try:
            lang = helpers.lang()
        except TypeError:
            lang = "fi"

    with open(content_types_file) as types:
        ct = json.load(types)

    return ct.get(lang)


def sort_datasets_by_state_priority(datasets):
    """ Sorts the given list of datasets so that drafts appear first and deleted ones last.
    Also secondary sorts by modification date, latest first. """

    sorted_datasets = []
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state'] == 'draft'],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state'] not in ['draft', 'deleted']],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    sorted_datasets.extend(sorted([dataset for dataset in datasets if dataset['state'] == 'deleted'],
                                  key=lambda sorting_key: sorting_key['metadata_modified'], reverse=True))
    return sorted_datasets


def get_facet_item_count(facet):
    if c.search_facets.get(facet):
        items = c.search_facets.get(facet)['items']
        return len(items)
    return 0


def get_remaining_facet_item_count(facet, limit=10):
    if c.search_facets.get(facet):
        items = c.search_facets.get(facet)['items']
        return len(items) - 1 - limit
    return 0


def sort_facet_items_by_name(items):
    sorted_items = []
    sorted_items.extend(sorted([item for item in items if item['active'] is True],
                               key=lambda item: (-item['count'], item['display_name'])))
    sorted_items.extend(sorted([item for item in items if item['active'] is False],
                               key=lambda item: (-item['count'], item['display_name'])))
    return sorted_items


def sort_facet_items_by_count(items):
    sorted_items = []
    sorted_items.extend(sorted([item for item in items], key=lambda item: (-item['count'], item['display_name'])))
    return sorted_items


def get_sorted_facet_items_dict(facet, limit=50, exclude_active=False):
    if not c.search_facets or \
            not c.search_facets.get(facet) or \
            not c.search_facets.get(facet).get('items'):
        return []
    facets = []
    for facet_item in c.search_facets.get(facet)['items']:
        if not len(facet_item['name'].strip()):
            continue
        if not (facet, facet_item['name']) in list(request.params.items()):
            facets.append(dict(active=False, **facet_item))
        elif not exclude_active:
            facets.append(dict(active=True, **facet_item))
    sorted_items = []
    sorted_items.extend(sorted([item for item in facets if item['active'] is True],
                               key=lambda item: item['display_name'].lower()))
    sorted_items.extend(sorted([item for item in facets if item['active'] is False],
                               key=lambda item: item['display_name'].lower()))

    # Use function default limit instead of c.search_facets_limits
    if limit:
        return sorted_items[:limit]
    else:
        return sorted_items


def calculate_dataset_stars(dataset_id):
    from ckan.logic import NotFound

    if not is_plugin_enabled('qa'):
        return (0, '', '')
    try:
        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        qa = get_action('qa_package_openness_show')(context, {'id': dataset_id})

    except NotFound:
        return (0, '', '')
    if not qa:
        return (0, '', '')
    if qa['openness_score'] is None:
        return (0, '', '')

    return (qa['openness_score'],
            qa['openness_score_reason'],
            qa['updated'])


def calculate_metadata_stars(dataset_id):
    """
        Calculate the metadata quality.

        The rating is based on 4 criteria:
            - Field completeness (required / optional) 5 + 5 points
            - More than 50 visits 3 points
            - More than 20 Resource downloads 2 points
            - Comment count: 0,5 points per comment. Max 5 points
            - English or Swedish translations for both title and description: 5 points

    """

    score = 0.0

    # Required fields, optional fields, and translated fields, that will be scored by completeness
    required_fields = ['collection_type', 'title', 'notes', 'tags', 'license_id', 'organization', 'content_type']
    optional_fields = ['valid_from', 'valid_till', 'extra_information',
                       'author', 'author_email', 'owner', 'maintainer', 'maintainer_email']
    translation_fields_en = ['title_en', 'notes_en']
    translation_fields_sv = ['title_sv', 'notes_sv']

    context = {'model': model, 'session': model.Session}
    data = get_action('package_show')(context, {'id': dataset_id})

    # Check that all the required fields are present in the dataset
    if all(data.get(field) for field in required_fields if field is not None):
        score += 5

    # how many optional fields have data?
    optional_count = len(list(data.get(field) for field in optional_fields if data.get(field)))

    # max 5 points from filled optional fields
    score += (optional_count * 5.0 / len(optional_fields))

    # visits from GA
    visits = toolkit.h.get_visits_for_dataset(dataset_id) if 'get_visits_for_dataset' in toolkit.h else 0
    visit_count = visits.get("count", 0)
    resource_download_count = visits.get("download_count", 0)

    if visit_count > 50:
        score += 2.5

    if resource_download_count > 20:
        score += 2.5

    # extras?

    # english translations
    if all(data.get(field) for field in translation_fields_en if data.get(field)):
        score += 5.0
    # swedish translations
    elif all(data.get(field) for field in translation_fields_sv if data.get(field)):
        score += 5.0

    return int(round((score / 5.0), 0))


def is_plugin_enabled(plugin_name):
    return plugin_name in toolkit.config.get('ckan.plugins', '').split()


def get_upload_size():
    size = toolkit.config.get('ckan.max_resource_size', 10)

    return size


def get_license(license_id):
    context = {}
    licenses = get_action('license_list')(context, {})

    for license_obj in licenses:
        license_obj_id = license_obj.get('id', None)
        print(license_obj)
        if license_obj_id and license_obj_id == license_id:
            return license_obj

    return None


def get_current_date():

    return datetime.datetime.now()


lang_map = {
    "fi": "fin",
    "sv": "swe",
    "en": "eng",
    "en_GB": "eng"
}


def get_geonetwork_link(uuid, organization, lang=None):
    link_stem = ""

    if organization == "suomen-ymparistokeskus":
        link_stem = "https://metadata.ymparisto.fi/dataset/{uuid}"
    else:
        if not lang:
            try:
                lang = helpers.lang()
            except TypeError:
                lang = "en"

        lang = lang_map[lang]
        link_stem = "https://www.paikkatietohakemisto.fi/geonetwork/srv/{lang}/catalog.search#/metadata/{uuid}"

    return link_stem.format(lang=lang, uuid=uuid)


def unquote_url(url):
    from urllib.parse import quote, unquote

    # leading slash may be interpreted as unicode marker, so remove temporarily
    if url[0:1] == '/':
        url = url[1:]

    unquoted = unquote(url)
    if not isinstance(unquoted, str):
        unquoted = unquoted.decode('utf8')

    try:
        unquoted.decode('ascii')
    except UnicodeEncodeError:
        # re-quote characters that should not be in a query string
        unquoted = quote(unquote(unquoted).encode('utf8'), '=&?')
    else:
        unquoted = unquoted.encode('ascii')

    return "/" + unquoted


def scheming_field_only_default_required(field, lang):

    if field and field.get('only_default_lang_required') and lang == toolkit.config.get('ckan.locale_default', 'en'):
        return True

    return False


def add_locale_to_source(kwargs, locale):
    copy = kwargs.copy()
    source = copy.get('data-module-source', None)
    if source:
        copy.update({'data-module-source': source + '_' + locale})
        return copy
    return copy


def scheming_language_text_or_empty(text, prefer_lang=None):
    """
    :param text: {lang: text} dict or text string
    :param prefer_lang: choose this language version if available
    Convert "language-text" to users' language by looking up
    language in dict or using gettext if not a dict
    """
    if not text:
        return ''

    if hasattr(text, 'get'):
        try:
            if prefer_lang is None:
                prefer_lang = lang()
        except TypeError:
            pass  # lang() call will fail when no user language available
        else:
            if prefer_lang in _LOCALE_ALIASES:
                prefer_lang = _LOCALE_ALIASES[prefer_lang]
            try:
                return text[prefer_lang]
            except KeyError:
                return ''

    t = _(text)
    if isinstance(t, str):
        return t.decode('utf-8')
    return t


def get_lang_prefix():
    language = i18n.get_lang()
    if language in _LOCALE_ALIASES:
        language = _LOCALE_ALIASES[language]

    return language


def call_toolkit_function(fn, args, kwargs):
    return getattr(toolkit, fn)(*args, **kwargs)


def get_label_for_producer(producer_type):
    return {
        "state-administration": "State administration",
        "country": "Country",
        "region": "Region",
        "public-service": "Public service",
        "cities": "Cities",
        "education-research": "Education - Research",
        "enterprise": "Enterprise",
        "society-trust": "Society - Trust",
        "person": "Person"
    }.get(producer_type, '')


def scheming_category_list(args):
    from ckan.logic import NotFound
    # FIXME: sometimes this might return 0 categories if in development

    try:
        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        group_ids = get_action('group_list')(context, {})
    except NotFound:
        return None
    else:
        category_list = []

        # filter groups to those user is allowed to edit
        group_authz = get_action('group_list_authz')({
            'model': model, 'session': model.Session, 'user': c.user
        }, {})

        user_group_ids = set(group['name'] for group in group_authz)
        group_ids = [group for group in group_ids if group in user_group_ids]

        for group in group_ids:
            try:
                context = {'model': model, 'session': model.Session, 'ignore_auth': True}
                group_details = get_action('group_show')(context, {'id': group, 'include_users': False,
                                                                   'include_dataset_count': False,
                                                                   'include_groups': False,
                                                                   'include_tags': False,
                                                                   'include_followers': False})
            except Exception as e:
                log.error(e)
                return None

            category_list.append({
                "value": group,
                "label": group_details.get('title_translated')
            })

    return category_list


def check_group_selected(val, data):
    if [x for x in data if x['name'] == val]:
        return True
    return False


def is_boolean_selected(value, selected):
    try:
        return toolkit.asbool(value) is toolkit.asbool(selected)
    except ValueError:
        return


# Get a list of groups and add a selected field which is
# true if they are selected in the dataset
def group_list_with_selected(package_groups):
    if not isinstance(package_groups, list):
        package_groups = []

    # Get list of groups in avoindata
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    all_groups = get_action('group_list')(
        context,
        {"all_fields": True, "include_extras": True},
    )

    # filter groups to those user is allowed to edit
    group_authz = get_action('group_list_authz')({
        'model': model, 'session': model.Session, 'user': c.user
    }, {})

    user_group_ids = set(group['id'] for group in group_authz)
    all_groups = [group for group in all_groups if group['id'] in user_group_ids]

    # Check which groups are selected
    groups_with_selected = []
    for group in all_groups:
        selected = False
        for package_group in package_groups:
            if package_group['id'] == group['id']:
                selected = True
                break
        group.update({"selected": selected})
        groups_with_selected.append(group)

    return groups_with_selected


def get_last_harvested_date(organization_name):

    organization = get_action('organization_show')({}, {'id': organization_name,
                                                        'include_users': False,
                                                        'include_dataset_count': False,
                                                        'include_groups': False,
                                                        'include_tags': False,
                                                        'include_followers': False})

    # if added by harvester to organization
    if not organization.get('last_harvested'):
        data_dict = {
            'fq': "dataset_type:harvest"
        }

        harvest_sources = get_action('package_search')({}, data_dict)['results']

        related_harvest_objects = [source for source in harvest_sources if source.get('owner_org') == organization_name]
        finished_jobs = [finished_source for finished_source in itertools.chain.from_iterable(
            [get_action('harvest_job_list')({'ignore_auth': True}, {'source_id': source['id'], 'status': "Finished"})
             for source in related_harvest_objects]) if finished_source.get('finished')]

        if finished_jobs:
            latest = max(finished_jobs, key=lambda item: datetime.datetime.strptime(item['finished'], "%Y-%m-%d %H:%M:%S.%f"))
            harvest_source = get_action('harvest_source_show')({}, {'id': latest['source_id']})
            return {"source": harvest_source, "date": datetime.datetime.strptime(latest['finished'], "%Y-%m-%d %H:%M:%S.%f")}
        else:
            return

    return {"source": {'title': organization.get("last_harvested_harvester")}, "date": organization.get('last_harvested')}


def get_resource_sha256(resource_id):
    context = {'model': model, 'session': model.Session, 'user': c.user}
    return get_action('resource_status')(context, {'id': resource_id}).get('sha256') or _('-')


def get_package_showcase_list(package_id):
    context = {'model': model, 'session': model.Session, 'user': c.user}
    return get_action('ckanext_package_showcase_list')(context, {'package_id': package_id})


def get_groups_where_user_is_admin():
    context = {'model': model, 'session': model.Session, 'user': c.user}
    return get_action('organization_list_for_user')(context, {'permission': 'admin'})


def get_value_from_extras_by_key(object_with_extras, key):
    extras = object_with_extras.get('extras', [])

    for k, v in [(extra['key'], extra['value']) for extra in extras]:
        if k == key:
            return v

    return None


def get_field_from_dataset_schema(schema, field_name):

    field = next(field for field in schema.get('dataset_fields', []) if field.get('field_name') == field_name)
    return field


def get_field_from_resource_schema(schema, field_name):

    field = next(field for field in schema.get('resource_fields', []) if field.get('field_name') == field_name)
    return field


def site_url_with_root_path():
    site_url = toolkit.config.get('ckan.site_url')
    root_path = toolkit.config.get('ckan.root_path')

    if site_url and root_path:
        return site_url + root_path.replace('{{LANG}}', '').rstrip('/')
    else:
        return site_url.rstrip('/')


def get_organization_filters_count():
    organizations = get_action('organization_list')({}, {'all_fields': False})
    organizations_with_datasets = (get_action('organization_tree_list')({}, {'with_datasets': True})
                                   .get('global_results', []))

    with_dataset_count = len(organizations_with_datasets)
    all_count = len(organizations)

    return {'with_dataset_count': with_dataset_count, 'all_count': all_count}
