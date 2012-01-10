import sys
import json
import messytables
from messytables import CSVTableSet, XLSTableSet, types_processor, headers_guess, headers_processor, \
  offset_processor 
import requests
import datetime

DATA_FORMATS = [ 
    'csv',
    'text/csv',
    'txt',
    'text/plain',
    'xls',
    'application/ms-excel',
    'application/vnd.ms-excel',
    'application/xls',
    'application/octet-stream'
]

def guess_types(rows):
    ''' Simple guess types of fields, only allowed are int, float and string'''

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
                
                
def upload_content(context, resource, result):
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
    # first sheet). We'd also need to name each sheet
    
    row_set = table_sets.tables[0]
    table_name = 'data'
    offset, headers = headers_guess(row_set.sample)
    row_set.register_processor(headers_processor(headers))
    row_set.register_processor(offset_processor(offset + 1))
#    row_set.register_processor(datetime_processor())

    types = guess_types(list(row_set.dicts(sample=True)))
    row_set.register_processor(offset_processor(offset + 1))
    row_set.register_processor(types_processor(types))
    
    rows = []
    
    for row in row_set.dicts():
        rows.append(row)

    if not context.get('webstore_url'):
        raise WebstorerError('Configuration error: "ckan.webstore_url" is not defined.')

    webstore_url = context.get('webstore_url').rstrip('/')
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
    if json.loads(webstore_response.content)[table_name]:
        raise WebstorerError('Webstore already has this resource')

    response = requests.post(webstore_request_url+'/' + table_name,
                             data = json.dumps(rows),
                             headers = {'Content-Type': 'application/json',
                                        'Authorization': context['apikey']},
                             )
    if response.status_code != 201:
        raise WebstorerError('Websore bad response code (%s). Response was %s'%
                             (response.status_code, response.content)
                            )

    try:
        ckan_url = context['site_url'].rstrip('/')
        ckan_request_url =  ckan_url + '/api/action/resource_update'

        ckan_resource_data = {
            'id': resource["id"],
            'webstore_url': webstore_request_url+'/' + table_name,
            'webstore_last_updated': datetime.datetime.now().isoformat()
        }

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
        
        