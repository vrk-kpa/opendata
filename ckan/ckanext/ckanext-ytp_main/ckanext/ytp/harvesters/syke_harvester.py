

import datetime
import six
from ckan import model
from ckan.lib.helpers import json, date_str_to_datetime
from ckan.plugins import toolkit
from ckan.logic import ValidationError, NotFound, get_action
from ckan.lib.munge import munge_tag
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.ckanharvester import CKANHarvester
import ckan.lib.plugins as lib_plugins

import logging
log = logging.getLogger(__name__)


_category_mapping = {
    'alueet-ja-kaupungit': ['boundaries', 'planningCadastre', 'imageryBaseMapsEarthCover', 'location'],
    'liikenne': ['transportation'],
    'maatalous-kalastus-metsatalous-ja-elintarvikkeet': ['farming'],
    'oikeus-oikeusjarjestelma-ja-yleinen-turvallisuus': ['intelligenceMilitary'],
    'rakennettu-ymparisto-ja-infrastruktuuri': ['utilitiesCommunication', 'structure'],
    'talous-ja-rahoitus': ['economy'],
    'terveys': ['health'],
    'vaesto-ja-yhteiskunta': ['society'],
    'ymparisto-ja-luonto': ['climatologyMeteorologyAtmosphere', 'elevation', 'environment',
                            'geoscientificInformation', 'biota', 'inlandWaters', 'oceans']
}


