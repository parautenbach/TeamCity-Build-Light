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
Tests.
"""

# System imports
import time
import unittest

# Local imports
from whatsthatlight import devices


class MyTestCase(unittest.TestCase):
    """
    Tests.
    """

    def test_something(self):
        """
        No test.
        """
        # Test parameters
        expected_vendor_id = 0x27b8
        expected_product_id = 0x01ed
        red = 0
        green = 200
        blue = 200
        fade_millis = 100
        th = (fade_millis & 0xff00) >> 8
        tl = fade_millis & 0x00ff
        led_number = 0
        off_data = [0x01, 0x63, 0, 0, 0, th, tl, led_number]
        light_blue_data = [0x01, 0x63, red, green, blue, th, tl, led_number]

        # Create
        device = devices.HidApiDevice(vendor_id=expected_vendor_id, product_id=expected_product_id)
        self.assertEqual(expected_vendor_id, device.get_vendor_id())
        self.assertEqual(expected_product_id, device.get_product_id())

        # Open
        device.open()
        self.assertTrue(device.is_open())

        # Off
        device.write(off_data)
        time.sleep(fade_millis/1000.0)

        # Light blue
        device.write(light_blue_data)
        time.sleep(10*fade_millis/1000.0)

        # Off
        device.write(off_data)
        time.sleep(fade_millis/1000.0)

        # Close
        device.close()
        self.assertFalse(device.is_open())


if __name__ == '__main__':
    unittest.main()
