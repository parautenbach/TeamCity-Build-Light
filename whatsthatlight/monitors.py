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
Various monitors.
"""

# System imports
import threading
import time


class DeviceMonitor(object):
    """
    A simple polling device monitor, to have something that works across commonly platforms.
    """

    def __init__(self, device, polling_interval=1):
        """
        Constructor.

        :param device: A Device instance.
        :param polling_interval: The polling interval in seconds, as a float.
        """
        self._device = device
        self._connected = False
        self._running = False
        self._thread = None
        self._added_handler = None
        self._removed_handler = None
        self._polling_interval = polling_interval

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
            time.sleep(self._polling_interval)


class ServerMonitor(object):
    """
    Monitors a build server.
    """

    def __init__(self, client, polling_interval=5):
        """
        Constructor.

        :param client: A build server client.
        :param polling_interval: The interval, in seconds, between checks.
        """
        self._client = client
        self._polling_interval = polling_interval
        self._handler = None
        self._running = False
        self._thread = None

    def start(self):
        """
        Start the monitor.
        """
        self._client.connect()
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def stop(self):
        """
        Stop the monitor.
        """
        self._running = False
        self._thread.join()
        self._client.disconnect()

    def set_handler(self, handler):
        """
        Set a handler for when any builds are running.

        :param handler: A function which accept the parameters (any_builds_running, any_build_failures),
                        where both parameters are boolean. A value if None indicates an undefined or unknown
                        state.
        """
        self._handler = handler

    def _run(self):
        """
        Polling thread.
        """
        self._running = True
        while self._running:
            if self._handler:
                # noinspection PyBroadException
                # pylint: disable=bare-except
                try:
                    any_builds_running = self._client.any_builds_running()
                    any_build_failures = self._client.any_build_failures()
                    self._handler(any_builds_running, any_build_failures)
                except:
                    self._handler(None, None)
                # pylint: enable=bare-except
            time.sleep(self._polling_interval)
