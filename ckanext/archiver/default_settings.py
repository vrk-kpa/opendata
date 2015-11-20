from pylons import config

# directory to save downloaded files to
ARCHIVE_DIR = config.get('ckanext-archiver.archive_dir', '/tmp/archive')

# Max content-length of archived files, larger files will be ignored
MAX_CONTENT_LENGTH = int(config.get('ckanext-archiver.max_content_length',
                                    50000000))

USER_AGENT_STRING = config.get('ckanext-archiver.user_agent_string', None)
if not USER_AGENT_STRING:
    USER_AGENT_STRING = '%s %s ckanext-archiver' % (
        config.get('ckan.site_title', ''), config.get('ckan.site_url'))
