import re

import magic

from ckanext.dgu.lib.formats import Formats

def sniff_file_format(filepath, log):
    '''For a given filepath, work out what file format it is.
    Returns extension e.g. 'csv'.
    '''
    format_ = None
    mime_type = magic.from_file(filepath, mime=True)
    if mime_type:
        format_ = Formats.by_mime_type().get(mime_type)
        if not format_:
            log.warning('Mimetype not recognised by CKAN as a data format: %s', mime_type)
        elif format_['display_name'] == 'TXT':
            # is it JSON?
            with open(filepath) as f:
                buf = f.read(100)
            if is_json(buf):
                format_ = Formats.by_extension()['json']
                
    if not format_:
        log.warning('Could not detect format of file: %s', filepath)
    return format_

def is_json(buf):
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
                        return False
                break
        else:
            # no match
            return False
        match_length = matcher.match(part_of_buf).end()
        #print "MATCHED %r %r %s" % (matcher.match(part_of_buf).string[:match_length], matcher.pattern, state_stack)
        pos += match_length
        number_of_matches += 1
        if number_of_matches > 5:
            return True
                                 
    return True
