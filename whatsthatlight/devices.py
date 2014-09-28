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
Various USB light devices.
"""

# System imports
import abc


class BaseDevice(object):
    """
    An abstract device for blink(1) devices.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, vendor_id, product_id, hidapi):
        """
        Constructor.

        :param vendor_id: The device's VID.
        :param product_id: The device's PID.
        :param hidapi: An imported HID API package/module. Write a wrapper if you need to.
        """
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._device = hidapi.device()

    @abc.abstractmethod  # pragma: no cover
    def get_vendor_id(self):
        """
        Get the vendor ID of the device.

        :return: The VID.
        """

    @abc.abstractmethod  # pragma: no cover
    def get_product_id(self):
        """
        Get the product ID of the device.

        :return: The PID.
        """

    @abc.abstractmethod  # pragma: no cover
    def open(self):
        """
        Open the device for communication.
        """

    @abc.abstractmethod  # pragma: no cover
    def is_open(self):
        """
        Check whether the device is open for communication.
        """

    @abc.abstractmethod  # pragma: no cover
    def send(self, any_builds_running, any_build_failures):
        """
        Sends build information to the device.

        :param any_builds_running: True if any builds running. None if unknown or undefined.
        :param any_build_failures: True if any builds failing or failed. None if unknown or undefined.
        """

    @abc.abstractmethod  # pragma: no cover
    def off(self):
        """
        Switch off the device.
        """

    @abc.abstractmethod  # pragma: no cover
    def close(self):
        """
        Close the device for communication.
        """

    # TODO: Off


class HidApiDevice(BaseDevice):
    """
    Wrapper class for an HID device using the Cython HID API module.
    """

    _DEFAULT_FAILURE_COLOUR = (230, 0, 0)
    _DEFAULT_SUCCESS_COLOUR = (0, 255, 0)
    _DEFAULT_UNDEFINED_COLOUR = (0, 200, 255)
    _DEFAULT_RUNNING_COLOUR = (200, 120, 0)
    _OFF_COLOUR = (0, 0, 0)
    _LED_NUMBER = 0
    _FADE_MILLIS = 100

    def __init__(self, vendor_id, product_id, hidapi):
        """
        Constructor.

        :param vendor_id: The device's VID.
        :param product_id: The device's PID.
        :param hidapi: An imported HID API package/module.
        """
        super(HidApiDevice, self).__init__(vendor_id, product_id, hidapi)
        self._packet_size = 64
        self._timeout = 50
        self._is_open = False
        self._th = (self._FADE_MILLIS & 0xff00) >> 8
        self._tl = self._FADE_MILLIS & 0x00ff

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

    def _encode(self, any_builds_running, any_build_failures):
        """
        Encode build server state.

        :param any_builds_running: True if any builds running. None if unknown or undefined.
        :param any_build_failures: True if any builds failing or failed. None if unknown or undefined.
        :return: Binary data.
        """
        # Running builds take precedence
        if any_builds_running is True:
            return self._create_packet(HidApiDevice._DEFAULT_RUNNING_COLOUR)
        elif any_build_failures is True:
            return self._create_packet(HidApiDevice._DEFAULT_FAILURE_COLOUR)
        elif any_build_failures is False:
            return self._create_packet(HidApiDevice._DEFAULT_SUCCESS_COLOUR)
        else:
            return self._create_packet(HidApiDevice._DEFAULT_UNDEFINED_COLOUR)

    def _create_packet(self, colour):
        """
        Create a binary data packet from a RGB colour tuple.

        :param colour: An RGB colour tuple.
        :return: Binary data.
        """
        (red, green, blue) = colour
        return [0x01, 0x63, red, green, blue, self._th, self._tl, HidApiDevice._LED_NUMBER]

    def send(self, any_builds_running, any_build_failures):
        """
        Sends build information to the device.

        :param any_builds_running: True if any builds running. None if unknown or undefined.
        :param any_build_failures: True if any builds failing or failed. None if unknown or undefined.
        """
        data = self._encode(any_builds_running, any_build_failures)
        self._write(data)

    def _write(self, data):
        """
        Internal write.

        :param data: Binary data.
        """
        nr_of_bytes = self._device.write(data)
        if nr_of_bytes != len(data):
            raise IOError('Could not write all data: {0}/{1} bytes'.format(nr_of_bytes, len(data)))

    def off(self):
        """
        Switch off the device.
        """
        data = self._create_packet(self._OFF_COLOUR)
        self._write(data)

    def close(self):
        """
        Close the device for communication.
        """
        if self.is_open():
            self._device.close()
        self._is_open = False
