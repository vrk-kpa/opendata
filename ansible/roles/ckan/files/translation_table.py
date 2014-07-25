#! /usr/bin/python

import os
import sys
import polib
import codecs
import cgi


def main(arguments):
    if len(arguments) != 5:
        print "Invalid arguments"
        return 1
    modules_root = arguments[0]
    destination = arguments[1]
    ckan_target_po_template = arguments[2]
    ckan_original_po_template = arguments[3]
    languages = arguments[4].split(",")

    po_files = []

    for root, _directories, files in os.walk(modules_root, topdown=False):
        for filename in files:
            if filename.endswith('.po') and "/LC_MESSAGES" in root:
                po_files.append(os.path.join(root, filename))

    for language in languages:
        po_files.append(ckan_original_po_template.replace('!LANGUAGE!', language))

    source_data = {}

    for po_file in po_files:
        for entry in polib.pofile(po_file):
            if entry.msgid not in source_data:
                source_data[entry.msgid] = set()
            source_data[entry.msgid].add(os.path.basename(po_file))

    data = {}
    for language in languages:
        for entry in polib.pofile(ckan_target_po_template.replace('!LANGUAGE!', language)):
            if entry.msgid not in data:
                data[entry.msgid] = {}
            data[entry.msgid][language] = entry.msgstr

    with codecs.open(destination, 'w', encoding="utf-8") as html_target:
        html_target.write(u"<!DOCTYPE html>\n<html>\n<head>\n<meta charset='utf-8'>\n<title>CKAN translations</title>\n")
        html_target.write(u"<style>\n")
        html_target.write(u".row th { text-align: left; }")
        html_target.write(u"tr:nth-child(even) {background: #FFFFFF}")
        html_target.write(u"tr:nth-child(odd) {background: #CCCCCC}")
        html_target.write(u".error {background: red}")
        html_target.write(u"</style>\n")

        html_target.write(u'<script type="text/javascript" src="//code.jquery.com/jquery-1.11.1.min.js"></script>\n')
        html_target.write(u'<script>function toggle_missing() { $(".row").toggle(); $(".error").parent().show(); return false; }</script>')
        html_target.write(u"</head>\n<body>\n")

        html_target.write(u"<a href='javascript:void(0);' onclick='toggle_missing(); return false;'>Toggle missing</a>\n")

        html_target.write(u"<table>\n<thead>\n<tr>")
        html_target.write(u"<th>key (en)</th>")
        for language in languages:
            html_target.write(u"<th>%s</th>" % cgi.escape(language))
        html_target.write(u"<th>sources</th>")

        html_target.write(u"</tr>\n</thead>\n")
        html_target.write(u"<tbody>\n")
        for msgid, translations in data.iteritems():
            html_target.write(u"<tr class='row'><th>%s</th>" % cgi.escape(msgid))
            for language in languages:
                translation = translations.get(language, None)
                html_target.write(u"<td class='%s'>%s</td>" % ('error' if not translation else "ok", cgi.escape(translation or "MISSING")))
            html_target.write(u"<td>%s</td>\n" % cgi.escape(", ".join(source_data.get(msgid, []))))
            html_target.write(u"</tr>\n")
        html_target.write(u"</tbody>\n</table>\n")
        html_target.write(u"</body>\n</html>\n")

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
