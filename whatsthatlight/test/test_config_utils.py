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
Test the configuration utilities module.
"""

# System imports
import logging.config
import os
import StringIO
import unittest

# Local imports
from whatsthatlight import clients
from whatsthatlight import devices
from whatsthatlight import config_utils


class TestConfigUtils(unittest.TestCase):
    """
    Tests for the configuration utilities module.
    """

    def setUp(self):
        """
        Test setup.
        """
        logging.config.fileConfig('../conf/build_light.ini')

    def test_argument_parser(self):
        """
        Test correct creation of the argument parser.
        """
        expected_config_option = '[--config CONFIG]'
        expected_version_option = '[-v]'
        expected_application_name = 'foo'
        expected_application_version = 'bar'
        parser = config_utils.create_argument_parser(expected_application_name, expected_application_version)

        # Check usage
        output = StringIO.StringIO()
        parser.print_usage(file=output)
        output.flush()
        output.seek(0)
        output_string = output.read()
        output.close()
        self.assertIn(expected_config_option, output_string)
        self.assertIn(expected_version_option, output_string)

        # Check help
        output = StringIO.StringIO()
        parser.print_version(file=output)
        output.flush()
        output.seek(0)
        output_string = output.read()
        output.close()
        self.assertIn(expected_application_name, output_string)
        self.assertIn(expected_application_version, output_string)

    def test_try_get_config_path(self):
        """
        Test that resolving the configuration path is done correctly.
        """
        # Command-line argument must override everything else
        override_config_path = 'override.ini'
        arguments = _MockArguments()
        arguments.config = override_config_path
        global_config_path = 'global.ini'
        local_config_path = 'local.ini'
        open(override_config_path, 'a').close()
        open(global_config_path, 'a').close()
        open(local_config_path, 'a').close()
        actual_config_path = config_utils.try_get_config_path(arguments, global_config_path, local_config_path)
        os.remove(override_config_path)
        os.remove(global_config_path)
        os.remove(local_config_path)
        self.assertEqual(override_config_path, actual_config_path)

        # Command-line argument was specified, but the file does not exist
        expected_config_path = 'no_such_file.ini'
        arguments = _MockArguments()
        arguments.config = expected_config_path
        global_config_path = 'global.ini'
        local_config_path = 'local.ini'
        if os.path.exists(expected_config_path):
            os.remove(expected_config_path)
        self.assertRaisesRegexp(Exception,
                                'specify a valid config file',
                                config_utils.try_get_config_path,
                                arguments,
                                global_config_path,
                                local_config_path)

        # No command-line argument, but global ini exists, and takes precedence over local ini
        arguments = _MockArguments()
        global_config_path = 'global.ini'
        local_config_path = 'local.ini'
        open(global_config_path, 'a').close()
        open(local_config_path, 'a').close()
        actual_config_path = config_utils.try_get_config_path(arguments, global_config_path, local_config_path)
        os.remove(global_config_path)
        os.remove(local_config_path)
        self.assertEqual(global_config_path, actual_config_path)

        # Nothing but the local ini exists
        arguments = _MockArguments()
        global_config_path = 'global.ini'
        local_config_path = 'local.ini'
        open(local_config_path, 'a').close()
        actual_config_path = config_utils.try_get_config_path(arguments, global_config_path, local_config_path)
        os.remove(local_config_path)
        self.assertEqual(local_config_path, actual_config_path)

        # Nothing exists
        arguments = _MockArguments()
        global_config_path = 'global.ini'
        local_config_path = 'local.ini'
        self.assertRaisesRegexp(Exception, 'Unable to locate',
                                config_utils.try_get_config_path,
                                arguments,
                                global_config_path,
                                local_config_path)

    def test_create_config_parser(self):
        """
        Test a config parser can be created from file.
        """
        # File exists
        expected_config_path = 'test.ini'
        open(expected_config_path, 'a').close()
        config_utils.create_config_parser(expected_config_path)
        os.remove(expected_config_path)

        # File does not exist
        self.assertRaisesRegexp(Exception, 'Invalid config file', config_utils.create_config_parser, expected_config_path)

    def test_create_logger(self):
        """
        Test that a valid logger is created from a configuration file path.
        """
        expected_config_path = 'test.ini'
        config_content = [
            '[loggers]',
            'keys=root',
            '',
            '[handlers]',
            'keys=consoleHandler,rotatingFileHandler',
            '',
            '[formatters]',
            'keys=defaultFormatter',
            '',
            '[logger_root]',
            'level=DEBUG',
            'handlers=consoleHandler,rotatingFileHandler',
            '',
            '[handler_consoleHandler]',
            'class=StreamHandler',
            'formatter=defaultFormatter',
            'args=(sys.stdout,)',
            '',
            '[handler_rotatingFileHandler]',
            'class=handlers.RotatingFileHandler',
            'formatter=defaultFormatter',
            'args=(\'no_such.log\',)',
            '',
            '[formatter_defaultFormatter]',
            'format=%(asctime)s %(levelname)s [%(threadName)s] (%(module)s:%(funcName)s:%(lineno)s) - %(message)s',
            'datefmt='
        ]
        with open(name=expected_config_path, mode='w') as config_file_handle:
            config_file_handle.writelines(['{0}\n'.format(line) for line in config_content])
        open(expected_config_path, 'a').close()
        logger = config_utils.create_logger(expected_config_path)
        os.remove(expected_config_path)
        self.assertIsNotNone(logger)

    def test_load_device(self):
        """
        Test that an device can be loaded from config.
        """
        # Test parameters
        config_file = 'test.ini'
        expected_device_namespace = 'whatsthatlight.devices'
        expected_device_class_name = 'HidApiDevice'
        expected_device_class = devices.HidApiDevice
        expected_device_vid = 0x0001
        expected_device_pid = 0x0002
        expected_device_hid_module = 'hid'

        # Write a config file
        config_content = [
            '[device]',
            'namespace={0}'.format(expected_device_namespace),
            'class_name={0}'.format(expected_device_class_name),
            'vid={0}'.format(expected_device_vid),
            'pid={0}'.format(expected_device_pid),
            'hid_module={0}'.format(expected_device_hid_module),
            "args=(%(vid)s,%(pid)s,'%(hid_module)s',)",
        ]
        with open(name=config_file, mode='w') as config_file_handle:
            config_file_handle.writelines(['{0}\n'.format(line) for line in config_content])

        # Execute
        config_parser = config_utils.create_config_parser(config_file)
        device = config_utils.load_device(config_parser)
        os.remove(config_file)

        # Test
        self.assertIsNotNone(device)
        self.assertIsInstance(device, expected_device_class)

    def test_load_client(self):
        """
        Test that a client can be loaded from config.
        """
        # Test parameters
        config_file = 'test.ini'
        expected_client_namespace = 'whatsthatlight.clients'
        expected_client_class_name = 'TeamCityClient'
        expected_client_class = clients.TeamCityClient
        expected_server_url = 'http://example.com/'
        expected_server_username = 'user'
        expected_server_password = 'pass'

        # Write a config file
        config_content = [
            '[server]',
            'namespace={0}'.format(expected_client_namespace),
            'class_name={0}'.format(expected_client_class_name),
            'server_url={0}'.format(expected_server_url),
            'username={0}'.format(expected_server_username),
            'password={0}'.format(expected_server_password),
            "args=('%(server_url)s','%(username)s','%(password)s',)",
        ]
        with open(name=config_file, mode='w') as config_file_handle:
            config_file_handle.writelines(['{0}\n'.format(line) for line in config_content])

        # Execute
        config_parser = config_utils.create_config_parser(config_file)
        client = config_utils.load_client(config_parser)
        os.remove(config_file)

        # Test
        self.assertIsNotNone(client)
        self.assertIsInstance(client, expected_client_class)


class _MockArguments(object):
    """
    Mock arguments.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.config = None


if __name__ == '__main__':
    unittest.main()
