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

"""
Devices.
"""

# Local imports
# from whatsthatlight import parser


class DeviceError(Exception):
    """
    Generic device exception.
    """


class HidApiDevice(object):
    """
    Wrapper class for an HID device using the Cython HID API module.
    """

    def __init__(self, vendor_id, product_id, hidapi):
        """
        Constructor.
        :param vendor_id: the device's VID
        :param product_id: the device's PID
        :param hidapi: An imported HID API package
        """
        self._packet_size = 64
        self._timeout = 50
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._device = hidapi.device()
        self._is_open = False

    def get_vendor_id(self):
        """
        Get the vendor ID of the device.
        """
        return self._vendor_id

    def get_product_id(self):
        """
        Get the product ID of the device.
        """
        return self._product_id

    def open(self):
        """
        Open the device for communication.
        """
        self._device.open(self._vendor_id, self._product_id)
        self._is_open = True

    def is_open(self):
        """
        Check whether the device is open for communication.
        """
        return self._is_open

    def write(self, data):
        """
        Write raw data.
        :param data: the binary data
        """
        nr_of_bytes = self._device.write(data)
        if nr_of_bytes != len(data):
            raise DeviceError('Could not write all data: {0}/{1} bytes'.format(nr_of_bytes, len(data)))

    def close(self):
        """
        Close the device for communication.
        """
        self._device.close()
        self._is_open = False