class SYKEHarvester(CKANHarvester):

    def info(self):
        return {
            'name': 'syke',
            'title': 'SYKE',
            'description': 'Harvests remote CKAN instance of SYKE',
            'form_config_interface': 'Text'
        }

    def modify_package_dict(self, package_dict, harvest_object):

        package_dict['title_translated'] = {
            "fi": package_dict.get('title', '')
        }
        package_dict['notes_translated'] = {
            "fi": package_dict.get('notes', '')
        }

        package_dict['collection_type'] = 'Open Data'
        package_dict['license_id'] = 'cc-by-4.0'
        package_dict['maintainer_website'] = 'https://www.syke.fi'

        package_dict['resources'] = [
            dict(**resource, **{'name_translated': {'fi': resource.get('name')}})
            for resource in package_dict.get('resources', [])
        ]

        # Remove tags as we don't use them
        package_dict.pop('tags', None)

        extras = package_dict.get('extras', [])

        for k, v, i in [(extra['key'], extra['value'], i) for i, extra in enumerate(extras)]:

            if k == 'responsible-party':
                responsible_party = json.loads(v)[0]
                package_dict['maintainer'] = responsible_party.get('name', '')
                package_dict['maintainer_email'] = responsible_party.get('email', '')

            if k == 'keywords':
                keywords = [keywords.get('keyword', []) for keywords in json.loads(v)]
                parsed_keywords = [munge_tag(item) for sublist in keywords for item in sublist]
                package_dict['keywords'] = {
                    'fi': parsed_keywords
                }

                # Remove keywords from extras as same key cannot be in schema and in extras
                extras.pop(i)

            if k == 'lineage':
                package_dict['notes_translated']['fi'] += '\n\n' + v

            if k == 'use_constraints':
                package_dict['copyright_notice_translated'] = {
                    'fi': json.loads(v)[0]
                }

            if k == 'metadata-date':
                metadata_date_isoformat = "%s.000000" % date_str_to_datetime(v).isoformat().split('+', 2)[0]
                package_dict['date_released'] = metadata_date_isoformat

            if k == 'temporal-extent-begin':
                try:
                    package_dict['valid_from'] = date_str_to_datetime(v)
                except ValueError:
                    log.info("Invalid date for valid_from, ignoring..")
                    pass

            if k == 'temporal-extent-end':
                try:
                    package_dict['valid_until'] = date_str_to_datetime(v)
                except ValueError:
                    log.info("Invalid date for valid_until, ignoring..")
                    pass

            if k == 'topic-category':
                topic_categories = json.loads(v)
                categories = [category for topic_category in topic_categories
                              for category, iso_topic_categories in six.iteritems(_category_mapping)
                              if topic_category in iso_topic_categories]
                package_dict['categories'] = categories

        return package_dict

    def gather_stage(self, harvest_job):
        log.debug('In SYKEHarvester gather_stage (%s)',
                  harvest_job.source.url)
        toolkit.requires_ckan_version(min_version='2.0')
        get_all_packages = True

        self._set_config(harvest_job.source.config)

        # Get source URL
        remote_ckan_base_url = harvest_job.source.url.rstrip('/')

        # Filter in/out datasets from particular organizations
        fq_terms = []
        org_filter_include = self.config.get('organizations_filter_include', [])
        org_filter_exclude = self.config.get('organizations_filter_exclude', [])
        if org_filter_include:
            fq_terms.append(' OR '.join(
                'organization:%s' % org_name for org_name in org_filter_include))
        elif org_filter_exclude:
            fq_terms.extend(
                '-organization:%s' % org_name for org_name in org_filter_exclude)

        groups_filter_include = self.config.get('groups_filter_include', [])
        groups_filter_exclude = self.config.get('groups_filter_exclude', [])
        if groups_filter_include:
            fq_terms.append(' OR '.join(
                'groups:%s' % group_name for group_name in groups_filter_include))
        elif groups_filter_exclude:
            fq_terms.extend(
                '-groups:%s' % group_name for group_name in groups_filter_exclude)

        # Ideally we can request from the remote CKAN only those datasets
        # modified since the last completely successful harvest.
        last_error_free_job = self.last_error_free_job(harvest_job)
        log.debug('Last error-free job: %r', last_error_free_job)
        if (last_error_free_job and
                not self.config.get('force_all', False)):
            get_all_packages = False

            # Request only the datasets modified since
            last_time = last_error_free_job.gather_started
            # Note: SOLR works in UTC, and gather_started is also UTC, so
            # this should work as long as local and remote clocks are
            # relatively accurate. Going back a little earlier, just in case.
            get_changes_since = \
                (last_time - datetime.timedelta(hours=1)).isoformat()
            log.info('Searching for datasets modified since: %s UTC',
                     get_changes_since)

            fq_since_last_time = 'metadata_modified:[{since}Z TO *]' \
                .format(since=get_changes_since)

            try:
                pkg_dicts = self._search_for_datasets(
                    remote_ckan_base_url,
                    fq_terms + [fq_since_last_time])
            except SearchError as e:
                log.info('Searching for datasets changed since last time '
                         'gave an error: %s', e)
                get_all_packages = True

            if not get_all_packages and not pkg_dicts:
                log.info('No datasets have been updated on the remote '
                         'CKAN instance since the last harvest job %s',
                         last_time)
                return []

        # Fall-back option - request all the datasets from the remote CKAN
        if get_all_packages:
            # Request all remote packages
            try:
                pkg_dicts = self._search_for_datasets(remote_ckan_base_url,
                                                      fq_terms)
            except SearchError as e:
                log.info('Searching for all datasets gave an error: %s', e)
                self._save_gather_error(
                    'Unable to search remote CKAN for datasets:%s url:%s'
                    'terms:%s' % (e, remote_ckan_base_url, fq_terms),
                    harvest_job)
                return None
        if not pkg_dicts:
            self._save_gather_error(
                'No datasets found at CKAN: %s' % remote_ckan_base_url,
                harvest_job)
            return []
        
        deleted_ids = set()
        received_ids = set(str(p['id']) for p in pkg_dicts)
        existing_ids = set(row[0] for row in model.Session.query(HarvestObject.guid)
                            .filter(HarvestObject.current == True)  # noqa
                            .filter(HarvestObject.harvest_source_id == harvest_job.source_id))
        deleted_ids = existing_ids - received_ids

        # Create harvest objects for each dataset
        try:
            package_ids = set()
            object_ids = []
            for pkg_dict in pkg_dicts:
                if pkg_dict['id'] in package_ids:
                    log.info('Discarding duplicate dataset %s - probably due '
                             'to datasets being changed at the same time as '
                             'when the harvester was paging through',
                             pkg_dict['id'])
                    continue

                if 'CC BY 4.0' not in pkg_dict.get('notes', ""):
                    log.info("Not under CC BY 4.0 license, skipping..")
                    continue
                package_ids.add(pkg_dict['id'])

                log.debug('Creating HarvestObject for %s %s',
                          pkg_dict['name'], pkg_dict['id'])
                obj = HarvestObject(guid=pkg_dict['id'],
                                    job=harvest_job,
                                    content=json.dumps(pkg_dict))
                obj.save()
                object_ids.append(obj.id)

            for deleted_id in deleted_ids:
                # Original harvest object needs to be updated
                log.debug('Creating deleting HarvestObject for %s', deleted_id)
                obj = model.Session.query(HarvestObject)\
                    .filter(
                    HarvestObject.current == True  # noqa
                )\
                    .filter(HarvestObject.guid == deleted_id).one()
                obj.job = harvest_job
                obj.content = '{"id":"%s", "delete":true}' % deleted_id
                obj.save()
                object_ids.append(obj.id)

            return object_ids
        except Exception as e:
            self._save_gather_error('%r' % e.message, harvest_job)

    def fetch_stage(self, harvest_object):
        # Nothing to do here - we got the package dict in the search in the
        # gather stage
        return True

    def import_stage(self, harvest_object):
        log.debug('In CKANHarvester import_stage')

        base_context = {'model': model, 'session': model.Session,
                        'user': self._get_user_name()}
        if not harvest_object:
            log.error('No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' %
                                    harvest_object.id,
                                    harvest_object, 'Import')
            return False

        self._set_config(harvest_object.job.source.config)

        try:
            package_dict = json.loads(harvest_object.content)

            if package_dict.get('delete', False):
                log.info('Deleting package %s' % package_dict['id'])
                toolkit.get_action('package_delete')(base_context.copy(), {'id': package_dict['id']})

                # Mark current to false, to mark it as deleted
                harvest_object.current = False
                return True

            if package_dict.get('type') == 'harvest':
                log.warn('Remote dataset is a harvest source, ignoring...')
                return True

            # Set default tags if needed
            default_tags = self.config.get('default_tags', [])
            if default_tags:
                if 'tags' not in package_dict:
                    package_dict['tags'] = []
                package_dict['tags'].extend(
                    [t for t in default_tags if t not in package_dict['tags']])

            remote_groups = self.config.get('remote_groups', None)
            if remote_groups not in ('only_local', 'create'):
                # Ignore remote groups
                package_dict.pop('groups', None)
            else:
                if 'groups' not in package_dict:
                    package_dict['groups'] = []

                # check if remote groups exist locally, otherwise remove
                validated_groups = []

                for group_ in package_dict['groups']:
                    try:
                        try:
                            if 'id' in group_:
                                data_dict = {'id': group_['id']}
                                group = get_action('group_show')(base_context.copy(), data_dict)
                            else:
                                raise NotFound

                        except NotFound:
                            if 'name' in group_:
                                data_dict = {'id': group_['name']}
                                group = get_action('group_show')(base_context.copy(), data_dict)
                            else:
                                raise NotFound
                        # Found local group
                        validated_groups.append({'id': group['id'], 'name': group['name']})

                    except NotFound:
                        log.info('Group %s is not available', group_)
                        if remote_groups == 'create':
                            try:
                                group = self._get_group(harvest_object.source.url, group_)
                            except RemoteResourceError:
                                log.error('Could not get remote group %s', group_)
                                continue

                            for key in ['packages', 'created', 'users', 'groups', 'tags', 'extras', 'display_name']:
                                group.pop(key, None)

                            get_action('group_create')(base_context.copy(), group)
                            log.info('Group %s has been newly created', group_)
                            validated_groups.append({'id': group['id'], 'name': group['name']})

                package_dict['groups'] = validated_groups

            # Local harvest source organization
            source_dataset = get_action('package_show')(base_context.copy(), {'id': harvest_object.source.id})
            local_org = source_dataset.get('owner_org')

            remote_orgs = self.config.get('remote_orgs', None)

            if remote_orgs not in ('only_local', 'create'):
                # Assign dataset to the source organization
                package_dict['owner_org'] = local_org
            else:
                if 'owner_org' not in package_dict:
                    package_dict['owner_org'] = None

                # check if remote org exist locally, otherwise remove
                validated_org = None
                remote_org = package_dict['owner_org']

                if remote_org:
                    try:
                        data_dict = {'id': remote_org}
                        org = get_action('organization_show')(base_context.copy(), data_dict)
                        validated_org = org['id']
                    except NotFound:
                        log.info('Organization %s is not available', remote_org)
                        if remote_orgs == 'create':
                            try:
                                try:
                                    org = self._get_organization(harvest_object.source.url, remote_org)
                                except RemoteResourceError:
                                    # fallback if remote CKAN exposes organizations as groups
                                    # this especially targets older versions of CKAN
                                    org = self._get_group(harvest_object.source.url, remote_org)

                                for key in ['packages', 'created', 'users', 'groups', 'tags',
                                            'extras', 'display_name', 'type']:
                                    org.pop(key, None)
                                get_action('organization_create')(base_context.copy(), org)
                                log.info('Organization %s has been newly created', remote_org)
                                validated_org = org['id']
                            except (RemoteResourceError, ValidationError):
                                log.error('Could not get remote org %s', remote_org)

                package_dict['owner_org'] = validated_org or local_org

            # Set default groups if needed
            default_groups = self.config.get('default_groups', [])
            if default_groups:
                if 'groups' not in package_dict:
                    package_dict['groups'] = []
                existing_group_ids = [g['id'] for g in package_dict['groups']]
                package_dict['groups'].extend(
                    [g for g in self.config['default_group_dicts']
                     if g['id'] not in existing_group_ids])

            # Set default extras if needed
            default_extras = self.config.get('default_extras', {})

            def get_extra(key, package_dict):
                for extra in package_dict.get('extras', []):
                    if extra['key'] == key:
                        return extra
            if default_extras:
                override_extras = self.config.get('override_extras', False)
                if 'extras' not in package_dict:
                    package_dict['extras'] = []
                for key, value in default_extras.items():
                    existing_extra = get_extra(key, package_dict)
                    if existing_extra and not override_extras:
                        continue  # no need for the default
                    if existing_extra:
                        package_dict['extras'].remove(existing_extra)
                    # Look for replacement strings
                    if isinstance(value, six.string_types):
                        value = value.format(
                            harvest_source_id=harvest_object.job.source.id,
                            harvest_source_url=harvest_object.job.source.url.strip('/'),
                            harvest_source_title=harvest_object.job.source.title,
                            harvest_job_id=harvest_object.job.id,
                            harvest_object_id=harvest_object.id,
                            dataset_id=package_dict['id'])

                    package_dict['extras'].append({'key': key, 'value': value})

            for resource in package_dict.get('resources', []):
                # Clear remote url_type for resources (eg datastore, upload) as
                # we are only creating normal resources with links to the
                # remote ones
                resource.pop('url_type', None)

                # Clear revision_id as the revision won't exist on this CKAN
                # and saving it will cause an IntegrityError with the foreign
                # key.
                resource.pop('revision_id', None)

            package_dict = self.modify_package_dict(package_dict, harvest_object)

            # validate packages if needed
            validate_packages = self.config.get('validate_packages', {})
            if validate_packages:
                if 'type' not in package_dict:
                    package_plugin = lib_plugins.lookup_package_plugin()
                    try:
                        # use first type as default if user didn't provide type
                        package_type = package_plugin.package_types()[0]
                    except (AttributeError, IndexError):
                        package_type = 'dataset'
                        # in case a 'dataset' plugin was registered w/o fallback
                        package_plugin = lib_plugins.lookup_package_plugin(package_type)
                    package_dict['type'] = package_type
                else:
                    package_plugin = lib_plugins.lookup_package_plugin(package_dict['type'])

                errors = {}
                # if package has been previously imported
                try:
                    existing_package_dict = self._find_existing_package(package_dict)

                    if 'metadata_modified' not in package_dict or \
                        package_dict['metadata_modified'] > existing_package_dict.get('metadata_modified'):
                        schema = package_plugin.update_package_schema()
                        data, errors = lib_plugins.plugin_validate(
                            package_plugin, base_context, package_dict, schema, 'package_update')

                except NotFound:

                    schema = package_plugin.create_package_schema()
                    data, errors = lib_plugins.plugin_validate(
                        package_plugin, base_context, package_dict, schema, 'package_create')

                if errors:
                    raise ValidationError(errors)

            result = self._create_or_update_package(
                package_dict, harvest_object, package_dict_form='package_show')

            return result
        except ValidationError as e:
            self._save_object_error('Invalid package with GUID %s: %r' %
                                    (harvest_object.guid, e.error_dict),
                                    harvest_object, 'Import')
        except Exception as e:
            self._save_object_error('%s' % e, harvest_object, 'Import')


class ContentFetchError(Exception):
    pass


class ContentNotFoundError(ContentFetchError):
    pass


class RemoteResourceError(Exception):
    pass


class SearchError(Exception):
    pass
