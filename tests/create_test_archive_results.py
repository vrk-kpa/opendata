import datetime
import sqlalchemy as sa
from webstore.database import DatabaseHandler

DB_FILE = 'test_archive_results.db'

connection_string = 'sqlite:///' + DB_FILE
db = DatabaseHandler(sa.create_engine(connection_string))
table = db['results']
result_1 = {
    u'resource_id': u'resource_1',
    u'message': u'message_1',
    u'success': unicode(True),
    u'content_type': u'text/csv',
    u'content_length': unicode(167),
    u'updated': unicode(datetime.datetime.now().isoformat())
}
table.add_row(result_1)
result_2 = {
    u'resource_id': u'resource_2',
    u'message': u'message_2',
    u'success': unicode(True),
    u'content_type': u'text/csv',
    u'content_length': unicode(168),
    u'updated': unicode(datetime.datetime.now().isoformat())
}
table.add_row(result_2)
table.commit()
