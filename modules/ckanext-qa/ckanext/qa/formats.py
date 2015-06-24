'''A directory of file formats and their properties'''

import re

class Formats(object):
    @classmethod
    def by_display_name(cls):
        '''Returns the formats data as a dict keyed by the display name'''
        if not hasattr(cls, '_by_display_name'):
            data = cls.get_data()
            cls._by_display_name = {}
            for format_dict in data:
                cls._by_display_name[format_dict['display_name']] = format_dict
        return cls._by_display_name

    @classmethod
    def by_mime_type(cls):
        '''Returns the formats data as a dict keyed by mime type'''
        if not hasattr(cls, '_by_mime_type'):
            data = cls.get_data()
            cls._by_mime_type = {}
            for format_dict in data:
                for mime_type in format_dict['mime_types']:
                    cls._by_mime_type[mime_type] = format_dict
        return cls._by_mime_type

    @classmethod
    def by_extension(cls):
        '''Returns the formats data as a dict keyed by filename extension'''
        if not hasattr(cls, '_by_extension'):
            data = cls.get_data()
            cls._by_extension = {}
            for format_dict in data:
                for extension in format_dict['extensions']:
                    cls._by_extension[extension] = format_dict
        return cls._by_extension

    @classmethod
    def by_reduced_name(cls):
        '''Returns the formats data as a dict keyed by "reduced" names for
        each format. This is helpful for matching against user-inputted formats.
        e.g. "TXT / .Zip" is "txt/zip"'''
        if not hasattr(cls, '_by_reduced'):
            data = cls.get_data()
            cls._by_reduced = {}
            for format_dict in data:
                for name in [format_dict['display_name']] + list(format_dict['extensions']) \
                             + list(format_dict['alternative_names']):
                    reduced_name = cls.reduce(name)
                    cls._by_reduced[reduced_name] = format_dict
        return cls._by_reduced

    @staticmethod
    def reduce(format_name):
        format_name = format_name.strip().lower()
        if format_name.startswith('.'): format_name = format_name[1:]
        return re.sub('[^a-z/+]', '', format_name)

    @classmethod
    def match(cls, raw_resource_format):
        '''Given a format that may be badly formatted, try and match it to
        a known format and return that.
        If no match is found, returns None.
        '''
        # Try exact match
        if raw_resource_format in cls.by_display_name():
            return cls.by_display_name()[raw_resource_format]

        # Try canonised match
        reduced_raw = cls.reduce(raw_resource_format)
        if reduced_raw in cls.by_reduced_name():
            return cls.by_reduced_name()[reduced_raw]

    @classmethod
    def get_data(cls):
        '''Returns the list of data formats, each one as a dict
        e.g. [{'display_name': 'TXT', 'extensions': ('txt',), 'extension': 'txt',
               'mime_types': ('text/plain',), 'openness': 1},
              ...]
        '''
        if not hasattr(cls, '_data'):
            # store the data here so it only loads when first used, rather
            # than on module load
            data_flat = (
                # Display name, alternative names, extensions (lower case), mime-types, openness, icon-name
                ('HTML', ('web page', 'website'), ('html', 'htm', 'asp', 'php'), ('text/html',), 0, 'globe--arrow'),
                ('JPEG', (), ('jpg','jpeg'), ('image/jpg',), 0, 'image'),
                ('TIFF', (), ('tifflzw','tiff'), ('image/tiff',), 0, 'image'),
                ('Database', ('database','sql'), (), (), 0, 'database-sql'),
                ('API', ('api',), (), (), 0, 'server-cloud'),
                ('TXT', (), ('txt',), ('text/plain',), 1, 'document-text'),
                ('TXT / Zip', (), ('txt.zip',), (), 1, 'document-text'),
                ('PDF', (), ('pdf',), ('application/pdf',), 1, 'document-pdf'),
                ('PDF / Zip', (), ('pdf.zip',), (), 1, 'document-pdf'),
                ('RTF', (), ('rtf',), ('application/rtf',), 1, 'document-word'),
                ('Zip', (), ('zip',), ('application/x-zip', 'application/x-compressed', 'application/x-zip-compressed', 'application/zip', 'multipart/x-zip', 'application/x-gzip'), 1, 'folder-zipper'),
                ('Torrent', (), ('torrent',), ('application/x-bittorrent',), 1, ''),
                ('DOC', ('word',), ('doc', 'docx', 'mcw'), ('application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-word.document.macroEnabled.12'), 1, 'document-word'),
                ('ODT', (), ('odt',), ('application/vnd.oasis.opendocument.text', 'application/x-vnd.oasis.opendocument.text'), 1, 'document-word'),
                ('PPT', ('powerpoint',), ('ppt', 'pptx', 'ppz'), ('application/mspowerpoint', 'application/vnd.ms-powerpoint.presentation.macroEnabled.12', 'application/vnd.ms-powerpoint'), 1, 'document-powerpoint'),
                ('ODP', (), ('odp',), ('application/vnd.oasis.opendocument.presentation', 'application/x-vnd.oasis.opendocument.presentation'), 1, 'document-powerpoint'),
                ('XLS', ('excel',), ('xls', 'xlsx', 'xlb'), ('application/excel', 'application/x-excel', 'application/x-msexcel', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel.sheet.binary.macroenabled.12', 'application/vnd.ms-excel.sheet.macroenabled.12', 'application/vnd.msexcel'), 2, 'document-excel'),
                ('XLS / Zip', (), ('xls.zip',), (), 2, 'document-excel'),
                ('SHP', ('shapefile', 'esri shapefile',), ('shp',), (), 2, 'globe-model'),
                ('SHP / Zip', (), ('shp.zip',), (), 2, 'globe-model'),
                ('CSV', ('csvfile',), ('csv',), ('text/csv','text/comma-separated-values'), 3, 'document-invoice'),
                ('CSV / Zip', (), ('csv.zip',), (), 3, 'document-invoice'),
                ('PSV', (), ('psv',), ('text/psv','text/pipe-separated-values'), 3, 'document-invoice'),
                ('PSV / Zip', (), ('psv.zip',), (), 3, 'document-invoice'),
                ('JSON', (), ('json',), ('application/json', 'text/x-json'), 3, 'document-node'),
                ('XML', (), ('xml',), ('text/xml','application/xml'), 3, 'document-code'),
                ('XML / Zip', (), ('xml.zip',), (), 3, 'document-code'),
                ('RSS', (), ('rss',), ('text/rss+xml',), 3, 'feed-document'),
                ('ODS', (), ('ods',), ('application/vnd.oasis.opendocument.spreadsheet',), 3, 'document-excel'),
                ('WMS', (), ('wms',), ('application/vnd.ogc.wms_xml',), 3, 'globe-model'),
                ('KML', (), ('kml',), ('application/vnd.google-earth.kml+xml',), 3, 'globe-model'),
                ('NetCDF', (), ('cdf', 'netcdf'), ('application/x-netcdf',), 3, ''),
                ('IATI', (), ('iati',), ('application/x-iati+xml',), 3, 'document-code'),
                ('iCalendar', ('iCal', 'ICS'), ('ics', 'ical'), ('text/calendar',), 3, 'calendar-day'),
                ('RDF', ('rdf/xml','Turtle','N-Triples'), ('rdf','ttl','nt'), ('application/rdf+xml','text/turtle'), 5, 'document-rdf'),
                ('RDFa', ('html+rdfa',), (), (), 5, 'document-rdf'),
                ('SPARQL', (), (), ('application/sparql-results+xml', 'application/sparql-query'), 5, 'document-rdf'),
                ('SPARQL web form', (), (), (), 5, 'document-rdf'),
                )
            cls._data = []
            for line in data_flat:
                display_name, alternative_names, extensions, mime_types, openness, icon = line
                format_dict = dict(zip(('display_name', 'alternative_names', 'extensions', 'mime_types', 'openness', 'icon'), line))
                format_dict['extension'] = extensions[0] if extensions else ''
                cls._data.append(format_dict)
        return cls._data

# Mime types which give not much clue to the format
VAGUE_MIME_TYPES = set(('application/octet-stream',))
