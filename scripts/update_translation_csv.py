import csv
import sys

if len(sys.argv) < 4:
    print("Usage: %s <combined_csv> <lang_csv> <lang>" % sys.argv[0])
    sys.exit()

csv_file_combined = sys.argv[1]
csv_file = sys.argv[2]
csv_lang = sys.argv[3]

combined_data = {row['msgid']: row for row in csv.DictReader(open(csv_file_combined, 'r'))}

rows = list(csv.DictReader(open(csv_file, 'r')))
fields = ['msgid','msgid_plural','flags','references','extractedComments','comments','msgstr[0]','msgstr[1]']
writer = csv.DictWriter(sys.stdout, fields, quoting=csv.QUOTE_ALL)
writer.writeheader()

for row in rows:
    combined_values = combined_data[row['msgid']]
    row['msgstr[0]'] = combined_values['%s' % csv_lang]
    row['msgstr[1]'] = combined_values['%s_plural' % csv_lang]
    writer.writerow(row)
