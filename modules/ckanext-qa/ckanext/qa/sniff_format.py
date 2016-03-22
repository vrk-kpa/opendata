import re
import zipfile
import os
from collections import defaultdict
import subprocess
import StringIO

import xlrd
import magic
import messytables

from ckanext.qa import lib
from ckan.lib import helpers as ckan_helpers


def sniff_file_format(filepath, log):
    '''For a given filepath, work out what file format it is.

    Returns a dict with format as a string, which is the format's canonical
    shortname (as defined by ckan's resource_formats.json) and a key that says
    if it is contained in a zip or something.

    e.g. {'format': 'CSV',
          'container': 'zip',
          }
    or None if it can\'t tell what it is.

    Note, log is a logger, either a Celery one or a standard Python logging
    one.
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
                buf = f.read(5000)
            format_ = get_xml_variant_including_xml_declaration(buf, log)
        elif mime_type == 'application/zip':
            format_ = get_zipped_format(filepath, log)
        elif mime_type in ('application/msword', 'application/vnd.ms-office'):
            # In the past Magic gives the msword mime-type for Word and other
            # MS Office files too, so use BSD File to be sure which it is.
            format_ = run_bsd_file(filepath, log)
            if not format_ and is_excel(filepath, log):
                format_ = {'format': 'XLS'}
        elif mime_type == 'application/octet-stream':
            # Excel files sometimes come up as this
            if is_excel(filepath, log):
                format_ = {'format': 'XLS'}
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
                format_ = {'format': 'IATI'}

        if format_:
            return format_

        format_tuple = ckan_helpers.resource_formats().get(mime_type)
        if format_tuple:
            format_ = {'format': format_tuple[1]}

        if not format_:
            if mime_type.startswith('text/'):
                # is it JSON?
                with open(filepath, 'rU') as f:
                    buf = f.read(10000)
                if is_json(buf, log):
                    format_ = {'format': 'JSON'}
                # is it CSV?
                elif is_csv(buf, log):
                    format_ = {'format': 'CSV'}
                elif is_psv(buf, log):
                    format_ = {'format': 'PSV'}

        if not format_:
            log.warning('Mimetype not recognised by CKAN as a data format: %s',
                        mime_type)

        if format_:
            log.info('Mimetype translates to filetype: %s',
                     format_['format'])

            if format_['format'] == 'TXT':
                # is it JSON?
                with open(filepath, 'rU') as f:
                    buf = f.read(10000)
                if is_json(buf, log):
                    format_ = {'format': 'JSON'}
                # is it CSV?
                elif is_csv(buf, log):
                    format_ = {'format': 'CSV'}
                elif is_psv(buf, log):
                    format_ = {'format': 'PSV'}
                # XML files without the "<?xml ... ?>" tag end up here
                elif is_xml_but_without_declaration(buf, log):
                    format_ = get_xml_variant_without_xml_declaration(buf, log)
                elif is_ttl(buf, log):
                    format_ = {'format': 'TTL'}

            elif format_['format'] == 'HTML':
                # maybe it has RDFa in it
                with open(filepath) as f:
                    buf = f.read(100000)
                if has_rdfa(buf, log):
                    format_ = {'format': 'RDFa'}

    else:
        # Excel files sometimes not picked up by magic, so try alternative
        if is_excel(filepath, log):
            format_ = {'format': 'XLS'}
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
                        log.info('Not JSON - %i matches', number_of_matches)
                        return False
                break
        else:
            # no match
            log.info('Not JSON - %i matches', number_of_matches)
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
    table_set = messytables.CSVTableSet(buf_rows)
    return _is_spreadsheet(table_set, 'CSV', log)

def is_psv(buf, log):
    '''If the buffer is a PSV file then return True.'''
    buf_rows = StringIO.StringIO(buf)
    table_set = messytables.CSVTableSet(buf_rows, delimiter='|')
    return _is_spreadsheet(table_set, 'PSV', log)

def _is_spreadsheet(table_set, format, log):
    def get_cells_per_row(num_cells, num_rows):
        if not num_rows:
            return 0
        return float(num_cells) / float(num_rows)
    num_cells = num_rows = 0
    try:
        table = table_set.tables[0]
        # Iterate through the table.sample (sample because otherwise
        # it will barf if there is an unclosed string at the end)
        for row in table.sample:
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
        return {'format': 'HTML'}
    log.debug('Not HTML')

def is_iati(buf, log):
    '''If this buffer is IATI format, return that format type, else None.'''
    xml_re = '.{0,3}\s*(<\?xml[^>]*>\s*)?(<!doctype[^>]*>\s*)?<iati-(activities|organisations)[^>]*>'
    match = re.match(xml_re, buf, re.IGNORECASE)
    if match:
        log.info('IATI tag detected')
        return {'format': 'IATI'}
    log.debug('Not IATI')

def is_xml_but_without_declaration(buf, log):
    '''Decides if this is a buffer of XML, but missing the usual <?xml ...?>
    tag.'''
    xml_re = '.{0,3}\s*(<\?xml[^>]*>\s*)?(<!doctype[^>]*>\s*)?<([^>\s]*)([^>]*)>'
    match = re.match(xml_re, buf, re.IGNORECASE)
    if match:
        top_level_tag_name, top_level_tag_attributes = match.groups()[-2:]
        if 'xmlns:' not in top_level_tag_attributes and \
               (len(top_level_tag_name) > 20 or
                len(top_level_tag_attributes) > 200):
            log.debug('Not XML (without declaration) - unlikely length first tag: <%s %s>',
                        top_level_tag_name, top_level_tag_attributes)
            return False
        log.info('XML detected - first tag name: <%s>', top_level_tag_name)
        return True
    log.debug('Not XML (without declaration) - tag not detected')
    return False

def get_xml_variant_including_xml_declaration(buf, log):
    '''If this buffer is in a format based on XML and has the <xml>
    declaration, return the format type.'''
    xml_re = '.{0,3}\s*<\?xml[^>]*>\s*(<!doctype[^>]*>\s*)?(<[^>]+>)'
    match = re.match(xml_re, buf, re.IGNORECASE)
    if match:
        top_level_tag_name = match.groups()[-1].lower()
        return get_xml_variant_without_xml_declaration(match.groups()[-1], log)
    log.debug('XML declaration not found: %s', buf)

def get_xml_variant_without_xml_declaration(buf, log):
    '''If this buffer is in a format based on XML, without any XML declaration
    or other boilerplate, return the format type.'''
    xml_re = '.{0,3}\s*<([^>\s]*)'
    match = re.match(xml_re, buf)
    if match:
        top_level_tag_name = match.groups()[-1].lower()
        top_level_tag_name = top_level_tag_name.replace('rdf:rdf', 'rdf')
        top_level_tag_name = top_level_tag_name.replace('wms_capabilities', 'wms')  # WMS 1.3
        top_level_tag_name = top_level_tag_name.replace('wmt_ms_capabilities', 'wms')  # WMS 1.1.1
        format_tuple = ckan_helpers.resource_formats().get(top_level_tag_name)
        if format_tuple:
            format_ = {'format': format_tuple[1]}
            log.info('XML variant detected: %s', format_tuple[2])
            return format_
        log.warning('Did not recognise XML format: %s', top_level_tag_name)
        return {'format': 'XML'}
    log.debug('XML tags not found: %s', buf)

def has_rdfa(buf, log):
    '''If the buffer HTML contains RDFa then this returns True'''
    # quick check for the key words
    if 'about=' not in buf or 'property=' not in buf:
        log.debug('Not RDFA')
        return False

    # more rigorous check for them as tag attributes
    about_re = '<[^>]+\sabout="[^"]+"[^>]*>'
    property_re = '<[^>]+\sproperty="[^"]+"[^>]*>'
    # remove CR to catch tags spanning more than one line
    #buf = re.sub('\r\n', ' ', buf)
    if not re.search(about_re, buf):
        log.debug('Not RDFA')
        return False
    if not re.search(property_re, buf):
        log.debug('Not RDFA')
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
        log.info('Zip file open raised error %s: %s',
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
        format_tuple = ckan_helpers.resource_formats().get(extension)
        if format_tuple:
            score = lib.resource_format_scores().get(format_tuple[1])
            if score is not None and score > top_score:
                top_score = score
                top_scoring_extension_counts = defaultdict(int)
            if score == top_score:
                top_scoring_extension_counts[extension] += 1
        else:
            log.info('Zipped file of unknown extension: "%s" (%s)', extension, filepath)
    if not top_scoring_extension_counts:
        log.info('Zip has no known extensions: %s', filepath)
        return {'format': 'ZIP'}

    top_scoring_extension_counts = sorted(top_scoring_extension_counts.items(),
                                          key=lambda x: x[1])
    top_extension = top_scoring_extension_counts[-1][0]
    log.info('Zip file\'s most popular extension is "%s" (All extensions: %r)',
             top_extension, top_scoring_extension_counts)
    format_tuple = ckan_helpers.resource_formats()[top_extension]
    format_ = {'format': format_tuple[1],
               'container': 'ZIP'}
    log.info('Zipped file format detected: %s', format_tuple[2])
    return format_


def is_excel(filepath, log):
    try:
        xlrd.open_workbook(filepath)
    except Exception, e:
        log.info('Not Excel - failed to load: %s %s', e, e.args)
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
    a format dict or None if it fails.'''
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
            format_tuple = ckan_helpers.resource_formats()[extension]
            log.info('"file" detected file format: %s',
                     format_tuple[2])
            return {'format': format_tuple[1]}
    match = re.search(': ESRI Shapefile', result)
    if match:
        format_ = {'format': 'SHP'}
        log.info('"file" detected file format: %s',
                 format_['format'])
        return format_
    log.info('"file" could not determine file format of "%s": %s',
             filepath, result)


