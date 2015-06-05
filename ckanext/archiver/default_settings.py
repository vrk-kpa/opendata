from pylons import config

import ckan.plugins.toolkit as t

# directory to save downloaded files to
ARCHIVE_DIR = config.get('ckanext-archiver.archive_dir', '/tmp/archive')

# Max content-length of archived files, larger files will be ignored
MAX_CONTENT_LENGTH = int(config.get('ckanext-archiver.max_content_length', 50000000))

# Only files with these mime-types or extensions will be archived.
# To archive all files, set DATA_FORMATS = 'all'
DEFAULT_DATA_FORMATS = [
    'csv',
    'text/csv',
    'txt',
    'text/plain',
    'text/html',
    'html',
    'rdf',
    'text/rdf',
    'xml',
    'xls',
    'application/ms-excel',
    'application/vnd.ms-excel',
    'application/xls',
    'text/xml',
    'tar',
    'application/x-tar',
    'zip',
    'application/zip'
    'gz',
    'application/gzip',
    'application/x-gzip',
    'application/octet-stream'
]
DATA_FORMATS = config.get['ckanext-archiver.data_formats'].split() if 'ckan-archiver.data_formats' in config else DEFAULT_DATA_FORMATS

USER_AGENT_STRING = config.get('ckanext.archiver.user_agent_string', None)
