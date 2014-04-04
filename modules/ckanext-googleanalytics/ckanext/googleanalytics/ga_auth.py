import os
import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

from pylons import config


def _prepare_credentials(token_filename, credentials_filename):
    """
    Either returns the user's oauth credentials or uses the credentials
    file to generate a token (by forcing the user to login in the browser)
    """
    storage = Storage(token_filename)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flow = flow_from_clientsecrets(credentials_filename,
                scope='https://www.googleapis.com/auth/analytics.readonly',
                message="Can't find the credentials file")
        credentials = run(flow, storage)

    return credentials


def init_service(token_file, credentials_file):
    """
    Given a file containing the user's oauth token (and another with
    credentials in case we need to generate the token) will return a
    service object representing the analytics API.
    """
    http = httplib2.Http()

    credentials = _prepare_credentials(token_file, credentials_file)
    http = credentials.authorize(http)  # authorize the http object

    return build('analytics', 'v3', http=http)


def get_profile_id(service):
    """
    Get the profile ID for this user and the service specified by the
    'googleanalytics.id' configuration option. This function iterates
    over all of the accounts available to the user who invoked the
    service to find one where the account name matches (in case the
    user has several).
    """
    accounts = service.management().accounts().list().execute()

    if not accounts.get('items'):
        return None

    accountName = config.get('googleanalytics.account')
    webPropertyId = config.get('googleanalytics.id')
    for acc in accounts.get('items'):
        if acc.get('name') == accountName:
            accountId = acc.get('id')

    webproperties = service.management().webproperties().list(accountId=accountId).execute()

    profiles = service.management().profiles().list(
        accountId=accountId, webPropertyId=webPropertyId).execute()

    if profiles.get('items'):
        return profiles.get('items')[0].get('id')

    return None
