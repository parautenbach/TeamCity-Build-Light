# Copyright 2013 Pieter Rautenbach
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-many-locals
# pylint: disable=invalid-name
# pylint: disable=too-many-statements
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-instance-attributes
# pylint: disable=duplicate-code
# pylint: disable=too-many-public-methods
# pylint: disable=no-member

"""
Tests for various clients.
"""

# System imports
import BaseHTTPServer
import SocketServer
import threading
import unittest

# Third-party imports
# from mockito import mock, when

# Local imports
from whatsthatlight import clients
from whatsthatlight.test import utils


class TestTeamCityClient(unittest.TestCase):
    """
    TeamCity client tests.
    """

    @staticmethod
    def test_connect_disconnect():
        """
        Test the start and stop behaviour.
        """
        client = clients.TeamCityClient(server_url=None, username=None, password=None)
        client.connect()
        client.disconnect()

    def test_any_builds_running_negative(self):
        """
        Test for when there are no builds running.
        """
        # Expectations
        expected_any_builds_running = False
        expected_verb = 'GET'
        expected_headers_subset = {
            'Accept': 'application/json'
        }

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'
        resource = '/httpAuth/app/rest/builds/'
        body = ('{{"href": "{resource}?locator=user:{username},personal:false,canceled:false,running:true,count:1"}}'
                .format(resource=resource,
                        username=username))
        response = (200, {}, body)
        responses = {
            expected_verb: {
                resource: [response]
            }
        }
        event = threading.Event()
        requests = []

        # Callback
        # noinspection PyUnusedLocal
        def _callback(verb, path, headers):
            """
            Callback closure to capture responses.
            """
            requests.append((verb, path, headers))
            event.set()

        # Setup
        client = clients.TeamCityClient(server_url=server_url,
                                        username=username,
                                        password=password)
        server = _SimpleHttpServer(host=host,
                                   port=port,
                                   callback=_callback,
                                   responses=responses)

        # Execute
        try:
            server.start()
            client.connect()
            event.clear()
            actual_any_builds_running = client.any_builds_running()
            event.wait()
        finally:
            client.disconnect()
            server.stop()

        # Test
        self.assertEqual(1, len(requests))
        (actual_verb, _, actual_headers) = requests[0]
        self.assertEqual(actual_verb, expected_verb)
        self.assertDictContainsSubset(expected_headers_subset, actual_headers)
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)

    def test_any_builds_running_positive(self):
        """
        Test for when there are builds running.
        """
        # Expectations
        expected_any_builds_running = True
        expected_verb = 'GET'
        expected_headers_subset = {
            'Accept': 'application/json'
        }

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'
        resource = '/httpAuth/app/rest/builds/'
        body = ('{{"href": "{resource}?locator=user:{username},personal:false,canceled:false,running:true,count:1", "count": "1"}}'
                .format(resource=resource,
                        username=username))
        response = (200, {}, body)
        responses = {
            expected_verb: {
                resource: [response]
            }
        }
        event = threading.Event()
        requests = []

        # Callback
        # noinspection PyUnusedLocal
        def _callback(verb, path, headers):
            """
            Callback closure to capture responses.
            """
            requests.append((verb, path, headers))
            event.set()

        # Setup
        client = clients.TeamCityClient(server_url=server_url,
                                        username=username,
                                        password=password)
        server = _SimpleHttpServer(host=host,
                                   port=port,
                                   callback=_callback,
                                   responses=responses)

        # Execute
        try:
            server.start()
            client.connect()
            event.clear()
            actual_any_builds_running = client.any_builds_running()
            event.wait()
        finally:
            client.disconnect()
            server.stop()

        # Test
        self.assertEqual(1, len(requests))
        (actual_verb, _, actual_headers) = requests[0]
        self.assertEqual(actual_verb, expected_verb)
        self.assertDictContainsSubset(expected_headers_subset, actual_headers)
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)


class _SimpleHttpServer(object):
    """
    A simple HTTP server for testing.
    """

    def __init__(self, host, port, callback, responses):
        """
        Constructor.

        :param host: The server host.
        :param port: The server port.
        :param callback: The callback(verb, path, headers) function to invoke when a request is received.
        :param responses: A data structure where the first dictionary key is the verb, the second the resource,
                          and the value the ordered list of responses. The response value is a
                          (status_code, headers, body) tuple.
        """

        self._callback = callback
        self._responses = responses
        parent = self

        class _HttpCallbackHandler(BaseHTTPServer.BaseHTTPRequestHandler):
            """
            A request handler that invokes a callback.
            """

            # noinspection PyPep8Naming
            def do_GET(self):
                """
                Handle a GET request.
                """
                verb = 'GET'
                resource = self.path.split('?')[0]
                # pylint: disable=protected-access
                response = parent._responses[verb][resource].pop(0)
                # pylint: enable=protected-access
                (status_code, headers, body) = response
                self.send_response(status_code)
                for (field, value) in headers:
                    self.send_header(field, value)
                self.end_headers()
                self.wfile.write(body)
                callback(verb, self.path, self.headers)

        self._httpd = SocketServer.TCPServer((host, port), _HttpCallbackHandler)
        self._httpd.allow_reuse_address = True
        self._thread = threading.Thread(target=self._httpd.serve_forever)

    def start(self):
        """
        Start the server.
        """
        self._thread.start()

    def stop(self):
        """
        Stop the server.
        """
        self._httpd.shutdown()
        self._thread.join()