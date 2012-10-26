import os

from pylons import config

from tasks import ArchiverError

def get_cached_resource_filepath(cache_url):
    '''Returns the filepath of the cached resource data file, calculated
    from its cache_url.

    Returns None if the resource has no cache.
    
    May raise ArchiverError for fatal errors.
    '''
    if not cache_url:
        return None
    if not cache_url.startswith(config['ckan.cache_url_root']):
        raise ArchiverError('Resource cache_url (%s) doesn\'t match the cache_url_root (%s)' % \
                      (cache_url, config['ckan.cache_url_root']))
    archive_dir = config['ckanext-archiver.archive_dir']
    if config['ckan.cache_url_root'].endswith('/') and not archive_dir.endswith('/'):
        archive_dir += '/'
    filepath = cache_url.replace(config['ckan.cache_url_root'],
                                 archive_dir)
    if not os.path.exists(filepath):
        raise ArchiverError('Local cache file does not exist: %s' % filepath)
    return filepath
