import re
import csv
import zipfile
import os
from collections import defaultdict
import subprocess
import StringIO

import xlrd
import magic
import messytables

from ckanext.dgu.lib.formats import Formats

def sniff_file_format(filepath, log):
    '''For a given filepath, work out what file format it is.
    Returns Format dict e.g. {'display_name': 'CSV', ...}
    or None if it can\'t tell what it is.

    Note, log is a logger, either a Celery one or a standard
    Python logging one.
    '''
    format_ = None
    log.info('Sniffing file format of: %s', filepath)
    filepath_utf8 = filepath.encode('utf8') if isinstance(filepath, unicode) \
                    else filepath
    mime_type = magic.from_file(filepath_utf8, mime=True)
    log.info('Magic detects file as: %s', mime_type)
    if mime_type:
        if mime_type == 'application/xml':
            with open(filepath) as f:
                buf = f.read(500)
            format_ = get_xml_variant(buf, log)
        elif mime_type == 'application/zip':
            format_ = get_zipped_format(filepath, log)
        elif mime_type == 'application/msword':
            # Magic gives this mime-type for other MS Office files too
            format_ = run_bsd_file(filepath, log)
            if not format_ and is_excel(filepath, log):
                format_ = Formats.by_display_name()['XLS']
        elif mime_type == 'application/octet-stream':
            # Excel files sometimes come up as this
            if is_excel(filepath, log):
                format_ = Formats.by_display_name()['XLS']
            else:
                # e.g. Shapefile
                format_ = run_bsd_file(filepath, log)
            if not format_:
                with open(filepath) as f:
                    buf = f.read(500)
                format_ = is_html(buf, log)
        elif mime_type == 'text/html':
            # Magic can mistake IATI for HTML
            with open(filepath) as f:
                buf = f.read(100)
            if is_iati(buf, log):
                format_ = Formats.by_display_name()['IATI']
                
        if format_:
            return format_
                
        format_ = Formats.by_mime_type().get(mime_type)

        if not format_:
            if mime_type.startswith('text/'):
                # is it JSON?
                with open(filepath, 'rU') as f:
                    buf = f.read(10000)
                if is_json(buf, log):
                    format_ = Formats.by_extension()['json']
                # is it CSV?
                elif is_csv(buf, log):
                    format_ = Formats.by_extension()['csv']
                elif is_psv(buf, log):
                    format_ = Formats.by_extension()['psv']
                    
                
        if not format_:
            log.warning('Mimetype not recognised by CKAN as a data format: %s', mime_type)
            
        if format_:
            log.info('Mimetype translates to filetype: %s', format_['display_name'])

            if format_['display_name'] == 'TXT':
                # is it JSON?
                with open(filepath, 'rU') as f:
                    buf = f.read(10000)
                if is_json(buf, log):
                    format_ = Formats.by_extension()['json']
                # is it CSV?
                elif is_csv(buf, log):
                    format_ = Formats.by_extension()['csv']
                elif is_psv(buf, log):
                    format_ = Formats.by_extension()['psv']

            elif format_['display_name'] == 'HTML':
                # maybe it has RDFa in it
                with open(filepath) as f:
                    buf = f.read(100000)
                if has_rdfa(buf, log):
                    format_ = Formats.by_display_name()['RDFa']

    else:
        # Excel files sometimes not picked up by magic, so try alternative
        if is_excel(filepath, log):
            format_ = Formats.by_display_name()['XLS']
        # BSD file picks up some files that Magic misses
        # e.g. some MS Word files
        if not format_:
            format_ = run_bsd_file(filepath, log)
                
    if not format_:
        log.warning('Could not detect format of file: %s', filepath)
    return format_

