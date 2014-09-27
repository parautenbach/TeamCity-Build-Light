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

"""
Config module tests.
"""

# System imports
import os
import unittest
import uuid

# Local imports
from whatsthatlight import config


class TestConfig(unittest.TestCase):
    """
    Config module tests.
    """

    def test_helpers(self):
        """
        Test the config helpers.
        """
        # Test parameters
        # Device
        expected_device_namespace = 'whatsthatlight.devices'
        expected_device_class_name = 'HidApiDevice'
        expected_device_vid = 0x0001
        expected_device_pid = 0x0002
        expected_device_hid_module = 'hid'
        expected_device_args = (expected_device_vid, expected_device_pid, expected_device_hid_module)
        # Server
        expected_client_namespace = 'whatsthatlight.clients'
        expected_client_class_name = 'TeamCityClient'
        expected_server_url = 'http://example.com/'
        expected_server_username = 'user'
        expected_server_password = 'pass'
        expected_client_args = (expected_server_url, expected_server_username, expected_server_password)

        # An INI file definition
        config_content = [
            '[DEFAULT]',
            '',
            '[device]',
            'namespace={0}'.format(expected_device_namespace),
            'class_name={0}'.format(expected_device_class_name),
            'vid={0}'.format(expected_device_vid),
            'pid={0}'.format(expected_device_pid),
            'hid_module={0}'.format(expected_device_hid_module),
            "args=(%(vid)s,%(pid)s,'%(hid_module)s',)",
            '',
            '[server]',
            'namespace={0}'.format(expected_client_namespace),
            'class_name={0}'.format(expected_client_class_name),
            'server_url={0}'.format(expected_server_url),
            'username={0}'.format(expected_server_username),
            'password={0}'.format(expected_server_password),
            "args=('%(server_url)s','%(username)s','%(password)s',)"
        ]
        config_file = '{0}.ini'.format(uuid.uuid1())
        with open(name=config_file, mode='w') as config_file_handle:
            config_file_handle.writelines(['{0}\n'.format(line) for line in config_content])

        # Load
        config_parser = config.ConfigParser()
        config_parser.read(filename=config_file)

        # Test
        try:
            # Device
            actual_device_namespace = config.get_device_namespace(config_parser)
            actual_device_class_name = config.get_device_class_name(config_parser)
            actual_device_args = config.get_device_args(config_parser)
            self.assertEqual(expected_device_namespace, actual_device_namespace)
            self.assertEqual(expected_device_class_name, actual_device_class_name)
            self.assertEqual(expected_device_args, actual_device_args)
            # Server
            actual_client_namespace = config.get_client_namespace(config_parser)
            actual_client_class_name = config.get_client_class_name(config_parser)
            actual_client_args = config.get_client_args(config_parser)
            self.assertEqual(expected_client_namespace, actual_client_namespace)
            self.assertEqual(expected_client_class_name, actual_client_class_name)
            self.assertEqual(expected_client_args, actual_client_args)
        finally:
            # Clean-up
            os.remove(config_file)


if __name__ == '__main__':
    unittest.main()
