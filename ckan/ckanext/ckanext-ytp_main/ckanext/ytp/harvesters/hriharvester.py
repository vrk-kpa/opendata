# -*- coding: utf-8 -*-

import urllib
import datetime
import socket
import re

from sqlalchemy import exists

from ckan import model
from ckan.logic import ValidationError, NotFound, get_action
from ckan.lib.helpers import json
from ckan.lib.munge import munge_name
from ckan.plugins import toolkit

from ckanext.harvest.model import HarvestJob, HarvestObject, HarvestGatherError
from ckanext.harvest.harvesters.base import HarvesterBase

import logging
log = logging.getLogger(__name__)

VALID_TAG_CHARACTERS = 'abcdefghijklmnopqrstuvwxyzåäö ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ1234567890-_.'
IS_INVALID_TAG_CHARACTER = re.compile('[^%s]' % VALID_TAG_CHARACTERS)
IS_VALID_TAG = re.compile('^"?([%s]*)"?$' % VALID_TAG_CHARACTERS)
IS_TAG_SET = re.compile('^{(.*)}$')
MINIMUM_TAG_LENGTH = 3
DATETIME_FORMATS = [
    '%Y-%m-%dT%H:%M:%S.%f%z',
    '%Y-%m-%dT%H:%M:%S%z',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%dT%H',
    '%Y-%m-%d',
    '%Y-%m',
    '%Y',
]


