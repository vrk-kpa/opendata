import sys
import os
sys.path.append(".")
import sqlalchemy as sa
import csv
import csv_file
import json

TYPE_CONVERSION = dict(int = sa.BigInteger,
                       bool = sa.Boolean,
                       decimal = sa.Numeric(15,2),
                       date = sa.Date,
                       boolean = sa.Boolean)

class Database(object):

    def __init__(self, connection = 'sqlite://'):
        self.connection_string = connection
        self.engine = sa.create_engine(self.connection_string)
        self.metadata = sa.MetaData(self.engine)

        self.tables = {}

    def conection(self):

        return self.engine.connect()

    def create_table(self, table_name, table_def):

        print table_def
        fields = []
        for name, field_type in table_def.iteritems():
            sqlalchemy_type = TYPE_CONVERSION.get(field_type)
            if sqlalchemy_type:
                fields.append(sa.Column(name, sqlalchemy_type))
                continue
            if field_type in csv_file.DATE_FORMATS:
                fields.append(sa.Column(name, sa.DateTime))
                continue
            try:
                field_type = int(field_type)
                if field_type > 500:
                    fields.append(sa.Column(name, sa.Unicode))
                else:
                    fields.append(sa.Column(name, sa.Unicode(field_type)))
            except:
                raise ValueError("%s is not a recognised field type" % 
                                 field_type)

        self.tables[table_name] = sa.Table(table_name, self.metadata, *fields) 

        self.metadata.create_all(self.engine)

    def insert_well_formed_data(self, data, table = None):

        if not table and len(self.tables) == 1:
            table = self.tables.keys()[0]

        if not table:
            raise ValueError("a table name is needed")

        con = self.engine.connect()
        return con.execute(self.tables[table].insert(), data)

    def import_bad_file(self, file_name = None, buffer = None, name = None, **kw):

        flat_file = open(file_name, mode = "rb")

        if name not in self.tables:
            self.create_table(name, {'__error': 1000})

        data = [dict(__error=unicode('utf8',errors='ignore')) for line in flat_file]

        con = self.engine.connect()
        return con.execute(self.tables[name].insert(), data)

    def load_csv(self, file_name = None, buffer = None, name = None, **kw):

        if file_name:
            csvfile = csv_file.CsvFile(file_name, **kw)
        else:
            csvfile = csv_file.CsvFile(buffer = buffer, **kw)
        if not name:
            #everything except the filename extension
            name = ".".join(os.path.basename(file_name).split(".")[:-1])
        try:
            csvfile.guess_skip_lines()
            csvfile.get_dialect()
            csvfile.get_headings()
            csvfile.parse_headings()
            csvfile.guess_types()
        except csv.Error:
            return self.import_bad_file(file_name, buffer, name, **kw)

        data = []

        print csvfile.skip_lines

        for row in csvfile.skip_line_rows():
            row['__errors'] = json.dumps(row['__errors'])
            data.append(row)

        errors = 0
        row_num = 0
        for row in csvfile.iterate_csv(as_dict = True, convert=True):
            row_num = row_num + 1
            if row['__errors']:
                errors = errors + 1
            row['__errors'] = json.dumps(row['__errors'])
            data.append(row)

        if row_num == 0 or (errors*100)/row_num > 40:
            return self.import_bad_file(file_name, buffer, name, **kw)

        if name not in self.tables:
            table_def = csvfile.headings_type
            table_def['__errors'] = 1000

            self.create_table(name, csvfile.headings_type)

        self.insert_well_formed_data(data, name)

