

import datetime
import six
from ckan.lib.helpers import json, date_str_to_datetime
from ckan.plugins import toolkit
from ckan.lib.munge import munge_tag
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.ckanharvester import CKANHarvester

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
            dict(resource.items() + {'name_translated': {'fi': resource.get('name')}}.items())
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

            return object_ids
        except Exception as e:
            self._save_gather_error('%r' % e.message, harvest_job)


class ContentFetchError(Exception):
    pass


class ContentNotFoundError(ContentFetchError):
    pass


class RemoteResourceError(Exception):
    pass


class SearchError(Exception):
    pass
