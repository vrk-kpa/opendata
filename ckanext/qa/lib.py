import json

import ckan.model as model
import ckan.plugins as p

def get_site_url(config):
    return config.get('ckan.site_url_internally') or config['ckan.site_url']

def get_user_and_context(site_url):
    user = p.toolkit.get_action('get_site_user')(
        {'model': model, 'ignore_auth': True, 'defer_commit': True}, {}
        )
    context = json.dumps({
        'site_url': site_url,
        'apikey': user.get('apikey'),
        'site_user_apikey': user.get('apikey'),
        'username': user.get('name'),
        })
    return user, context
