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
Tests for various devices.
"""

# System imports
import threading
import unittest

# Third-party imports
from mockito import mock, when

# Local imports
from whatsthatlight import devices


class TestHidApiDevice(unittest.TestCase):
    """
    HidApiDevice tests.
    """

    @staticmethod
    def test_start_stop():
        """
        Test the start and stop behaviour.
        """
        # Setup
        device = mock(devices.Device)
        device_monitor = devices.DeviceMonitor(device=device)

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
        interval = 0.1

        # Mocks
        device = mock(devices.Device)
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
        device_monitor = devices.DeviceMonitor(device=device, interval=interval)

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
        wait_event.wait(2 * nr_of_events * interval)
        device_monitor.stop()

        # Test
        self.assertTrue(wait_event.is_set(), 'The expected number of events were not triggered')
        self.assertListEqual(expected_events, actual_events, 'Unexpected events or events order')


if __name__ == '__main__':
    unittest.main()
