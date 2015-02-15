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
Tests for the controller.
"""

# System imports
import importlib
import logging
import logging.config
import signal
import subprocess
import sys
import threading
import time
import unittest

# Third-party imports
from mockito import mock, when

# Local imports
from whatsthatlight import clients
from whatsthatlight import controllers
from whatsthatlight import devices
from whatsthatlight import monitors
from whatsthatlight.test import constants


class TestController(unittest.TestCase):
    """
    Device monitor tests.
    """

    def setUp(self):
        """
        Test setup.
        """
        logging.config.fileConfig('../conf/build_light.ini')
        logger = logging.getLogger('build_light')
        logger.info('Logger set up')

    @staticmethod
    def test_start_stop():
        """
        Test the start and stop behaviour.
        """
        # Mocks
        device = mock(devices.BaseDevice)
        device_monitor = mock(monitors.DeviceMonitor)
        server_monitor = mock(monitors.ServerMonitor)

        # Setup
        controller = controllers.Controller(device=device,
                                            device_monitor=device_monitor,
                                            server_monitor=server_monitor)

        # Execute
        controller.start()
        controller.stop()

    @staticmethod
    @unittest.skipIf(constants.SKIP_MANUAL_TESTS, 'Manual test')
    def test_console():
        """
        Test the console script.
        """
        script = './scripts/run/build_light_dev'
        max_number_of_log_lines = 20
        log_substring_condition = 'Controller started'
        process = subprocess.Popen([script],
                                   cwd='..',
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        print('Subprocess ID: {0}'.format(process.pid))
        sys.stdout.flush()
        number_of_lines = 0
        while number_of_lines < max_number_of_log_lines:
            line = process.stdout.readline().strip()
            print('Scanning for started log message: {0}'.format(line))
            sys.stdout.flush()
            if log_substring_condition in line:
                print('Found started log message')
                sys.stdout.flush()
                break
            number_of_lines += 1
            time.sleep(0.01)
        process.send_signal(signal.SIGTERM)

    def test_initial_state_and_device_added(self):
        """
        Test that the initial state and device added state is set.
        """
        # Test parameters
        expected_nr_of_writes = 2
        expected_data_0 = (None, None)
        expected_any_builds_running_1 = True
        expected_any_build_failures_1 = False
        expected_data_1 = (expected_any_builds_running_1, expected_any_build_failures_1)
        polling_interval = 0.1

        device_data = []
        event = threading.Event()

        # Callback closure
        def send(any_builds_running, any_build_failures):
            """
            Sends build information to the device.

            :param any_builds_running: True if any builds running. None if unknown or undefined.
            :param any_build_failures: True if any builds failing or failed. None if unknown or undefined.
            """
            device_data.append((any_builds_running, any_build_failures))
            if len(device_data) == expected_nr_of_writes:
                event.set()

        # Mocks
        device = mock(devices.BaseDevice)
        when(device).get_vendor_id().thenReturn(0)
        when(device).get_product_id().thenReturn(0)
        device.send = send
        when(device).is_open().thenReturn(True)
        client = mock(clients.BaseClient)
        when(client).any_builds_running().thenReturn(expected_any_builds_running_1)
        when(client).any_build_failures().thenReturn(expected_any_build_failures_1)

        # Setup
        device_monitor = monitors.DeviceMonitor(device=device,
                                                polling_interval=1 * polling_interval)
        server_monitor = monitors.ServerMonitor(client=client,
                                                polling_interval=5 * polling_interval)
        controller = controllers.Controller(device=device,
                                            device_monitor=device_monitor,
                                            server_monitor=server_monitor)

        # Execute
        event.clear()
        controller.start()
        try:
            event.wait(5 * polling_interval)
        finally:
            controller.stop()

        # Test
        self.assertTrue(event.is_set(), 'Timeout')
        self.assertEqual(expected_nr_of_writes, len(device_data))
        actual_data = device_data[0]
        self.assertEqual(actual_data, expected_data_0)
        actual_data = device_data[1]
        self.assertEqual(actual_data, expected_data_1)

    @staticmethod
    @unittest.skipIf(constants.SKIP_MANUAL_TESTS, 'Manual test')
    def test_against_actual_device():
        """
        Test the controller works with an actual device.
        """
        # Test parameters
        expected_any_builds_running = True
        expected_any_build_failures = False
        polling_interval = 1
        vendor_id = 0x27b8
        product_id = 0x01ed
        hid_module = importlib.import_module('hid')

        # Mocks
        client = mock(clients.BaseClient)
        when(client).any_builds_running().thenReturn(expected_any_builds_running)
        when(client).any_build_failures().thenReturn(expected_any_build_failures)

        # Setup
        device = devices.HidApiDevice(vendor_id=vendor_id, product_id=product_id, hidapi=hid_module)
        device_monitor = monitors.DeviceMonitor(device=device,
                                                polling_interval=1 * polling_interval)
        server_monitor = monitors.ServerMonitor(client=client,
                                                polling_interval=5 * polling_interval)
        controller = controllers.Controller(device=device,
                                            device_monitor=device_monitor,
                                            server_monitor=server_monitor)

        # Execute
        controller.start()
        time.sleep(2 * polling_interval)
        controller.stop()
        time.sleep(2 * polling_interval)

    def test_no_device_no_write(self):
        """
        Test that when there is no device, nothing gets written to the device.
        """
        # Test parameters
        polling_interval = 0.2

        event = threading.Event()

        # Callback closure
        def write(any_builds_running, any_build_failures):
            """
            Write raw data.

            :param any_builds_running: True if any builds running. None if unknown or undefined.
            :param any_build_failures: True if any builds failing or failed. None if unknown or undefined.
            """
            print(any_builds_running, any_build_failures)
            event.set()

        # Mocks
        device = mock(devices.BaseDevice)
        device.write = write
        when(device).open().thenRaise(IOError('Test'))
        when(device).is_open().thenReturn(False)
        client = mock(clients.BaseClient)
        when(client).any_builds_running().thenReturn(None)
        when(client).any_build_failures().thenReturn(None)

        # Setup
        device_monitor = monitors.DeviceMonitor(device=device,
                                                polling_interval=polling_interval)
        server_monitor = monitors.ServerMonitor(client=client,
                                                polling_interval=polling_interval)
        controller = controllers.Controller(device=device,
                                            device_monitor=device_monitor,
                                            server_monitor=server_monitor)

        # Execute
        event.clear()
        controller.start()
        event.wait(2 * polling_interval)
        controller.stop()

        # Test
        self.assertFalse(event.is_set(), 'Data was written to the device')


if __name__ == '__main__':
    unittest.main()