def is_json(buf, log):
    '''Returns whether this text buffer (potentially truncated) is in
    JSON format.'''
    string = '"[^"]*"'
    string_re = re.compile(string)
    number_re = re.compile('-?\d+(\.\d+)?([eE][+-]?\d+)?')
    extra_values_re = re.compile('true|false|null')
    object_start_re = re.compile('{%s:\s?' % string)
    object_middle_re = re.compile('%s:\s?' % string)
    object_end_re = re.compile('}')
    comma_re = re.compile(',\s?')
    array_start_re = re.compile('\[')
    array_end_re = re.compile('\]')
    any_value_regexs = [string_re, number_re, object_start_re, array_start_re, extra_values_re]

    # simplified state machine - just looks at stack of object/array and
    # ignores contents of them, beyond just being simple JSON bits
    pos = 0
    state_stack = [] # stack of 'object', 'array'
    number_of_matches = 0
    while pos < len(buf):
        part_of_buf = buf[pos:]
        if pos == 0:
            potential_matches = (object_start_re, array_start_re, string_re, number_re, extra_values_re)
        elif not state_stack:
            # cannot have content beyond the first byte that is not nested
            return False
        elif state_stack[-1] == 'object':
            # any value
            potential_matches = [comma_re, object_middle_re, object_end_re] + any_value_regexs
        elif state_stack[-1] == 'array':
            # any value or end it
            potential_matches = any_value_regexs + [comma_re, array_end_re]
        for matcher in potential_matches:
            if matcher.match(part_of_buf):
                if matcher in any_value_regexs and state_stack and state_stack[-1] == 'comma':
                    state_stack.pop()
                if matcher == object_start_re:
                    state_stack.append('object')
                elif matcher == array_start_re:
                    state_stack.append('array')
                elif matcher in (object_end_re, array_end_re):
                    try:
                        state = state_stack.pop()
                    except IndexError:
                        # nothing to pop
                        log.info('JSON detect failed: %i matches', number_of_matches)
                        return False
                break
        else:
            # no match
            log.info('JSON detect failed: %i matches', number_of_matches)
            return False
        match_length = matcher.match(part_of_buf).end()
        #print "MATCHED %r %r %s" % (matcher.match(part_of_buf).string[:match_length], matcher.pattern, state_stack)
        pos += match_length
        number_of_matches += 1
        if number_of_matches > 5:
            log.info('JSON detected: %i matches', number_of_matches)
            return True
                                 
    log.info('JSON detected: %i matches', number_of_matches)
    return True

def is_csv(buf, log):
    '''If the buffer is a CSV file then return True.'''
    buf_rows = StringIO.StringIO(buf)
    table_set = messytables.CSVTableSet.from_fileobj(buf_rows)
    return _is_spreadsheet(table_set, 'CSV', log)

def is_psv(buf, log):
    '''If the buffer is a PSV file then return True.'''
    buf_rows = StringIO.StringIO(buf)
    table_set = messytables.CSVTableSet.from_fileobj(buf_rows, delimiter='|')
    return _is_spreadsheet(table_set, 'PSV', log)

def _is_spreadsheet(table_set, format, log):
    def get_cells_per_row(num_cells, num_rows):
        if not num_rows:
            return 0
        return float(num_cells) / float(num_rows)
    num_cells = num_rows = 0
    try:
        table = table_set.tables[0]
        for row in table:
            if row:
                # Must have enough cells
                num_cells += len(row)
                num_rows += 1
                if num_cells > 20 or num_rows > 10:
                    cells_per_row = get_cells_per_row(num_cells, num_rows)
                    # over the long term, 2 columns is the minimum
                    if cells_per_row > 1.9:
                        log.info('Is %s because %.1f cells per row (%i cells, %i rows)', \
                                 format,
                                 get_cells_per_row(num_cells, num_rows),
                                 num_cells, num_rows)
                        return True
    finally:
        pass
    # if file is short then be more lenient
    if num_cells > 3 or num_rows > 1:
        cells_per_row = get_cells_per_row(num_cells, num_rows)
        if cells_per_row > 1.5:
            log.info('Is %s because %.1f cells per row (%i cells, %i rows)', \
                     format,
                     get_cells_per_row(num_cells, num_rows),
                     num_cells, num_rows)
            return True
    log.info('Not %s - not enough valid cells per row '
             '(%i cells, %i rows, %.1f cells per row)', \
             format, num_cells, num_rows, get_cells_per_row(num_cells, num_rows))
    return False
    
def is_html(buf, log):
    '''If this buffer is HTML, return that format type, else None.'''
    xml_re = '.{0,3}\s*(<\?xml[^>]*>\s*)?(<!doctype[^>]*>\s*)?<html[^>]*>'
    match = re.match(xml_re, buf, re.IGNORECASE)
    if match:
        log.info('HTML tag detected')
        return Formats.by_extension()['html']
    log.warning('html not detected %s', buf)    

def is_iati(buf, log):
    '''If this buffer is IATI format, return that format type, else None.'''
    xml_re = '.{0,3}\s*(<\?xml[^>]*>\s*)?(<!doctype[^>]*>\s*)?<iati-(activities|organisations)[^>]*>'
    match = re.match(xml_re, buf, re.IGNORECASE)
    if match:
        log.info('IATI tag detected')
        return Formats.by_extension()['iati']
    log.warning('IATI not detected %s', buf)

def get_xml_variant(buf, log):
    '''If this buffer is in a format based on XML, return the format type.'''
    xml_re = '.{0,3}\s*<\?xml[^>]*>\s*(<!doctype[^>]*>\s*)?<([^>\s]*)'
    match = re.match(xml_re, buf, re.IGNORECASE)
    if match:
        top_level_tag_name = match.groups()[-1].lower()
        top_level_tag_name = top_level_tag_name.replace('rdf:rdf', 'rdf')
        top_level_tag_name = top_level_tag_name.replace('wms_capabilities', 'wms')
        if top_level_tag_name in Formats.by_extension():
            format_ = Formats.by_extension()[top_level_tag_name]
            log.info('XML variant detected: %s', format_['display_name'])
            return format_
        log.warning('Did not recognise XML format: %s', top_level_tag_name)
        return Formats.by_extension()['xml']
    log.warning('XML format didn\'t conform to expected format: %s', buf)