class HRIHarvester(HarvesterBase):
    '''
    A Harvester for CKAN instances
    '''
    config = None

    api_version = 2
    action_api_version = 3

    def _parse_tag(self, tag_string):
        if len(tag_string) < MINIMUM_TAG_LENGTH:
            return ''

        valid = IS_VALID_TAG.match(tag_string)
        if valid:
            return valid.group(1)

        modified = IS_INVALID_TAG_CHARACTER.sub('', tag_string)
        if len(modified) < MINIMUM_TAG_LENGTH:
            return ''
        else:
            return modified

    def _parse_tag_string(self, tag_string):
        tag_set = IS_TAG_SET.match(tag_string)
        if tag_set:
            tags = (t for t in tag_set.group(1).split(',') if t)
        else:
            tags = [tag_string]
        return [self._parse_tag(t) for t in tags]

    def _parse_datetime(self, datetime_string):
        if not datetime_string:
            return None

        for fmt in DATETIME_FORMATS:
            try:
                result = datetime.datetime.strptime(datetime_string, fmt)
            except Exception:
                continue
            return result

        log.debug('Invalid datetime string: "%s"' % datetime_string)
        return None

    def _get_action_api_offset(self):
        return '/api/%d/action' % self.action_api_version

    def _get_search_api_offset(self):
        return '%s/package_search' % self._get_action_api_offset()

    def _get_content(self, url):
        http_request = urllib.request.Request(url=url)

        api_key = self.config.get('api_key')
        if api_key:
            http_request.add_header('Authorization', api_key)

        try:
            http_response = urllib.request.urlopen(http_request)
        except urllib.error.HTTPError as e:
            if e.getcode() == 404:
                raise ContentNotFoundError('HTTP error: %s' % e.code)
            else:
                raise ContentFetchError('HTTP error: %s' % e.code)
        except urllib.error.URLError as e:
            raise ContentFetchError('URL error: %s' % e.reason)
        except urllib.error.HTTPException as e:
            raise ContentFetchError('HTTP Exception: %s' % e)
        except socket.error as e:
            raise ContentFetchError('HTTP socket error: %s' % e)
        except Exception as e:
            raise ContentFetchError('HTTP general exception: %s' % e)
        return http_response.read()

    def _get_group(self, base_url, group_name):
        url = base_url + self._get_action_api_offset() + '/group_show?id=' + \
            munge_name(group_name)
        try:
            content = self._get_content(url)
            return json.loads(content)
        except (ContentFetchError, ValueError):
            log.debug('Could not fetch/decode remote group')
            raise RemoteResourceError('Could not fetch/decode remote group')

    def _get_organization(self, base_url, org_name):
        url = base_url + self._get_action_api_offset() + \
            '/organization_show?id=' + org_name
        try:
            content = self._get_content(url)
            content_dict = json.loads(content)
            return content_dict['result']
        except (ContentFetchError, ValueError, KeyError):
            log.debug('Could not fetch/decode remote group')
            raise RemoteResourceError(
                'Could not fetch/decode remote organization')

    def _set_config(self, config_str):
        if config_str:
            self.config = json.loads(config_str)
            if 'api_version' in self.config:
                self.api_version = int(self.config['api_version'])

            log.debug('Using config: %r', self.config)
        else:
            self.config = {}

    def info(self):
        return {
            'name': 'hri',
            'title': 'HRI',
            'description': 'Harvests hri.fi',
            'form_config_interface': 'Text'
        }

    def validate_config(self, config):
        if not config:
            return config

        try:
            config_obj = json.loads(config)

            if 'api_version' in config_obj:
                try:
                    int(config_obj['api_version'])
                except ValueError:
                    raise ValueError('api_version must be an integer')

            if 'default_tags' in config_obj:
                if not isinstance(config_obj['default_tags'], list):
                    raise ValueError('default_tags must be a list')

            if 'default_groups' in config_obj:
                if not isinstance(config_obj['default_groups'], list):
                    raise ValueError('default_groups must be a list')

                # Check if default groups exist
                context = {'model': model, 'user': toolkit.g.user}
                for group_name in config_obj['default_groups']:
                    try:
                        get_action('group_show')(context, {'id': group_name})
                    except NotFound:
                        raise ValueError('Default group not found')

            if 'default_extras' in config_obj:
                if not isinstance(config_obj['default_extras'], dict):
                    raise ValueError('default_extras must be a dictionary')

            if 'user' in config_obj:
                # Check if user exists
                context = {'model': model, 'user': toolkit.g.user}
                try:
                    get_action('user_show')(context, {'id': config_obj.get('user')})
                except NotFound:
                    raise ValueError('User not found')

            for key in ('read_only', 'force_all'):
                if key in config_obj:
                    if not isinstance(config_obj[key], bool):
                        raise ValueError('%s must be boolean' % key)

        except ValueError as e:
            raise e

        return config

    def gather_stage(self, harvest_job):
        log.debug('In HRIHarvester gather_stage (%s)',
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

        # Ideally we can request from the remote CKAN only those datasets
        # modified since the last completely successful harvest.
        last_error_free_job = self._last_error_free_job(harvest_job)
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
                return None

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
            return None

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
                package_ids.add(pkg_dict['id'])

                log.debug('Creating HarvestObject for %s %s',
                          pkg_dict['name'], pkg_dict['id'])
                obj = HarvestObject(guid=pkg_dict['id'],
                                    job=harvest_job,
                                    content=json.dumps(pkg_dict))
                obj.save()
                object_ids.append(obj.id)

            return object_ids
        except Exception as e:
            self._save_gather_error('%r' % e.message, harvest_job)

    def _search_for_datasets(self, remote_ckan_base_url, fq_terms=None):
        '''Does a dataset search on a remote CKAN and returns the results.
        Deals with paging to return all the results, not just the first page.
        '''
        base_search_url = remote_ckan_base_url + self._get_search_api_offset()
        params = {'rows': '100', 'start': '0'}
        # There is the worry that datasets will be changed whilst we are paging
        # through them.
        # * In SOLR 4.7 there is a cursor, but not using that yet
        #   because few CKANs are running that version yet.
        # * However we sort, then new names added or removed before the current
        #   page would cause existing names on the next page to be missed or
        #   double counted.
        # * Another approach might be to sort by metadata_modified and always
        #   ask for changes since (and including) the date of the last item of
        #   the day before. However if the entire page is of the exact same
        #   time, then you end up in an infinite loop asking for the same page.
        # * We choose a balanced approach of sorting by ID, which means
        #   datasets are only missed if some are removed, which is far less
        #   likely than any being added. If some are missed then it is assumed
        #   they will harvested the next time anyway. When datasets are added,
        #   we are at risk of seeing datasets twice in the paging, so we detect
        #   and remove any duplicates.
        params['sort'] = 'id asc'
        if fq_terms:
            params['fq'] = ' '.join(fq_terms)

        pkg_dicts = []
        pkg_ids = set()
        previous_content = None
        while True:
            url = base_search_url + '?' + urllib.parse.urlencode(params)
            log.debug('Searching for CKAN datasets: %s', url)
            try:
                content = self._get_content(url)
            except ContentFetchError as e:
                raise SearchError(
                    'Error sending request to search remote '
                    'CKAN instance %s using URL %r. Error: %s' %
                    (remote_ckan_base_url, url, e))

            if previous_content and content == previous_content:
                raise SearchError('The paging doesn\'t seem to work. URL: %s' %
                                  url)
            try:
                response_dict = json.loads(content)
            except ValueError:
                raise SearchError('Response from remote CKAN was not JSON: %r'
                                  % content)
            try:
                pkg_dicts_page = response_dict.get('result', {}).get('results',
                                                                     [])
            except ValueError:
                raise SearchError('Response JSON did not contain '
                                  'result/results: %r' % response_dict)

            # Weed out any datasets found on previous pages (should datasets be
            # changing while we page)
            ids_in_page = set(p['id'] for p in pkg_dicts_page)
            duplicate_ids = ids_in_page & pkg_ids
            if duplicate_ids:
                pkg_dicts_page = [p for p in pkg_dicts_page
                                  if p['id'] not in duplicate_ids]
            pkg_ids |= ids_in_page

            pkg_dicts.extend(pkg_dicts_page)

            if len(pkg_dicts_page) == 0:
                break

            params['start'] = str(int(params['start']) + int(params['rows']))

        return pkg_dicts

    @classmethod
    def _last_error_free_job(cls, harvest_job):
        # TODO weed out cancelled jobs somehow.
        # look for jobs with no gather errors
        jobs = \
            model.Session.query(HarvestJob) \
            .filter(HarvestJob.source == harvest_job.source) \
            .filter(HarvestJob.gather_started is not None) \
            .filter(HarvestJob.status == 'Finished') \
            .filter(HarvestJob.id != harvest_job.id) \
            .filter(
                ~exists().where(
                    HarvestGatherError.harvest_job_id == HarvestJob.id)) \
            .order_by(HarvestJob.gather_started.desc())
        # now check them until we find one with no fetch/import errors
        # (looping rather than doing sql, in case there are lots of objects
        # and lots of jobs)
        for job in jobs:
            for obj in job.objects:
                if obj.current is False and \
                        obj.report_status != 'not modified':
                    # unsuccessful, so go onto the next job
                    break
            else:
                return job

    def fetch_stage(self, harvest_object):
        # Nothing to do here - we got the package dict in the search in the
        # gather stage
        return True

    def import_stage(self, harvest_object):
        log.debug('In HRIHarvester import_stage')

        context = {'model': model, 'session': model.Session,
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

            if package_dict.get('type') == 'harvest':
                log.warn('Remote dataset is a harvest source, ignoring...')
                return True

            # Set default translations
            lang = toolkit.config['ckan.locale_default']

            def translated_field(name):
                translated = package_dict.get('%s_translated' % name, {})
                translated[lang] = translated.get(lang, package_dict[name])
                # Process translations added as extras
                translated.update((e['key'].split('_', 2)[1], e['value'])
                                  for e in package_dict.get('extras', [])
                                  if e['key'].startswith('%s_' % name))
                return translated

            def translated_extra_list(name):
                translated = {lang: []}
                for x in package_dict.get('extras', []):
                    if x['key'] == name and len(x['value']) > 2:
                        translated[lang] = [x['value']]

                package_dict['extras'] = [x for x in package_dict.get('extras', []) if x['key'] != name]
                return translated

            package_dict['title_translated'] = translated_field('title')
            package_dict['notes_translated'] = translated_field('notes')
            package_dict['update_frequency'] = translated_extra_list('update_frequency')

            # Set default values for required fields
            default_values = {
                'maintainer': package_dict.get('author') or '(not set)',
                'maintainer_email': package_dict.get('author_email') or '(not set)',
            }
            missing_values = (
                (k, v) for k, v in default_values.items()
                if not package_dict.get(k))
            package_dict.update(missing_values)

            # Set default tags if needed
            default_tags = self.config.get('default_tags', [])
            if default_tags:
                if 'tags' not in package_dict:
                    package_dict['tags'] = []
                package_dict['tags'].extend(
                    [t for t in default_tags if t not in package_dict['tags']])

            keywords = package_dict.get('keywords', {})
            keywords[lang] = keywords.get(lang, [x['name'] for x in package_dict['tags']])
            package_dict['keywords'] = keywords

            remote_groups = self.config.get('remote_groups', None)
            if remote_groups not in ('only_local', 'create'):
                # Ignore remote groups
                package_dict.pop('groups', None)
            else:
                if 'groups' not in package_dict:
                    package_dict['groups'] = []

                # check if remote groups exist locally, otherwise remove
                validated_groups = []

                for group_name in package_dict['groups']:
                    try:
                        data_dict = {'id': group_name}
                        group = get_action('group_show')(context, data_dict)
                        if self.api_version == 1:
                            validated_groups.append(group['name'])
                        else:
                            validated_groups.append(group['id'])
                    except NotFound:
                        log.info('Group %s is not available', group_name)
                        if remote_groups == 'create':
                            try:
                                group = self._get_group(harvest_object.source.url, group_name)
                            except RemoteResourceError:
                                log.error('Could not get remote group %s', group_name)
                                continue

                            for key in ['packages', 'created', 'users', 'groups', 'tags', 'extras', 'display_name']:
                                group.pop(key, None)

                            get_action('group_create')(context, group)
                            log.info('Group %s has been newly created', group_name)
                            if self.api_version == 1:
                                validated_groups.append(group['name'])
                            else:
                                validated_groups.append(group['id'])

                package_dict['groups'] = validated_groups

            # Find if remote org exists locally, otherwise don't import dataset
            if 'owner_org' not in package_dict:
                package_dict['owner_org'] = None

            remote_org = None
            if package_dict.get('organization'):
                remote_org = package_dict['organization']['name']

            if remote_org:
                try:
                    data_dict = {'id': remote_org}
                    org = get_action('organization_show')(context, data_dict)
                    package_dict['owner_org'] = org['id']
                except NotFound:
                    log.info('No organization exist, not importing dataset')
                    return "unchanged"
            else:
                log.info('No organization in harvested dataset')
                return "unchanged"

            # Set default groups if needed
            default_groups = self.config.get('default_groups', [])
            if default_groups:
                if 'groups' not in package_dict:
                    package_dict['groups'] = []
                package_dict['groups'].extend(
                    [g for g in default_groups
                     if g not in package_dict['groups']])

            # Map fields
            fields_to_map = [('url', 'maintainer_website')]
            for key_from, key_to in fields_to_map:
                if key_to not in package_dict and key_from in package_dict:
                    package_dict[key_to] = package_dict[key_from]

            # Rename extras
            extras_to_rename_keys = {
                'geographic_coverage': 'geographical_coverage',
                'temporal_coverage-from': 'valid_from',
                'temporal_coverage-to': 'valid_till',
                'source': 'owner'
            }

            def map_extra(e):
                result = {}
                result.update(e)
                result['key'] = extras_to_rename_keys.get(e['key'], e['key'])
                return result

            package_dict['extras'] = [map_extra(extra) for extra in package_dict.get('extras', [])]

            # Set default extras if needed
            default_extras = self.config.get('default_extras', {})

            def get_extra(key, package_dict):
                for extra in package_dict.get('extras', []):
                    if extra['key'] == key:
                        return extra
            if default_extras:
                override_extras = self.config.get('override_extras', False)
                if 'extras' not in package_dict:
                    package_dict['extras'] = {}
                for key, value in default_extras.items():
                    existing_extra = get_extra(key, package_dict)
                    if existing_extra and not override_extras:
                        continue  # no need for the default
                    if existing_extra:
                        package_dict['extras'].remove(existing_extra)
                    # Look for replacement strings
                    if isinstance(value, str):
                        value = value.format(
                            harvest_source_id=harvest_object.job.source.id,
                            harvest_source_url=harvest_object.job.source.url.strip('/'),
                            harvest_source_title=harvest_object.job.source.title,
                            harvest_job_id=harvest_object.job.id,
                            harvest_object_id=harvest_object.id,
                            dataset_id=package_dict['id'])

                    package_dict['extras'].append({'key': key, 'value': value})

            # Convert extras from strings to datetimes
            extras_to_datetimes = ['valid_from', 'valid_till']

            def map_extra_to_date(e):
                if e['key'] not in extras_to_datetimes:
                    return e
                result = {}
                result.update(e)
                result['value'] = self._parse_datetime(e['value'])
                return result

            package_dict['extras'] = [map_extra_to_date(extra) for extra in package_dict.get('extras', [])]

            # Move extras to fields
            extras_to_fields_keys = ['collection_type', 'geographical_coverage', 'valid_from', 'valid_till', 'owner']
            extras_to_fields = [
                x for x in package_dict.get('extras', [])
                if x['key'] in extras_to_fields_keys
                and x['key'] not in package_dict]

            for x in extras_to_fields:
                package_dict[x['key']] = x['value']

            package_dict['extras'] = [x for x in package_dict.get('extras', []) if x['key'] not in extras_to_fields_keys]

            for resource in package_dict.get('resources', []):
                # Clear remote url_type for resources (eg datastore, upload) as
                # we are only creating normal resources with links to the
                # remote ones
                resource.pop('url_type', None)

                # Clear revision_id as the revision won't exist on this CKAN
                # and saving it will cause an IntegrityError with the foreign
                # key.
                resource.pop('revision_id', None)

            # Ensure imported tags are valid
            tag_string_fields = ['geographical_coverage']
            for field in tag_string_fields:
                package_dict[field] = [t
                                       for t in self._parse_tag_string(package_dict.get(field, ''))
                                       if t]

            # Create or update package
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
