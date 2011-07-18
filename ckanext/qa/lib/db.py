"""
Functions for adding data to a local webstore
"""
import os
import datetime
import sqlalchemy as sa
from webstore.database import DatabaseHandler
from webstore.validation import validate_name, NamingException
import transform
from ckanext.qa.lib.log import log

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
    """
    Create a database called db_file, create a table called 'resource' and
    add all data in resource_file to it.
    """
    if not resource_format:
        try:
            resource_format = os.path.split(resource_file)[1].split('.')[1].lower()
        except:
            raise RequestError('Resource format not specified.', 
                'Transformation of resource is not supported as the ' +\
                'resource format could not be determined' 
            )

    try:
        transformer = transform.transformer(resource_format)
    except Exception, e:
        raise RequestError('Resource type not supported', 
            'Transformation of resource of type %s is not supported. Reason: %s'
            % (resource_format, e)
        )

    # convert CSV file to a Python dict
    transformed_file = transformer.transform(resource_file)

    # make sure column names are valid
    fields = []
    for f in transformed_file['fields']:
        try:
            validate_name(f)
            fields.append(f)
        except NamingException:
            # TODO: improve renaming
            try:
                # replace spaces in column names with underscores, spaces are not
                # allowed in webstore column names
                f = f.replace(' ', '_')
                # make sure name starts with a letter
                if not f[0].isalpha():
                    f = "column_" + f
                validate_name(f)
                fields.append(f)
            except:
                # if failed again, ignore this field
                print "Warning: Field name", f, "is not valid, ignoring"

    # add to local webstore: create a new database from the dict
    connection_string = 'sqlite:///' + db_file
    db = DatabaseHandler(sa.create_engine(connection_string))
    table = db['resource']
    # insert dataset
    for row in transformed_file['data']:
        # create a dict for each row
        row_dict = {}
        for i, column_name in enumerate(fields):
            row_dict[column_name] = row[i]
        # add dict to the database
        table.add_row(row_dict)
    table.commit()

def archive_result(db_file, resource_id, message, success=False, content_type=None, content_length=None):
    """
    Save the result of attempting to archive resource_id.
    """
    # add result to local webstore
    connection_string = 'sqlite:///' + db_file
    db = DatabaseHandler(sa.create_engine(connection_string))
    table = db['results']
    result = {
        u'resource_id': resource_id,
        u'message': unicode(message),
        u'success': unicode(success),
        u'content_type': unicode(content_type),
        u'content_length': unicode(content_length),
        u'updated': unicode(datetime.datetime.now().isoformat())
    }
    table.add_row(result)
    table.commit()
    if success:
        log.info("Successfully archived resource")
    else:
        log.info("Could not archive resource: %s" % message)

def get_resource_result(db_file, resource_id):
    try:
        connection_string = 'sqlite:///' + db_file
        db = DatabaseHandler(sa.create_engine(connection_string))
        table = db['results']
        clause = table.args_to_clause({'resource_id': resource_id})
        statement = table.table.select(clause)
        results = table.bind.execute(statement)
        keys = results.keys()
        return dict(zip(keys, results.fetchone()))
    except Exception as e:
        log.error("Could not get archive results for " + resource_id)
        log.error(e.message)
