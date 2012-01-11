import sys
import json
import messytables
from messytables import CSVTableSet, XLSTableSet, types_processor, \
headers_guess, headers_processor, offset_processor 
import requests
import datetime
from unicodedata import normalize
from re import sub

DATA_FORMATS = [ 
    'csv',
    'text/csv',
    'xls',
    'application/ms-excel',
    'application/vnd.ms-excel',
    'application/xls',
    'application/octet-stream'
]

def guess_types(rows):
    ''' Simple guess types of fields, only allowed are int, float and string'''
    if not rows:
        return
    headers = rows[0].keys()
    guessed_types = [] 
    for header in headers:
        data_types = set([int, float])
        for row in rows:
            if not row.get(header):
                continue
            for data_type in list(data_types):
                try:
                    data_type(row[header])
                except (TypeError, ValueError):
                    data_types.discard(data_type)
            if not data_types:
                break
        if int in data_types:
            guessed_types.append(messytables.IntegerType())
        elif float in data_types:
            guessed_types.append(messytables.FloatType())
        else:
            guessed_types.append(messytables.StringType())
    return guessed_types


def _clean_name(name):
    # Looks like a path
    if '/' in name:
        name = name[name.index('/')+1:]

    if not name:
        return 'data'

    res = normalize('NFKD', name).encode('ascii', 'ignore').replace(' ', '-').lower()
    res = sub('[^a-zA-Z0-9_-]', '', res)
    res = sub('-+', '-', res)
    return res
                
                
def upload_content(context, resource, result):    
    
    if not context.get('webstore_url'):
        raise WebstorerError('Configuration error: "ckan.webstore_url" is not defined.')
    webstore_url = context.get('webstore_url').rstrip('/')    
    first_ws_url = None
    
    excel_types = ['xls', 'application/ms-excel', 'application/xls','application/vnd.ms-excel',]
    content_type = result['headers'].get('content-type', '')        
    f = open(result['saved_file'], 'rb')

    if content_type in excel_types or resource['format'] in excel_types:
        table_sets = XLSTableSet.from_fileobj(f)
        if not resource.get('mimetype'):
            resource['mimetype'] = 'application/ms-excel'
    else:
        table_sets = CSVTableSet.from_fileobj(f)
        if not resource.get('mimetype'):
            resource['mimetype'] = 'text/csv'

    # To implement for each sheet we would need to change the webstore url
    # returned to the front end - for preview (or at least default to the 
    # first sheet). We'd also need to name each sheet which is currently problematic
    # as webstore seems to want 'data'. 
    
    tables = table_sets.tables
    table_count,counter = len(tables), 1
    for row_set in tables:
        if table_count == 1:
            table_name = _clean_name(resource['name'])                
        else:
            table_name = 'Sheet_%s' % (counter,)
            counter = counter + 1
        
        offset, headers = headers_guess(row_set.sample)
        row_set.register_processor(headers_processor(headers))
        row_set.register_processor(offset_processor(offset + 1))

        types = guess_types(list(row_set.dicts(sample=True)))
        row_set.register_processor(offset_processor(offset + 1))
        row_set.register_processor(types_processor(types))
        
        rows = []
        for row in row_set.dicts():
            rows.append(row)
            
        if len(rows) == 0:
            print 'No rows to upload'
            continue
        
        webstore_request_url = '%s/%s/%s' % (webstore_url,
                                             context['username'],
                                             resource['id']
                                             )
                                         
        #check if resource is already there.
        webstore_response = requests.get(webstore_request_url+'.json')
        print 'Checking for existing',webstore_response
        if not webstore_response.status_code:
            raise WebstorerError('Failed to connect to Webstore')        

        #should be an empty list as no tables should be there.
        check_dict = json.loads(webstore_response.content)
        if table_name in check_dict:
            raise WebstorerError('Webstore already has this resource')

        if not first_ws_url:
            first_ws_url = webstore_request_url + '/' + table_name
            
        print 'Saving ' + table_name
        response = requests.post(webstore_request_url+'/' + table_name,
                                 data = json.dumps(rows),
                                 headers = {'Content-Type': 'application/json',
                                            'Authorization': context['apikey']},
                                 )
        if response.status_code != 201:
            raise WebstorerError('Webstore bad response code (%s). Response was %s'%
                                 (response.status_code, response.content)
                                )

    try:
        if first_ws_url:
            # If we have at least uploaded one item
            ckan_url = context['site_url'].rstrip('/')
            ckan_request_url =  ckan_url + '/api/action/resource_update'

            ckan_resource_data = {
                'id': resource["id"],
                'webstore_url': first_ws_url,
                'webstore_last_updated': datetime.datetime.now().isoformat()
            }
            
            # If we have determined mimetype ....
            if 'mimetype' in resource and resource['mimetype']:
                ckan_resource_data['mimetype'] = resource['mimetype']

            response = requests.post(
                ckan_request_url,
                data=json.dumps(ckan_resource_data),
                headers = {'Content-Type': 'application/json',
                           'Authorization': context['apikey']},
                )

            if response.status_code not in (201, 200):
                raise WebstorerError('Ckan bad response code (%s). Response was %s'%
                                     (response.status_code, response.content)
                                    )
    except Exception, eckan:
        print eckan
        
        