# pylint: disable=too-many-lines
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
        body = """
                   {{
                       "href": "{resource}?locator=personal:false,canceled:false,running:true"
                   }}
               """.format(resource=resource)
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

        # Resources
        builds_resource = '/httpAuth/app/rest/builds/'
        build_resource = '{builds_resource}id:376'.format(builds_resource=builds_resource)
        changes_resource = '/httpAuth/app/rest/changes'
        change_detail_resource = '/httpAuth/app/rest/changes/id:68'

        # List of running builds
        running_builds_body = """
            {{
                "count": 1,
                "build":
                    [
                        {{
                            "href": "{build_resource}",
                            "buildTypeId": "Test_TestFoo",
                            "id": 376
                        }}
                    ]
            }}""".format(build_resource=build_resource)
        running_builds_response = (200, {}, running_builds_body)

        # The running build
        running_build_body = """
            {{
                    "id": 376,
                    "state": "running",
                    "buildTypeId": "Test_TestFoo",
                    "status": "SUCCESS",
                    "triggered":
                        {{
                            "type": "user",
                            "user":
                                {{
                                    "username": "{username}"
                                }}
                        }},
                    "running": true,
                    "changes":
                        {{
                            "href": "{changes_resource}?locator=build:(id:376)"
                        }}
            }}""".format(username=username, changes_resource=changes_resource)
        running_build_response = (200, {}, running_build_body)

        # Changes for build
        changes_body = """
            {{
                "change":
                    [
                        {{
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "{username}"
                        }}
                    ],
                "count": 1,
                "href": "/httpAuth/app/rest/changes?locator=build:(id:376)"
            }}
            """.format(username=username)
        changes_response = (200, {}, changes_body)

        # Change detail for a given change
        change_detail_body = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "user":
                    {{
                        "href": "/httpAuth/app/rest/users/id:1",
                        "id": 1,
                        "name": "Administrator",
                        "username": "{username}"
                    }},
                "username": "foo"
            }}
            """.format(username=username)
        change_detail_response = (200, {}, change_detail_body)

        # Assemble responses
        responses = {
            expected_verb: {
                builds_resource: [running_builds_response],
                build_resource: [running_build_response],
                changes_resource: [changes_response],
                change_detail_resource: [change_detail_response]
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
        self.assertEqual(4, len(requests))
        for (actual_verb, _, actual_headers) in requests:
            self.assertEqual(actual_verb, expected_verb)
            self.assertDictContainsSubset(expected_headers_subset, actual_headers)
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)

    def test_any_builds_running_positive_vcs_user_different(self):
        """
        Test for when there are builds running and the VCS user is mapped to the current user.
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

        # Resources
        builds_resource = '/httpAuth/app/rest/builds/'
        build_resource = '{builds_resource}id:376'.format(builds_resource=builds_resource)
        changes_resource = '/httpAuth/app/rest/changes'
        change_detail_resource = '/httpAuth/app/rest/changes/id:68'

        # List of running builds
        running_builds_body = """
            {{
                "count": 1,
                "build":
                    [
                        {{
                            "href": "{build_resource}",
                            "buildTypeId": "Test_TestFoo",
                            "id": 376
                        }}
                    ]
            }}""".format(build_resource=build_resource)
        running_builds_response = (200, {}, running_builds_body)

        # The running build
        running_build_body = """
            {{
                    "id": 376,
                    "state": "running",
                    "buildTypeId": "Test_TestFoo",
                    "status": "SUCCESS",
                    "triggered":
                        {{
                            "type": "user",
                            "user":
                                {{
                                    "username": "{username}"
                                }}
                        }},
                    "running": true,
                    "changes":
                        {{
                            "href": "{changes_resource}?locator=build:(id:376)"
                        }}
            }}""".format(username=username, changes_resource=changes_resource)
        running_build_response = (200, {}, running_build_body)

        # Changes for build
        changes_body = """
            {{
                "change":
                    [
                        {{
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "{username}"
                        }}
                    ],
                "count": 1,
                "href": "/httpAuth/app/rest/changes?locator=build:(id:376)"
            }}
            """.format(username=username)
        changes_response = (200, {}, changes_body)

        # Change detail for a given change
        change_detail_body = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "user":
                    {{
                        "href": "/httpAuth/app/rest/users/id:1",
                        "id": 1,
                        "name": "Administrator",
                        "username": "{username}"
                    }},
                "username": "foo"
            }}
            """.format(username=username)
        change_detail_response = (200, {}, change_detail_body)

        # Assemble responses
        responses = {
            expected_verb: {
                builds_resource: [running_builds_response],
                build_resource: [running_build_response],
                changes_resource: [changes_response],
                change_detail_resource: [change_detail_response]
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
        self.assertEqual(4, len(requests))
        for (actual_verb, _, actual_headers) in requests:
            self.assertEqual(actual_verb, expected_verb)
            self.assertDictContainsSubset(expected_headers_subset, actual_headers)
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)

    def test_any_builds_running_positive_multiple_builds(self):
        """
        Test for when there are multiple builds running.
        """
        # Expectations
        expected_any_builds_running = True
        expected_verb = 'GET'

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'

        # Resources
        builds_resource = '/httpAuth/app/rest/builds/'
        build_resource1 = '{builds_resource}id:376'.format(builds_resource=builds_resource)
        build_resource2 = '{builds_resource}id:377'.format(builds_resource=builds_resource)
        changes_resource = '/httpAuth/app/rest/changes'
        change_detail_resource = '/httpAuth/app/rest/changes/id:68'

        # List of running builds
        running_builds_body = """
            {{
                "count": 2,
                "build":
                    [
                        {{
                            "href": "{build_resource1}",
                            "buildTypeId": "Test_TestFoo",
                            "id": 376
                        }},
                        {{
                            "href": "{build_resource2}",
                            "buildTypeId": "Test_TestBar",
                            "id": 377
                        }}
                    ]
            }}""".format(build_resource1=build_resource1,
                         build_resource2=build_resource2)
        running_builds_response = (200, {}, running_builds_body)

        # The running builds
        running_build_body1 = """
            {{
                    "id": 376,
                    "state": "running",
                    "buildTypeId": "Test_TestFoo",
                    "status": "SUCCESS",
                    "triggered":
                        {{
                            "type": "schedule"
                        }},
                    "running": true,
                    "changes":
                        {{
                            "href": "{changes_resource}?locator=build:(id:376)"
                        }}
            }}""".format(username=username, changes_resource=changes_resource)
        running_build_response1 = (200, {}, running_build_body1)
        running_build_body2 = """
            {{
                    "id": 377,
                    "state": "running",
                    "buildTypeId": "Test_TestBar",
                    "status": "SUCCESS",
                    "triggered":
                        {{
                            "type": "schedule"
                        }},
                    "running": true,
                    "changes":
                        {{
                            "href": "{changes_resource}?locator=build:(id:377)"
                        }}
            }}""".format(username=username, changes_resource=changes_resource)
        running_build_response2 = (200, {}, running_build_body2)

        # Changes for build
        changes_body1 = """
            {
                "change":
                    [
                        {
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "foo"
                        }
                    ],
                "count": 1,
                "href": "/httpAuth/app/rest/changes?locator=build:(id:367)"
            }
            """
        changes_response1 = (200, {}, changes_body1)
        changes_body2 = """
            {{
                "change":
                    [
                        {{
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "{username}"
                        }}
                    ],
                "count": 1,
                "href": "/httpAuth/app/rest/changes?locator=build:(id:367)"
            }}
            """.format(username=username)
        changes_response2 = (200, {}, changes_body2)

        # Change detail for a given change
        change_detail_body1 = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "user":
                    {{
                        "href": "/httpAuth/app/rest/users/id:1",
                        "id": 1,
                        "name": "Administrator",
                        "username": "bar"
                    }},
                "username": "foo"
            }}
            """.format(username=username)
        change_detail_response1 = (200, {}, change_detail_body1)
        change_detail_body2 = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "user":
                    {{
                        "href": "/httpAuth/app/rest/users/id:1",
                        "id": 1,
                        "name": "Administrator",
                        "username": "{username}"
                    }},
                "username": "foo"
            }}
            """.format(username=username)
        change_detail_response2 = (200, {}, change_detail_body2)

        # Assemble responses
        responses = {
            expected_verb: {
                builds_resource: [running_builds_response],
                build_resource1: [running_build_response1],
                build_resource2: [running_build_response2],
                changes_resource: [changes_response1,
                                   changes_response2],
                change_detail_resource: [change_detail_response1,
                                         change_detail_response2]
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
        self.assertEqual(7, len(requests))
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)

    def test_any_builds_running_positive_multiple_contributors(self):
        """
        Test for when there are builds with multiple contributors running.
        """
        # Expectations
        expected_any_builds_running = True
        expected_verb = 'GET'

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'

        # Resources
        builds_resource = '/httpAuth/app/rest/builds/'
        build_resource = '{builds_resource}id:376'.format(builds_resource=builds_resource)
        changes_resource = '/httpAuth/app/rest/changes'
        change_detail_resource = '/httpAuth/app/rest/changes/id:68'

        # List of running builds
        running_builds_body = """
            {{
                "count": 1,
                "build":
                    [
                        {{
                            "href": "{build_resource}",
                            "buildTypeId": "Test_TestFoo",
                            "id": 376
                        }}
                    ]
            }}""".format(build_resource=build_resource)
        running_builds_response = (200, {}, running_builds_body)

        # The running build
        running_build_body = """
            {{
                    "id": 376,
                    "state": "running",
                    "buildTypeId": "Test_TestFoo",
                    "status": "SUCCESS",
                    "triggered":
                        {{
                            "type": "user",
                            "user":
                                {{
                                    "username": "{username}"
                                }}
                        }},
                    "running": true,
                    "changes":
                        {{
                            "href": "{changes_resource}?locator=build:(id:376)"
                        }}
            }}""".format(username=username, changes_resource=changes_resource)
        running_build_response = (200, {}, running_build_body)

        # Changes for build
        changes_body = """
            {{
                "change":
                    [
                        {{
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "foo"
                        }},
                        {{
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "{username}"
                        }}
                    ],
                "count": 1,
                "href": "/httpAuth/app/rest/changes?locator=build:(id:367)"
            }}
            """.format(username=username)
        changes_response = (200, {}, changes_body)

        # Change detail for a given change
        change_detail_body_other = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "username": "foo"
            }}
            """.format(username=username)
        change_detail_response_other = (200, {}, change_detail_body_other)

        # Change detail for a given change
        change_detail_body = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "user":
                    {{
                        "href": "/httpAuth/app/rest/users/id:1",
                        "id": 1,
                        "name": "Administrator",
                        "username": "{username}"
                    }},
                "username": "bas"
            }}
            """.format(username=username)
        change_detail_response = (200, {}, change_detail_body)

        # Assemble responses
        responses = {
            expected_verb: {
                builds_resource: [running_builds_response],
                build_resource: [running_build_response],
                changes_resource: [changes_response],
                change_detail_resource: [change_detail_response_other,
                                         change_detail_response]
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
        self.assertEqual(5, len(requests))
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)

    def test_any_builds_running_positive_triggered_by(self):
        """
        Test for when there are builds running where the user triggered it.
        """
        # Expectations
        expected_any_builds_running = True
        expected_verb = 'GET'

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'

        # Resources
        builds_resource = '/httpAuth/app/rest/builds/'
        build_resource = '{builds_resource}id:376'.format(builds_resource=builds_resource)
        changes_resource = '/httpAuth/app/rest/changes'

        # List of running builds
        running_builds_body = """
            {{
                "count": 1,
                "build":
                    [
                        {{
                            "href": "{build_resource}",
                            "buildTypeId": "Test_TestFoo",
                            "id": 376
                        }}
                    ]
            }}""".format(build_resource=build_resource)
        running_builds_response = (200, {}, running_builds_body)

        # The running build
        running_build_body = """
            {{
                    "id": 376,
                    "state": "running",
                    "buildTypeId": "Test_TestFoo",
                    "status": "SUCCESS",
                    "triggered":
                        {{
                            "type": "user",
                            "user":
                                {{
                                    "username": "{username}"
                                }}
                        }},
                    "running": true,
                    "changes":
                        {{
                            "href": "{changes_resource}?locator=build:(id:376)"
                        }}
            }}""".format(username=username, changes_resource=changes_resource)
        running_build_response = (200, {}, running_build_body)

        # Changes for build
        changes_body = """
            {{
                "href": "/httpAuth/app/rest/changes?locator=build:(id:367)"
            }}
            """.format(username=username)
        changes_response = (200, {}, changes_body)

        # Assemble responses
        responses = {
            expected_verb: {
                builds_resource: [running_builds_response],
                build_resource: [running_build_response],
                changes_resource: [changes_response]
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
        self.assertEqual(3, len(requests))
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)

    def test_any_build_failures_positive(self):
        """
        Test for when there is a build in a failed state.
        """
        # Expectations
        expected_any_build_failures = True
        expected_verb = 'GET'

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'

        # Resources
        build_types_resource = '/httpAuth/app/rest/buildTypes'
        build_resource_a = '/httpAuth/app/rest/builds/id:378'
        changes_resource = '/httpAuth/app/rest/changes'
        change_detail_resource = '/httpAuth/app/rest/changes/id:68'

        # A list of builds
        build_types_body = """
                           {
                               "count": 1,
                               "buildType": [
                                               {"id": "TestProject_BuildConfigA"}
                                           ]
                           }
                           """
        build_types_response = (200, {}, build_types_body)
        build_type_resource = '/httpAuth/app/rest/builds/'
        build_type_body_status_failure = """
            {
                "count": 1,
                "build":
                    [
                        {
                            "href": "/httpAuth/app/rest/builds/id:378"
                        }
                    ]
            }"""
        build_types_response_a = (200, {}, build_type_body_status_failure)

        # A failing build
        build_a = """
            {{
                    "id": 378,
                    "state": "running",
                    "buildTypeId": "Test_TestFoo",
                    "status": "FAILURE",
                    "triggered":
                        {{
                            "type": "user",
                            "user":
                                {{
                                    "username": "{username}"
                                }}
                        }},
                    "running": true,
                    "changes":
                        {{
                            "href": "{changes_resource}?locator=build:(id:378)"
                        }}
            }}
        """.format(username=username, changes_resource=changes_resource)
        build_response_a = (200, {}, build_a)

        # Changes
        changes_body = """
            {{
                "change":
                    [
                        {{
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "{username}"
                        }}
                    ],
                "count": 1,
                "href": "/httpAuth/app/rest/changes?locator=build:(id:378)"
            }}
            """.format(username=username)
        changes_response = (200, {}, changes_body)

        # Change detail for a given change
        change_detail_body = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "user":
                    {{
                        "href": "/httpAuth/app/rest/users/id:1",
                        "id": 1,
                        "name": "Administrator",
                        "username": "{username}"
                    }},
                "username": "foo"
            }}
            """.format(username=username)
        change_detail_response = (200, {}, change_detail_body)

        # Assembly responses
        responses = {
            expected_verb: {
                build_types_resource: [build_types_response],
                build_type_resource: [build_types_response_a],
                build_resource_a: [build_response_a],
                changes_resource: [changes_response],
                change_detail_resource: [change_detail_response]
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
            actual_any_build_failures = client.any_build_failures()
            event.wait()
        finally:
            client.disconnect()
            server.stop()

        # Test
        self.assertEqual(5, len(requests))
        self.assertEqual(actual_any_build_failures, expected_any_build_failures)

    def test_any_build_failures_positive_multiple_failed_builds(self):
        """
        Test for when there are builds in a failed state, but only the last one is due to the user.
        """
        # Expectations
        expected_any_build_failures = True
        expected_verb = 'GET'

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'

        # Resources
        build_types_resource = '/httpAuth/app/rest/buildTypes'
        build_resource_a = '/httpAuth/app/rest/builds/id:378'
        build_resource_b = '/httpAuth/app/rest/builds/id:379'
        build_resource_c = '/httpAuth/app/rest/builds/id:380'
        build_resource_d = '/httpAuth/app/rest/builds/id:381'
        changes_resource = '/httpAuth/app/rest/changes'
        change_detail_resource = '/httpAuth/app/rest/changes/id:68'

        # A list of builds
        build_types_body = """
                           {
                               "count": 2,
                               "buildType": [
                                               {"id": "TestProject_BuildConfigA"},
                                               {"id": "TestProject_BuildConfigB"}
                                           ]
                           }
                           """
        build_types_response = (200, {}, build_types_body)
        build_type_resource = '/httpAuth/app/rest/builds/'
        build_type_body_status_failure_a = """
            {
                "count": 2,
                "build":
                    [
                        {
                            "href": "/httpAuth/app/rest/builds/id:378"
                        },
                        {
                            "href": "/httpAuth/app/rest/builds/id:379"
                        }
                    ]
            }"""
        build_types_response_a = (200, {}, build_type_body_status_failure_a)
        build_type_body_status_failure_b = """
            {
                "count": 2,
                "build":
                    [
                        {
                            "href": "/httpAuth/app/rest/builds/id:380"
                        },
                        {
                            "href": "/httpAuth/app/rest/builds/id:381"
                        }
                    ]
            }"""
        build_types_response_b = (200, {}, build_type_body_status_failure_b)

        # Failing builds
        build = """
            {{
                    "id": 378,
                    "state": "running",
                    "buildTypeId": "TestProject_BuildConfigA",
                    "status": "FAILURE",
                    "triggered":
                        {{
                            "type": "user",
                            "user":
                                {{
                                    "username": "foo"
                                }}
                        }},
                    "running": true,
                    "changes":
                        {{
                            "href": "{changes_resource}?locator=build:(id:378)"
                        }}
            }}
        """.format(username=username, changes_resource=changes_resource)
        build_response = (200, {}, build)

        # Changes
        changes_body_other = """
            {
                "change":
                    [
                        {
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "foo"
                        }
                    ],
                "count": 1,
                "href": "/httpAuth/app/rest/changes?locator=build:(id:378)"
            }
            """
        changes_response_other = (200, {}, changes_body_other)
        changes_body = """
            {{
                "change":
                    [
                        {{
                            "date": "20140928T150722+0200",
                            "href": "/httpAuth/app/rest/changes/id:68",
                            "id": 68,
                            "username": "{username}"
                        }}
                    ],
                "count": 1,
                "href": "/httpAuth/app/rest/changes?locator=build:(id:381)"
            }}
            """.format(username=username)
        changes_response = (200, {}, changes_body)

        # Change detail for a given change
        change_detail_body_other = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "user":
                    {{
                        "href": "/httpAuth/app/rest/users/id:1",
                        "id": 1,
                        "name": "Administrator",
                        "username": "bar"
                    }},
                "username": "foo"
            }}
            """.format(username=username)
        change_detail_response_other = (200, {}, change_detail_body_other)

        # Change detail for a given change
        change_detail_body = """
            {{
                "href": "/httpAuth/app/rest/changes/id:76",
                "id": 76,
                "user":
                    {{
                        "href": "/httpAuth/app/rest/users/id:1",
                        "id": 1,
                        "name": "Administrator",
                        "username": "{username}"
                    }},
                "username": "foo"
            }}
            """.format(username=username)
        change_detail_response = (200, {}, change_detail_body)

        # Assembly responses
        responses = {
            expected_verb: {
                build_types_resource: [build_types_response],
                build_type_resource: [build_types_response_a, build_types_response_b],
                build_resource_a: [build_response],
                build_resource_b: [build_response],
                build_resource_c: [build_response],
                build_resource_d: [build_response],
                changes_resource: [changes_response_other,
                                   changes_response_other,
                                   changes_response_other,
                                   changes_response],
                change_detail_resource: [change_detail_response_other,
                                         change_detail_response_other,
                                         change_detail_response_other,
                                         change_detail_response]
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
            actual_any_build_failures = client.any_build_failures()
            event.wait()
        finally:
            client.disconnect()
            server.stop()

        # Test
        self.assertEqual(15, len(requests))
        self.assertEqual(actual_any_build_failures, expected_any_build_failures)

    def test_any_build_failures_negative(self):
        """
        Test for when there are no builds in a failed state.
        """
        # Expectations
        expected_any_build_failures = False
        expected_verb = 'GET'

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'
        build_types_resource = '/httpAuth/app/rest/buildTypes'
        build_types_body = """
                           {
                               "count": 5,
                               "buildType": [
                                               {"id": "TestProject_BuildConfigA"},
                                               {"id": "TestProject_BuildConfigB"},
                                               {"id": "TestProject_BuildConfigC"},
                                               {"id": "TestProject_BuildConfigD"},
                                               {"id": "TestProject_BuildConfigE"}
                                           ]
                           }
                           """
        build_types_response = (200, {}, build_types_body)
        build_type_resource = '/httpAuth/app/rest/builds/'
        build_type_body_status_success = '{}'
        build_types_response_a = (200, {}, build_type_body_status_success)
        build_types_response_b = (200, {}, build_type_body_status_success)
        build_types_response_c = (200, {}, build_type_body_status_success)
        build_types_response_d = (200, {}, build_type_body_status_success)
        build_types_response_e = (200, {}, build_type_body_status_success)
        responses = {
            expected_verb: {
                build_types_resource: [build_types_response],
                build_type_resource: [build_types_response_a,
                                      build_types_response_b,
                                      build_types_response_c,
                                      build_types_response_d,
                                      build_types_response_e]
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
            actual_any_build_failures = client.any_build_failures()
            event.wait()
        finally:
            client.disconnect()
            server.stop()

        # Test
        self.assertEqual(6, len(requests))
        self.assertEqual(actual_any_build_failures, expected_any_build_failures)

    def test_any_build_failures_negative_no_data(self):
        """
        Test for when there are builds in a failed state.
        """
        # Expectations
        expected_any_build_failures = False
        expected_verb = 'GET'

        # Test parameters
        host = 'localhost'
        port = utils.get_available_port()
        server_url = 'http://{0}:{1}/'.format(host, port)
        username = 'admin'
        password = 'admin'
        build_types_resource = '/httpAuth/app/rest/buildTypes'
        build_types_body = '{}'
        build_types_response = (200, {}, build_types_body)
        responses = {
            expected_verb: {
                build_types_resource: [build_types_response]
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
            actual_any_build_failures = client.any_build_failures()
            event.wait()
        finally:
            client.disconnect()
            server.stop()

        # Test
        self.assertEqual(1, len(requests))
        self.assertEqual(actual_any_build_failures, expected_any_build_failures)


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
