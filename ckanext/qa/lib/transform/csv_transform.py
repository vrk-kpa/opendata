"""
Data Proxy - CSV transformation adapter
"""
import base
import brewery.ds as ds

try:
    import json
except ImportError:
    import simplejson as json

class CSVTransformer(base.Transformer):
    def __init__(self):
        super(CSVTransformer, self).__init__()
        self.requires_size_limit = False

        # if 'encoding' in self.query:
        #     self.encoding = self.query["encoding"]
        # else:
        self.encoding = 'utf-8'
        # if 'dialect' in self.query:
        #     self.dialect = self.query["dialect"]
        # else:
        self.dialect = None
        
    def transform(self, handle):
        src = ds.CSVDataSource(handle, encoding = self.encoding, dialect = self.dialect)
        src.initialize()
        result = self.read_source_rows(src)
        return result
