import ckan.plugins as p
from ckan.plugins.toolkit import config
from ckan.lib.plugins import DefaultTranslation
import ckan.logic as logic
from urllib.parse import urlparse
import os


class ResourceStatusPlugin(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.IActions, inherit=True)

    def get_actions(self):
        return {'resource_status': resource_status}


@logic.side_effect_free
def resource_status(context=None, data_dict=None):
    resource = logic.get_action('resource_show')(context, data_dict)

    if resource.get('url_type') != 'upload':
        return {'finished': True}

    sha256 = resource.get('sha256')
    status_updated = resource.get('status_updated')
    malware = resource.get('malware_check')
    finished = all(x not in (None, '') for x in (sha256, malware))

    if not finished:
        status = get_resource_status(resource)
        finished = all(x not in (None, '') for x in (sha256, malware))

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
            patch_context = {'ignore_auth': True, 'user': site_user['name']}
            logic.get_action('resource_patch')(patch_context, patch)

    return {'finished': finished,
            'clean': malware == 'clean' if malware is not None else None,
            'updated': status_updated,
            'sha256': sha256}


def get_resource_status(resource):
    if p.plugin_loaded('cloudstorage'):
        return CloudResourceStatus(resource)
    else:
        return ResourceStatus(resource)


class ResourceStatus(object):
    def __init__(self, resource):
        self.resource = resource

    def sha256(self):
        return None

    def malware(self):
        return None

    def updated(self):
        return None


class CloudResourceStatus(ResourceStatus):
    def __init__(self, resource):
        import boto3
        super(CloudResourceStatus, self).__init__(resource)
        aws_bucket_name = config.get('ckanext.cloudstorage.container_name')
        resource_id = resource.get('id')
        filename = os.path.basename(urlparse(resource.get('url')).path)
        object_key = 'resources/%s/%s' % (resource_id, filename)

        s3 = boto3.client('s3')
        tags_response = s3.get_object_tagging(Bucket=aws_bucket_name, Key=object_key)
        self.tags = {item['Key']: item['Value'] for item in tags_response['TagSet']}

    def sha256(self):
        return self.tags.get('sha256')

    def malware(self):
        return self.tags.get('malware')

    def updated(self):
        return self.tags.get('updated')
