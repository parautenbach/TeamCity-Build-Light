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
import importlib
import time
import unittest

# pylint: disable=redefined-builtin
from mockito import mock, when, any

# Local imports
from whatsthatlight import devices


class TestHidApiDevice(unittest.TestCase):
    """
    HID API device tests.
    """

    @unittest.skipIf(True, 'Manual test')
    def test_basic_sequence(self):
        """
        A basic open, write and close sequence against an actual device.
        """
        # Test parameters
        expected_vendor_id = 0x27b8
        expected_product_id = 0x01ed
        # We assume fade millis is 100ms, so we'll wait 1s
        wait_time = 2
        hidapi = importlib.import_module('hid')

        # Create
        device = devices.HidApiDevice(vendor_id=expected_vendor_id, product_id=expected_product_id, hidapi=hidapi)
        self.assertEqual(expected_vendor_id, device.get_vendor_id())
        self.assertEqual(expected_product_id, device.get_product_id())

        # Open
        device.open()
        self.assertTrue(device.is_open())

        # Off (none)
        print('Off')
        device.off()
        time.sleep(wait_time)

        # Unknown (blue)
        print('Unknown => Blue')
        device.send(any_builds_running=None, any_build_failures=None)
        time.sleep(wait_time)

        # Failure (red)
        print('Failure => Red')
        device.send(any_builds_running=False, any_build_failures=True)
        time.sleep(wait_time)

        # Running (yellow)
        print('Running => Yellow')
        device.send(any_builds_running=True, any_build_failures=False)
        time.sleep(wait_time)

        # Success (green)
        print('Success => Green')
        device.send(any_builds_running=False, any_build_failures=False)
        time.sleep(wait_time)

        # Off (none)
        print('Off')
        device.off()
        time.sleep(wait_time)

        # Close (twice, without problems)
        device.close()
        self.assertFalse(device.is_open())

    def test_write_device_error(self):
        """
        Test that an error is raised if not all data was written.
        """
        # Test parameters
        vendor_id = 0
        product_id = 0

        # Mocks
        hidapi = importlib.import_module('hid')
        mock_device = mock(hidapi.device)
        when(mock_device).write(any()).thenReturn(0)
        mock_hidapi = mock(hidapi)
        when(mock_hidapi).device().thenReturn(mock_device)

        # Test
        device = devices.HidApiDevice(vendor_id=vendor_id, product_id=product_id, hidapi=mock_hidapi)
        self.assertRaises(IOError, device.send, any_builds_running=None, any_build_failures=None)

    def test_open_close(self):
        """
        Test opening and closing the device.
        """
        # Test parameters
        vendor_id = 0
        product_id = 0

        # Mocks
        hidapi = importlib.import_module('hid')
        mock_device = mock(hidapi.device)
        when(mock_device).write(any()).thenReturn(8)
        mock_hidapi = mock(hidapi)
        when(mock_hidapi).device().thenReturn(mock_device)

        # Test
        device = devices.HidApiDevice(vendor_id=vendor_id, product_id=product_id, hidapi=mock_hidapi)
        device.open()
        self.assertTrue(device.is_open())
        device.close()
        self.assertFalse(device.is_open())

    def test_send_and_off(self):
        """
        Test sending information to the device.
        """
        # Test parameters
        expected_data = [[1, 99, 0, 200, 255, 0, 100, 0],
                         [1, 99, 0, 255, 0, 0, 100, 0],
                         [1, 99, 230, 0, 0, 0, 100, 0],
                         [1, 99, 200, 120, 0, 0, 100, 0],
                         [1, 99, 200, 120, 0, 0, 100, 0],
                         [1, 99, 0, 0, 0, 0, 100, 0]]
        vendor_id = 0
        product_id = 0

        actual_data = []

        def write(data):
            """
            Close for capturing data written to the device.

            :param data: The binary data.
            :return: The number of bytes written.
            """
            actual_data.append(data)
            return len(data)

        # Mocks
        hidapi = importlib.import_module('hid')
        mock_device = mock(hidapi.device)
        mock_device.write = write
        mock_hidapi = mock(hidapi)
        when(mock_hidapi).device().thenReturn(mock_device)

        # Execute
        device = devices.HidApiDevice(vendor_id=vendor_id, product_id=product_id, hidapi=mock_hidapi)
        device.send(None, None)
        device.send(False, False)
        device.send(False, True)
        device.send(True, False)
        device.send(True, True)
        device.off()

        # Test
        self.assertListEqual(actual_data, expected_data)

    # @unittest.skip
    # def test_(self):
    #     """
    #     Test
    #     """
    #     # Test parameters
    #     expected_vendor_id = 0x27b8
    #     expected_product_id = 0x01ed
    #     # We assume fade millis is 100ms, so we'll wait 1s
    #     wait_time = 1
    #     hidapi = importlib.import_module('hid')
    #
    #     # Create
    #     device = devices.HidApiDevice(vendor_id=expected_vendor_id, product_id=expected_product_id, hidapi=hidapi)
    #
    #     errors = []
    #
    #     def _run(any_builds_running, any_build_failures):
    #         """
    #         :param any_builds_running:
    #         :param any_build_failures:
    #         :return:
    #         """
    #         print(any_builds_running, any_build_failures)
    #         # pylint: disable=broad-except
    #         try:
    #             device.open()
    #             if device.is_open():
    #                 time.sleep(wait_time)
    #                 # print(any_builds_running, any_build_failures)
    #                 device.send(any_builds_running, any_build_failures)
    #                 print('wait1')
    #                 time.sleep(wait_time)
    #                 print('wait2')
    #                 device.close()
    #         except Exception, e:
    #             errors.append(e)
    #         # pylint: enable=broad-except
    #
    #     thread1 = threading.Thread(target=_run, args=(False, True))
    #     thread2 = threading.Thread(target=_run, args=(False, False))
    #
    #     thread1.start()
    #     thread2.start()
    #
    #     # Stop
    #     thread1.join()
    #     thread2.join()
    #     # And another close must no matter
    #     device.close()
    #     self.assertFalse(device.is_open())
    #     self.assertEqual(0, len(errors), errors)


if __name__ == '__main__':
    unittest.main()
