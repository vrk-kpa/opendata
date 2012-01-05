import json
import messytables
from messytables import CSVTableSet, XLSTableSet, types_processor, headers_guess, headers_processor, \
  offset_processor 
from ckan.lib.celery_app import celery
import requests
import datetime


DATA_FORMATS = [ 
    'csv',
    'text/csv',
    'txt',
    'text/plain',
    'xls',
    'application/ms-excel',
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
    excel_types = ['xls', 'application/ms-excel', 'application/xls']
    content_type = result['headers'].get('content-type', '')
    f = open(result['saved_file'], 'rb')

    if content_type in excel_types or resource['format'] in excel_types:
        table_sets = XLSTableSet.from_fileobj(f)
    else:
        table_sets = CSVTableSet.from_fileobj(f)

    ##only first sheet in xls for time being
    row_set = table_sets.tables[0]
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
    
    #TODO: Check we want username (as opposed to user id) here
    webstore_request_url = '%s/%s/%s' % (webstore_url,
                                         context['username'],
                                         resource['id']
                                         )
    #check if resource is already there.
    webstore_response = requests.get(webstore_request_url+'.json')
    if not webstore_response.status_code:
        raise WebstorerError('Failed to connect to Webstore')        
#    check_response_and_retry(webstore_response, webstore_request_url+'.json')

    #should be an empty list as no tables should be there.
    if json.loads(webstore_response.content)['data']:
        raise WebstorerError('Webstore already has this resource')

    response = requests.post(webstore_request_url+'/data',
                             data = json.dumps(rows),
                             headers = {'Content-Type': 'application/json',
                                        'Authorization': context['apikey']},
                             )
#    check_response_and_retry(response, webstore_request_url+'.json')
    if response.status_code != 201:
        raise WebstorerError('Websore bad response code (%s). Response was %s'%
                             (response.status_code, response.content)
                            )

    ckan_url = context['site_url'].rstrip('/')
    ckan_request_url =  ckan_url + '/api/action/resource_update'

    ckan_resource_data = {
        'id': resource["id"],
        'webstore_url': webstore_request_url+'/data',
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
                