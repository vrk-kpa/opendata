"""
The QA Resource Controller

This controller exposes only one action: check_link
"""
import json
import mimetypes
import posixpath
import urllib
import urlparse

from ckan.lib.base import request
from ckan.lib.helpers import parse_rfc_2822_date

from ckanext.archiver.tasks import link_checker, LinkCheckerError

from ckanext.qa.controllers.base import QAController

class QAResourceController(QAController):

    def check_link(self):
        """
        Checks the given urls by making a HEAD request for them.

        Returns a list of dicts (one for each url) containing information
        gathered about that url.  Serialized as json.

        Each dict in the returned list has the form: ::

        {
          'url_errors': [ list of error messages that indicate the url is bad ],
          'inner_format': "A guess at the inner-most format",
          'format': "A guess at nested formats",
          'mimetype': "The mimetype returned in the HEAD request (Content-Type header)",
          'size': "The content-length returned in the HEAD request",
          'last_modified': "The 'last-modified' returned in the HEAD request",
        }

        where:

        url_errors : list of Strings corresponding to the following possible errors:
            * Invalid URL scheme (must be "http", "https" or "ftp")
            * Invalid URL (if the string doesn't seem to be a valid URL)
            * HTTP Error
            * Timeout
      
        format/inner_format: A best guess at the format of the file
            * a_file.csv has format "csv" and inner-format "csv"
            * a_file.csv.gz.torrent has inner-format "csv" and format "torrent:gz:csv"
            * This inspects the url and pulls out the file-extension(s) from it.
            * If that fails, then the "Content-Type" header is inspected, and passed to
              `mimetypes.guess_extension()` to make a reasonable guess at the file extension
            * May be None if unknown/un-guessable.

        mimetype: The Content-Type as returned in the HTTP headers
            * Stripped of character encoding parameters if they exist
            * Is the 'outer' mimetype as described in [2]

        size / last_modified: Just taken from the response headers.

        TODO:
        =====

         [ ] Maybe it's better to parse the url that the HEAD request gets
             redirected to.  eg [1] gets redirected to a listings page, [2] ?

             [1] http://www.ons.gov.uk/ons/dcp19975_226817.xml
             [2] http://www.ons.gov.uk/ons/rel/regional-trends/region-and-country-profiles/social-indicators/index.html
        """
        urls = request.GET.getall('url')
        result = [ self._check_link(url) for url in urls ]
        return json.dumps(result)

    def _check_link(self, url):
        """
        Synchronously check the given link, and return dict representing results.
        """

        # If a user enters "www.example.com" then we assume they meant "http://www.example.com"
        scheme, path = urllib.splittype(url)
        if not scheme:
            url = 'http://' + path

        context = {}
        data = {
            'url_timeout': 10,
            'url': url
        }
        result = {
            'errors': [],
            'url_errors': [],
            'inner_format': '',
            'format': '',
            'mimetype': '',
            'size': '',
            'last_modified': '',
        }

        try:
            headers = json.loads(link_checker(json.dumps(context), json.dumps(data)))
            result['format'] = ':'.join(self._extract_file_format(url, headers))
            result['inner_format'] = result['format'].split(':')[-1]
            result['mimetype'] = self._extract_mimetype(headers)
            result['size'] = headers.get('content-length', '')
            result['last_modified'] = self._parse_and_format_date(headers.get('last-modified', ''))
        except LinkCheckerError, e:
            result['url_errors'].append(str(e))
        return result

    def _extract_file_format(self, url, headers):
        """
        Makes a best guess at the file format.

        Returns a list of strings, with formats[0] being the outermost format.
        If no format can be found, then returns an empty list.

        /path/to/a_file.csv has format "csv"
        /path/to/a_file.csv.gz.torrent has format "torrent:gz:csv" (and inner-form "csv")

        First this function tries to extract the file-extensions from the url,
        and deduce the format from there.  If no file-extension is found, then
        the mimetype from the headers is passed to `mimetypes.guess_extension()`.
        """
        # Try to extract format from the file extension(s)
        formats = []
        parsed_url = urlparse.urlparse(url)
        path = parsed_url.path
        base, extension = posixpath.splitext(path)
        while extension:
            formats.append(extension[1:]) # strip leading '.' from extension
            base, extension = posixpath.splitext(base)
        if formats:
            return formats

        # No file extension found, attempt to extract format using the mimetype
        stripped_mimetype = self._extract_mimetype(headers) # stripped of charset
        extension = mimetypes.guess_extension(stripped_mimetype)
        return [extension[1:]] if extension else []

    def _extract_mimetype(self, headers):
        """
        The Content-Type in headers, stripped of character encoding parameters.
        """
        return headers.get('content-type', '').split(';')[0].strip()

    def _parse_and_format_date(self, date_string):
        """
        Parse date string in form specified in RFC 2822, and reformat to iso format.

        Returns the empty string if the date_string cannot be parsed
        """
        dt = parse_rfc_2822_date(date_string)

        # Remove timezone information, adjusting as necessary.
        if dt and dt.tzinfo:
            dt = (dt - dt.utcoffset()).replace(tzinfo=None)
        return dt.isoformat() if dt else ''