def is_ttl(buf, log):
    '''If the buffer is a Turtle RDF file then return True.'''
    # Turtle spec: "Turtle documents may have the strings '@prefix' or '@base' (case dependent) near the beginning of the document."
    at_re = '^@(prefix|base) '
    match = re.search(at_re, buf, re.MULTILINE)
    if match:
        log.info('Turtle RDF detected - @prefix or @base')
        return True

    # Alternatively look for several triples
    num_required_triples = 5
    ignore, num_replacements = turtle_regex().subn('', buf, num_required_triples)
    if num_replacements >= num_required_triples:
        log.info('Turtle RDF detected - %s triples' % num_replacements)
        return True

    log.debug('Not Turtle RDF - triples not detected (%i)' % num_replacements)

turtle_regex_ = None
def turtle_regex():
    '''Return a compiled regex that matches a turtle triple.

    Each RDF term may be in these forms:
         <url>
         "a literal"
         "translation"@ru
         "literal typed"^^<http://www.w3.org/2001/XMLSchema#string>
         "literal typed with prefix"^^xsd:string
         'single quotes'
         """triple \n quotes"""
         -4.2E-9
         false
         _:blank_node
     No need to worry about prefixed terms, since there would have been a
     @prefix already detected for them to be used.
         prefix:term  :blank_prefix
     does not support nested blank nodes, collection, sameas ('a' token)
    '''
    global turtle_regex_
    if not turtle_regex_:
        rdf_term = '(<[^ >]+>|_:\S+|".+?"(@\w+)?(\^\^\S+)?|\'.+?\'(@\w+)?(\^\^\S+)?|""".+?"""(@\w+)?(\^\^\S+)?|\'\'\'.+?\'\'\'(@\w+)?(\^\^\S+)?|[+-]?([0-9]+|[0-9]*\.[0-9]+)(E[+-]?[0-9]+)?|false|true)'

        # simple case is: triple_re = '^T T T \.$'.replace('T', rdf_term)
        # but extend to deal with multiple predicate-objects:
        #triple = '^T T T\s*(;\s*T T\s*)*\.\s*$'.replace('T', rdf_term).replace(' ', '\s+')
        triple = '(^T|;)\s*T T\s*(;|\.\s*$)'.replace('T', rdf_term).replace(' ', '\s+')
        turtle_regex_ = re.compile(triple, re.MULTILINE)
    return turtle_regex_
