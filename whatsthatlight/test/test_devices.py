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
        print('Off => None')
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
        print('Off => None')
        device.off()
        time.sleep(wait_time)

        # Close
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


if __name__ == '__main__':
    unittest.main()
