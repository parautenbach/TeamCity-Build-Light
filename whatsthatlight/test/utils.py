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
Test utilities.
"""

# System imports
import socket


def get_available_port():
    """
    Uses socket default behaviour to get open port. Is not 100% reliable, as the port can be closed in the time between
    when this function is called and when its return value is used, but should be good enough for testing.

    :return: An available port as an int value.
    """
    server_socket = socket.socket()
    server_socket.bind(('', 0))
    port = server_socket.getsockname()[1]
    server_socket.close()
    return port
