# directory to save downloaded files to
ARCHIVE_DIR = '/tmp/archive'

# Max content-length of archived files, larger files will be ignored
MAX_CONTENT_LENGTH = 50000000

# Only files with these mime-types or extensions will be archived.
# To archive all files, set DATA_FORMATS = 'all'
DATA_FORMATS = [ 
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

RETRIES = False
