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
Tests for various monitors.
"""

# System imports
import threading
import unittest

# Third-party imports
from mockito import mock, when

# Local imports
from whatsthatlight import devices
from whatsthatlight import monitors
from whatsthatlight import clients


class TestDeviceMonitor(unittest.TestCase):
    """
    Device monitor tests.
    """

    @staticmethod
    def test_start_stop():
        """
        Test the start and stop behaviour.
        """
        # Setup
        device = mock(devices.BaseDevice)
        device_monitor = monitors.DeviceMonitor(device=device,
                                                polling_interval=0.1)

        # Execute
        device_monitor.start()
        device_monitor.stop()

    def test_added_removed(self):
        """
        Test that the added and removed events are triggered correctly.
        """
        # Test parameters
        nr_of_events = 5
        actual_events = []
        expected_events = ['added', 'removed', 'added', 'removed', 'added']
        polling_interval = 0.1

        # Mocks
        device = mock(devices.BaseDevice)
        (when(device).open()
         # No change, as we assuming no device is plugged in when started
         .thenRaise(IOError())
         # Now a device was plugged in
         .thenReturn(None)
         # Plugged out
         .thenRaise(IOError())
         # Plugged in
         .thenReturn(None)
         # Plugged out
         .thenRaise(IOError())
         # Plugged in
         .thenReturn(None))

        # Setup
        wait_event = threading.Event()
        wait_event.clear()
        device_monitor = monitors.DeviceMonitor(device=device,
                                                polling_interval=polling_interval)

        # Handlers
        def added():
            """
            A device added handler.
            """
            actual_events.append('added')
            if len(actual_events) == nr_of_events:
                wait_event.set()

        def removed():
            """
            A device removed handler.
            """
            actual_events.append('removed')
            if len(actual_events) == nr_of_events:
                wait_event.set()

        # Execute
        device_monitor.set_added_handler(added)
        device_monitor.set_removed_handler(removed)
        device_monitor.start()
        wait_event.wait(2 * nr_of_events * polling_interval)
        device_monitor.stop()

        # Test
        self.assertTrue(wait_event.is_set(), 'The expected number of events were not triggered')
        self.assertListEqual(expected_events, actual_events, 'Unexpected events or events order')


class TestServerMonitor(unittest.TestCase):
    """
    Server monitor tests.
    """

    @staticmethod
    def test_start_stop():
        """
        Test the start and stop behaviour.
        """
        client = mock(clients.TeamCityClient)
        server_monitor = monitors.ServerMonitor(client=client,
                                                polling_interval=0.1)
        server_monitor.start()
        server_monitor.stop()

    def test_handler(self):
        """
        Test invocation of the handler.
        """
        # Test parameters
        expected_any_builds_running = True
        expected_any_build_failures = False
        polling_interval = 0.1

        # Callback closure
        server_events = []
        event = threading.Event()

        def handler(any_builds_running, any_build_failures):
            """
            Test handler.

            :param any_builds_running: True if any builds running. None if unknown or undefined.
            :param any_build_failures: True if any builds failing or failed. None if unknown or undefined.
            """
            server_events.append((any_builds_running, any_build_failures))
            event.set()

        # Mocks
        client = mock(clients.TeamCityClient)
        when(client).any_builds_running().thenReturn(expected_any_builds_running)
        when(client).any_build_failures().thenReturn(expected_any_build_failures)

        # Execute
        server_monitor = monitors.ServerMonitor(client=client,
                                                polling_interval=polling_interval)
        server_monitor.set_handler(handler)
        event.clear()
        server_monitor.start()
        event.wait(2 * polling_interval)
        server_monitor.stop()

        # Test
        self.assertTrue(event.is_set(), 'Timeout')
        self.assertEqual(1, len(server_events))
        (actual_any_builds_running, actual_any_build_failures) = server_events[0]
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)
        self.assertEqual(actual_any_build_failures, expected_any_build_failures)

    def test_client_exception(self):
        """
        Test invocation of the handler when an exception is raised.
        """
        # Test parameters
        expected_any_builds_running = None
        expected_any_build_failures = None
        polling_interval = 0.1

        # Callback closure
        server_events = []
        event = threading.Event()

        def handler(any_builds_running, any_build_failures):
            """
            Test handler.

            :param any_builds_running: True if any builds running. None if unknown or undefined.
            :param any_build_failures: True if any builds failing or failed. None if unknown or undefined.
            """
            server_events.append((any_builds_running, any_build_failures))
            event.set()

        # Mocks
        client = mock(clients.TeamCityClient)
        when(client).any_builds_running().thenRaise(Exception('Test exception'))

        # Execute
        server_monitor = monitors.ServerMonitor(client=client,
                                                polling_interval=polling_interval)
        server_monitor.set_handler(handler)
        event.clear()
        server_monitor.start()
        event.wait(2 * polling_interval)
        server_monitor.stop()

        # Test
        self.assertTrue(event.is_set(), 'Timeout')
        self.assertEqual(1, len(server_events))
        (actual_any_builds_running, actual_any_build_failures) = server_events[0]
        self.assertEqual(actual_any_builds_running, expected_any_builds_running)
        self.assertEqual(actual_any_build_failures, expected_any_build_failures)


if __name__ == '__main__':
    unittest.main()
