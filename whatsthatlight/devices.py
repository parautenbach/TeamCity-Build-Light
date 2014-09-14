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
import threading
import time


class Device(object):
    """
    An abstract device.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod  # pragma: no cover
    def get_vendor_id(self):
        """
        Get the vendor ID of the device.
        """

    @abc.abstractmethod  # pragma: no cover
    def get_product_id(self):
        """
        Get the product ID of the device.
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
    def write(self, data):
        """
        Write raw data.
        :param data: The binary data.
        """

    @abc.abstractmethod  # pragma: no cover
    def close(self):
        """
        Close the device for communication.
        """


class HidApiDevice(Device):
    """
    Wrapper class for an HID device using the Cython HID API module.
    """

    def __init__(self, vendor_id, product_id, hidapi):
        """
        Constructor.
        :param vendor_id: The device's VID.
        :param product_id: The device's PID.
        :param hidapi: An imported HID API package.
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
        :param data: The binary data.
        """
        nr_of_bytes = self._device.write(data)
        if nr_of_bytes != len(data):
            raise IOError('Could not write all data: {0}/{1} bytes'.format(nr_of_bytes, len(data)))

    def close(self):
        """
        Close the device for communication.
        """
        self._device.close()
        self._is_open = False


class DeviceMonitor(object):
    """
    A simple polling device monitor, to have something that works across commonly platforms.
    """

    def __init__(self, device, interval=1):
        """
        Constructor.

        :param device: A Device instance.
        :param interval: The polling interval in seconds, as a float.
        """
        self._device = device
        self._connected = False
        self._running = False
        self._thread = None
        self._added_handler = None
        self._removed_handler = None
        self._interval = interval

    def start(self):
        """
        Start to poll.
        """
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def stop(self):
        """
        Stop polling.
        """
        self._running = False
        self._thread.join()

    def set_added_handler(self, handler):
        """
        Set a handler for when a device gets plugged in.

        :param handler: Parameterless function.
        """
        self._added_handler = handler

    def set_removed_handler(self, handler):
        """
        Set a handler for when a device gets plugged out.

        :param handler: Parameterless function.
        """
        self._removed_handler = handler

    def _run(self):
        """
        Polling thread.
        """
        self._running = True
        while self._running:
            try:
                self._device.open()
                could_open = True
                self._device.close()
            except IOError:
                could_open = False
            if self._connected and not could_open and self._removed_handler:
                # The device was plugged out
                self._connected = False
                self._removed_handler()
            elif not self._connected and could_open and self._added_handler:
                # The device was plugged in
                self._connected = True
                self._added_handler()
            # else:
            time.sleep(self._interval)
