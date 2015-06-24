from pylons import config

import ckan.plugins.toolkit as t

# directory to save downloaded files to
ARCHIVE_DIR = config.get('ckanext-archiver.archive_dir', '/tmp/archive')

# Max content-length of archived files, larger files will be ignored
MAX_CONTENT_LENGTH = int(config.get('ckanext-archiver.max_content_length', 50000000))
