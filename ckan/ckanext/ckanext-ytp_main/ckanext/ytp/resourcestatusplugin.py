import os
from logging import getLogger
from typing import Optional
from urllib.parse import urlparse

import ckan.logic as logic
import ckan.plugins as p
import yaml
from ckan.lib.plugins import DefaultTranslation
from ckan.plugins.toolkit import config

log = getLogger(__name__)

class ResourceStatusPlugin(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.IActions, inherit=True)
    p.implements(p.IResourceController, inherit=True)

    def get_actions(self) -> dict:
        return {'resource_status': resource_status}

    def before_resource_update(self, context: dict, current: dict, resource: dict) -> None:
        if not (context.get('upload_in_progress') or context.get('set_resource_status')):
            resource.pop('sha256', None)
            resource.pop('malware', None)

    # CKAN <2.10
    def before_update(self, context: dict, current: dict, resource: dict) -> None:
        self.before_resource_update(context, current, resource)

    def after_resource_update(self, context: dict, resource: dict) -> None:
        if not context.get('set_resource_status'):
            p.toolkit.get_action('resource_status')(context, {'id': resource["id"]})

    # CKAN <2.10
    def after_update(self, context: dict, resource: dict) -> None:
        self.after_resource_update(context, resource)


@logic.side_effect_free
def resource_status(context: dict, data_dict: dict) -> dict:
    resource = logic.get_action('resource_show')(context, data_dict)

    if resource.get('url_type') != 'upload':
        return {'finished': True}

    sha256 = resource.get('sha256')
    status_updated = resource.get('status_updated')
    malware = resource.get('malware_check')
    finished = (sha256 not in (None, '') and malware not in (None, ''))

    if not finished:
        try:
            status = get_resource_status(resource)
            patch = {}
            if status.sha256() is not None and status.sha256() != sha256:
                patch['sha256'] = status.sha256()
            if status.malware() is not None and status.malware() != malware:
                patch['malware_check'] = status.malware()
            if status.updated() is not None and status.updated() != status_updated:
                patch['status_updated'] = status.updated()
            if patch:
                patch['id'] = resource['id']
                site_user = logic.get_action('get_site_user')({'ignore_auth': True}, {})
                patch_context = {'ignore_auth': True,
                                 'user': site_user['name'],
                                 'set_resource_status': True}
                logic.get_action('resource_patch')(patch_context, patch)
            log.warning(f'Resource status updated successfully for resource {resource["id"]}.')
        except ResourceStatusUnavailableError:
            log.warning(f'Resource status not available for resource {resource["id"]}. Possibly an incomplete upload.')

    return {'finished': finished,
            'clean': malware == 'clean' if malware is not None else None,
            'updated': status_updated,
            'sha256': sha256}


class ResourceStatusUnavailableError(Exception):
    pass


class ResourceStatus(object):
    def __init__(self, resource: dict) -> None:
        self.resource = resource

    def sha256(self) -> Optional[str]:
        return None

    def malware(self) -> Optional[str]:
        return None

    def updated(self) -> Optional[str]:
        return None


def get_resource_status(resource: dict) -> ResourceStatus:
    if p.plugin_loaded('cloudstorage'):
        return CloudResourceStatus(resource)
    return ResourceStatus(resource)


class CloudResourceStatus(ResourceStatus):
    def __init__(self, resource: dict) -> None:
        import boto3
        super().__init__(resource)
        aws_bucket_name = config.get('ckanext.cloudstorage.container_name')
        resource_id = resource.get('id')
        filename = os.path.basename(urlparse(resource.get('url')).path)
        object_key = f'resources/{resource_id}/{filename}'

        driver_options = config.get('ckanext.cloudstorage.driver_options')
        if driver_options:
            driver_options = yaml.safe_load(driver_options)
            s3 = boto3.client('s3',
                aws_access_key_id=driver_options.get('key'),
                aws_secret_access_key=driver_options.get('secret'),
                aws_session_token=driver_options.get('token'))
        else:
            s3 = boto3.client('s3')

        try:
            tags_response = s3.get_object_tagging(Bucket=aws_bucket_name, Key=object_key)
            self.tags = {item['Key']: item['Value'] for item in tags_response['TagSet']}
        except s3.exceptions.NoSuchKey as e:
            raise ResourceStatusUnavailableError() from e

    def sha256(self) -> Optional[str]:
        return self.tags.get('sha256')

    def malware(self) -> Optional[str]:
        return self.tags.get('malware')

    def updated(self) -> Optional[str]:
        return self.tags.get('updated')
