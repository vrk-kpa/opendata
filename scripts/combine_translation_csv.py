import csv
import sys

if len(sys.argv) < 4:
    print("Usage: %s <csv_fi> <csv_sv> <csv_en>" % sys.argv[0])
    sys.exit()

csv_file_fi = sys.argv[1]
csv_file_sv = sys.argv[2]
csv_file_en = sys.argv[3]

def extract_from_csv(filename):
    reader = csv.DictReader(open(filename, 'r'))
    return {row['msgid']: row for row in reader}

fi_data = extract_from_csv(csv_file_fi)
sv_data = extract_from_csv(csv_file_sv)
en_data = extract_from_csv(csv_file_en)

keys = set(fi_data.keys()).union(set(sv_data.keys())).union(set(en_data.keys()))

fields = ['msgid', 'msgid_plural', 'references', 'fi', 'fi_plural', 'en', 'en_plural', 'sv', 'sv_plural']
writer = csv.DictWriter(sys.stdout, fields, quoting=csv.QUOTE_ALL)
writer.writeheader()

for key in keys:
    fi_values = fi_data[key]
    sv_values = sv_data[key]
    en_values = en_data[key]
    values = {
            'msgid': key,
            'msgid_plural': fi_values['msgid_plural'],
            'references': fi_values['references'],
            'fi': fi_values['msgstr[0]'],
            'fi_plural': fi_values['msgstr[1]'],
            'sv': sv_values['msgstr[0]'],
            'sv_plural': sv_values['msgstr[1]'],
            'en': en_values['msgstr[0]'],
            'en_plural': en_values['msgstr[1]'],
            }
    writer.writerow(values)

