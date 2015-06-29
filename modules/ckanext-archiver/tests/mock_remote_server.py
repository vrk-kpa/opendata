"""
An HTTP server that listens on localhost and returns a variety of responses for
mocking remote servers.
"""
from contextlib import contextmanager
from threading import Thread
from time import sleep
from wsgiref.simple_server import make_server
import urllib2
import socket
import os

class MockHTTPServer(object):
    """
    Mock HTTP server that can take the place of a remote server for testing
    fetching of remote resources.

    Uses contextmanager to allow easy setup and teardown of the WSGI server in
    a separate thread, eg::

        >>> with MockTestServer().serve() as server_address:
        ...     urllib2.urlopen(server_address)
        ...

    Subclass this and override __call__ to provide your own WSGI handler function.
    """

    def __call__(self, environ, start_response):
        raise NotImplementedError()

    @contextmanager
    def serve(self, host='localhost', port_range=(8000, 9000)):
        """
        Start an instance of wsgiref.simple_server set up to handle requests in
        a separate daemon thread.
        Return the address of the server eg ('http://localhost:8000').
        This uses context manager to make sure the server is stopped::

            >>> with MockTestServer().serve() as addr:
            ...     print urllib2.urlopen('%s/?content=hello+world').read()
            ...
            'hello world'
        """
        for port in range(*port_range):
            try:
                server = make_server(host, port, self)
            except socket.error:
                continue
            break
        else:
            raise Exception("Could not bind to a port in range %r" % (port_range,))

        serving = True

        def _serve_until_stopped():
            while serving:
                server.handle_request()

        thread = Thread(target=_serve_until_stopped)
        thread.daemon = True
        thread.start()
        try:
            yield 'http://%s:%d' % (host, port)
        finally:
            serving = False

            # Call the server to make sure the waiting handle_request()
            # call completes. Set a very small timeout as we don't actually need to
            # wait for a response. We don't care about exceptions here either.
            try:
                urllib2.urlopen("http://%s:%s/" % (host, port), timeout=0.01)
            except Exception:
                pass

    @classmethod
    def get_content(cls, varspec):
        """
        Return the value of the variable at varspec, which must be in the
        format 'package.module:variable'. If variable is callable, it will be
        called and its return value used.
        """
        modpath, var = varspec.split(':')
        mod = reduce(getattr, modpath.split('.')[1:], __import__(modpath))
        var = reduce(getattr, var.split('.'), mod)
        try:
            return var()
        except TypeError:
            return var

class MockEchoTestServer(MockHTTPServer):
    """
    WSGI application that echos back the status, headers and 
    content passed via the URL, eg:

        a 500 error response: 'http://localhost/?status=500'

        a 200 OK response, returning the function's docstring: 'http://localhost/?status=200;content-type=text/plain;content_var=ckan.tests.lib.test_package_search:test_wsgi_app.__doc__'

    To specify content, use:

        content=string
        content_var=package.module:variable
    """


    def __call__(self, environ, start_response):

        from httplib import responses
        from webob import Request
        request = Request(environ)
        status = int(request.str_params.get('status', '200'))
        ## if 'redirect' in redirect.str_params:
        ##     params = dict([(key, value) for param in request.str_params \
        ##                    if key != 'redirect'])
        ##     redirect_status = int(request.str_params['redirect'])
        ##     status = int(request.str_params.get('status', '200'))
        ##     resp = make_response(render_template('error.html'), redirect_status)
        ##     resp.headers['Location'] = url_for(request.path, params)
        ##     return resp
        if 'content_var' in request.str_params:
            content = request.str_params.get('content_var')
            content = self.get_content(content)
        elif 'content_long' in request.str_params:
            content = '*' * 1000001
        else:
            content = request.str_params.get('content', '')
        if 'method' in request.str_params \
               and request.method.lower() != request.str_params['method'].lower():
            content = ''
            status = 405

        if isinstance(content, unicode):
            raise TypeError("Expected raw byte string for content")

        headers = [
            item
            for item in request.str_params.items()
            if item[0] not in ('content', 'status')
        ]
        if 'length' in request.str_params:
            cl = request.str_params.get('length')
            headers += [('Content-Length', cl)]
        elif content and not 'no-content-length' in request.str_params:
            headers += [('Content-Length', str(len(content)))]
        start_response(
            '%d %s' % (status, responses[status]),
            headers
        )
        return [content]

class MockTimeoutTestServer(MockHTTPServer):
    """
    Sleeps ``timeout`` seconds before responding. Make sure that your timeout value is
    less than this to check handling timeout conditions.
    """
    def __init__(self, timeout):
        super(MockTimeoutTestServer, self).__init__()
        self.timeout = timeout

    def __call__(self, environ, start_response):
        # Sleep until self.timeout or the parent thread finishes
        sleep(self.timeout)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['xyz']

def get_file_content(data_filename):
    filepath = os.path.join(os.path.dirname(__file__), 'data', data_filename)
    assert os.path.exists(filepath), filepath
    with open(filepath, 'rb') as f:
        return f.read()

class MockWmsServer(MockHTTPServer):
    """Acts like an OGC WMS server (well, one basic call)
    """
    def __init__(self, wms_version='1.3'):
        self.wms_version = wms_version
        super(MockWmsServer, self).__init__()

    def __call__(self, environ, start_response):
        from httplib import responses
        from webob import Request
        request = Request(environ)
        status = int(request.str_params.get('status', '200'))
        headers = {'Content-Type': 'text/plain'} 
        # e.g. params ?service=WMS&request=GetCapabilities&version=1.1.1
        if request.str_params.get('service') != 'WMS':
            status = 200
            content = ERROR_WRONG_SERVICE
        elif request.str_params.get('request') != 'GetCapabilities':
            status = 405
            content = '"request" param wrong'
        elif 'version' in request.str_params and \
                request.str_params.get('version') != self.wms_version:
            status = 405
            content = '"version" not compatible - need to be %s' % self.wms_version
        elif self.wms_version == '1.1.1':
            status = 200
            content = get_file_content('wms_getcap_1.1.1.xml')
        elif self.wms_version == '1.3':
            status = 200
            content = get_file_content('wms_getcap_1.3.xml')
        start_response(
            '%d %s' % (status, responses[status]),
            headers.items()
        )
        return [content]

class MockWfsServer(MockHTTPServer):
    """Acts like an OGC WFS server (well, one basic call)
    """
    def __init__(self):
        super(MockWfsServer, self).__init__()

    def __call__(self, environ, start_response):
        from httplib import responses
        from webob import Request
        request = Request(environ)
        status = int(request.str_params.get('status', '200'))
        headers = {'Content-Type': 'text/plain'}
        # e.g. params ?service=WFS&request=GetCapabilities
        if request.str_params.get('service') != 'WFS':
            status = 200
            content = ERROR_WRONG_SERVICE
        elif request.str_params.get('request') != 'GetCapabilities':
            status = 405
            content = '"request" param wrong'
        else:
            status = 200
            content = get_file_content('wfs_getcap.xml')
        start_response(
            '%d %s' % (status, responses[status]),
            headers.items()
        )
        return [content]

ERROR_WRONG_SERVICE = "<ows:ExceptionReport version='1.1.0' language='en' xmlns:ows='http://www.opengis.net/ows'><ows:Exception exceptionCode='NoApplicableCode'><ows:ExceptionText>Wrong service type.</ows:ExceptionText></ows:Exception></ows:ExceptionReport>"
