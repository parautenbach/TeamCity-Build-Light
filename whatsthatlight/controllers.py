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
Service controllers for controlling a device and client connection together.
"""

# System imports
import threading
import logging


class Controller(object):
    """
    Controller for controlling a device and client connection together.
    """

    def __init__(self, device, device_monitor, server_monitor):
        """
        Constructor.

        :param device: A device.
        :param device_monitor: A device monitor.
        :param server_monitor: A server monitor.
        """
        self._logger = logging.getLogger()
        self._device = device
        self._device_monitor = device_monitor
        self._server_monitor = server_monitor
        self._device_connected = False
        self._build_state = (None, None)

    def start(self):
        """
        Start the controller and dependencies.
        """

        event = threading.Event()

        def _device_added_handler():
            """
            Device added handler.
            """
            self._logger.info('Device added (vid=%0#6x, pid=%0#6x)',
                              self._device.get_vendor_id(),
                              self._device.get_product_id())
            self._device.open()
            (any_builds_running, any_build_failures) = self._build_state
            self._device.send(any_builds_running, any_build_failures)
            self._device.close()
            self._device_connected = True
            event.set()

        def _device_removed_handler():
            """
            Device removed handler.
            """
            self._logger.info('Device removed')
            self._device_connected = False

        def _server_handler(any_builds_running, any_build_failures):
            """
            Server handler.

            :param any_builds_running: True if any builds running. None if unknown or undefined.
            :param any_build_failures: True if any builds failing or failed. None if unknown or undefined.
            """
            self._build_state = (any_builds_running, any_build_failures)
            self._logger.debug('Build server state: any_builds_running={any_builds_running}, any_build_failures={any_build_failures}'
                               .format(any_builds_running=any_builds_running,
                                       any_build_failures=any_build_failures))
            if self._device_connected:
                # Warning: Abstraction bleeding: There can be only one open handle to the device
                # at any given time. Because we're using the same device for polling and updating
                # state, from two different contexts, we need to open the device only when we are
                # going to write, and immediately close it thereafter. Now, because of the two
                # polling loops (in the two monitors) there is of course the possibility of a
                # race condition, where the two loops will coincide: The one loop will open the
                # device, but before closing, the other loop will also open it. This will cause the
                # hidapi to blow up.
                self._logger.debug('Device connected; setting state')
                self._device.open()
                self._device.send(any_builds_running, any_build_failures)
                self._device.close()

        # Set handlers
        self._device_monitor.set_added_handler(_device_added_handler)
        self._device_monitor.set_removed_handler(_device_removed_handler)
        self._server_monitor.set_handler(_server_handler)

        # Synchronised start
        event.clear()
        self._device_monitor.start()
        event.wait(1)
        self._server_monitor.start()

    def stop(self):
        """
        Stop the controller and dependencies.
        """
        if self._device_connected:
            self._device.open()
            self._device.off()
            self._device.close()
        self._server_monitor.stop()
        self._device_monitor.stop()
