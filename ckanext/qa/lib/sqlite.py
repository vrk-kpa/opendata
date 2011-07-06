"""
Functions for converting data to and from SQLite databases.
"""
import sqlite
import os
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

def resource_to_sqlite(resource_format, resource_file, db_file):
    try:
        transformer = transform.transformer(resource_format)
    except Exception, e:
        raise RequestError('Resource type not supported', 
            'Transformation of resource of type %s is not supported. Reason: %s'
            % (resource_format, e)
        )

    f = open(resource_file, 'r')
    transformed_file = transformer.transform(f)
    f.close()
