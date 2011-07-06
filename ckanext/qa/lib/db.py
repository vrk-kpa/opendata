"""
Functions for converting datasets to and from databases.
"""
import os
import sqlalchemy as sa
import transform

class ProxyError(StandardError):
    def __init__(self, title, message):
        super(ProxyError, self).__init__()
        self.title = title
        self.message = message
        self.error = "Error"
        
class ResourceError(ProxyError):
    def __init__(self, title, message):
        super(ResourceError, self).__init__(title, message)
        self.error = "Resource Error"

class RequestError(ProxyError):
    def __init__(self, title, message):
        super(RequestError, self).__init__(title, message)
        self.error = "Request Error"

def resource_to_db(resource_format, resource_file, db_file):
    try:
        transformer = transform.transformer(resource_format)
    except Exception, e:
        raise RequestError('Resource type not supported', 
            'Transformation of resource of type %s is not supported. Reason: %s'
            % (resource_format, e)
        )

    # convert CSV file to a Python dict
    # f = open(resource_file, 'r')
    f = open('/Users/john/Desktop/foo.csv', 'r')
    transformed_file = transformer.transform(f)
    f.close()

    # create a new database from the dict
    connection_string = 'sqlite:///' + db_file
    engine = sa.create_engine(connection_string)
    connection = engine.connect()
    metadata = sa.MetaData(engine)

    # create the table from the field names
    fields = []
    for field in transformed_file['fields']:
        fields.append(sa.Column(field, sa.Unicode))
    table = sa.Table('resource', metadata, *fields) 
    metadata.create_all(engine)

    # insert dataset
    # for row in transformed_file['data']:
    #     transaction = connection.begin()
    #     try:
    #         connection.execute(table.insert(), row)
    #         transaction.commit()
    #     except Exception as e:
    #         print e.message
    #         transaction.rollback()
    #         print "Error adding dataset to database:", db_file
    
    connection.close()
    return True