def has_rdfa(buf, log):
    '''If the buffer HTML contains RDFa then this returns True'''
    # quick check for the key words
    if 'about=' not in buf or 'property=' not in buf:
        return False

    # more rigorous check for them as tag attributes
    about_re = '<[^>]+\sabout="[^"]+"[^>]*>'
    property_re = '<[^>]+\sproperty="[^"]+"[^>]*>'
    # remove CR to catch tags spanning more than one line
    #buf = re.sub('\r\n', ' ', buf)
    if not re.search(about_re, buf):
        return False
    if not re.search(property_re, buf):
        return False
    log.info('RDFA tags found in HTML')
    return True

def get_zipped_format(filepath, log):
    '''For a given zip file, return the format of file inside.
    For multiple files, choose by the most open, and then by the most
    popular extension.'''
    # just check filename extension of each file inside
    try:
        # note: Cannot use "with" with a zipfile before python 2.7
        #       so we have to close it manually.
        zip = zipfile.ZipFile(filepath, 'r')
        try:
            filenames = zip.namelist()
        finally:
            zip.close()
    except zipfile.BadZipfile, e:
        log.warning('Zip file open raised error %s: %s',
                    e, e.args)
        return
    except Exception, e:
        log.warning('Zip file open raised exception %s: %s',
                    e, e.args)
        return
    top_score = 0
    top_scoring_extension_counts = defaultdict(int) # extension: number_of_files
    for filename in filenames:
        extension = os.path.splitext(filename)[-1][1:].lower()
        if extension in Formats.by_extension():
            if (extension + '.zip') in Formats.by_extension():
                format_ = Formats.by_extension()[extension]
                if format_['openness'] > top_score:
                    top_score = format_['openness']
                    top_scoring_extension_counts = defaultdict(int)
                if format_['openness'] == top_score:
                    top_scoring_extension_counts[extension] += 1
            else:
                log.warning('Zipped file extension not a known format combination: "%s" (%s)', extension, filepath)
        else:
            log.warning('Zipped file of unknown extension: "%s" (%s)', extension, filepath)
    if not top_scoring_extension_counts:
        log.warning('Zip has no known extensions: %s', filepath)
        return Formats.by_display_name()['Zip']
        
    top_scoring_extension_counts = sorted(top_scoring_extension_counts.items(),
                                          lambda x: x[1])
    top_extension = top_scoring_extension_counts[-1][0]
    log.info('Zip file\'s most popular extension is "%s" (All extensions: %r)',
             top_extension, top_scoring_extension_counts)
    zipped_extension = top_extension + '.zip'
    if zipped_extension not in Formats.by_extension():
        log.warning('Zipped %s not a registered format', top_extension)
        return Formats.by_display_name()['Zip']
    format_ = Formats.by_extension()[zipped_extension]
    log.info('Zipped file format detected: %s', format_['display_name'])
    return format_
    
def is_excel(filepath, log):
    try:
        book = xlrd.open_workbook(filepath)
    except Exception, e:
        log.info('Failed to load as Excel: %s %s', e, e.args)
        return False
    else:
        log.info('Excel file opened successfully')
        return True

# same as the python 2.7 subprocess.check_output
def check_output(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise Exception('Non-zero exit status %s: %s' % (retcode, output))
    return output

def run_bsd_file(filepath, log):
    '''Run the BSD command-line tool "file" to determine file type. Returns
    a Format or None if it fails.'''
    result = check_output(['file', filepath])
    match = re.search('Name of Creating Application: ([^,]*),', result)
    if match:
        app_name = match.groups()[0]
        format_map = {'Microsoft Office PowerPoint': 'ppt',
                      'Microsoft PowerPoint': 'ppt',
                      'Microsoft Excel': 'xls',
                      'Microsoft Office Word': 'doc',
                      'Microsoft Word 10.0': 'doc',
                      'Microsoft Macintosh Word': 'doc',
                      }
        if app_name in format_map:
            extension = format_map[app_name]
            format_ = Formats.by_extension()[extension]
            log.info('"file" detected file format: %s',
                     format_['display_name'])
            return format_
    match = re.search(': ESRI Shapefile', result)
    if match:
        format_ = Formats.by_extension()['shp']
        log.info('"file" detected file format: %s',
                 format_['display_name'])
        return format_
    log.info('"file" could not determine file format of "%s": %s',
             filepath, result)
                      
