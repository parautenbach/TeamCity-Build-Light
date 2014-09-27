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
Configuration module.
"""

# System imports
import ast
import ConfigParser as BuiltinConfigParser

# Constants
# Sections
_DEFAULT_SECTION = 'DEFAULT'
_DEVICE_SECTION = 'device'
_SERVER_SECTION = 'server'
# Default options
# Generic (common/shared) options
NAMESPACE_OPTION = 'namespace'
CLASS_NAME_OPTION = 'class_name'
CONSTRUCTOR_ARGS_OPTION = 'args'


def get_device_namespace(config_parser):
    """
    Get the device namespace.

    :param config_parser: A configuration parser.
    :returns: The namespace.
    """
    return config_parser.get(_DEVICE_SECTION, NAMESPACE_OPTION)


def get_device_class_name(config_parser):
    """
    Get device class name.

    :param config_parser: A configuration parser.
    :returns: The class name.
    """
    return config_parser.get(_DEVICE_SECTION, CLASS_NAME_OPTION)


def get_device_args(config_parser):
    """
    Get the device constructor arguments.

    :param config_parser: A configuration parser.
    :returns: The argument tuple.
    """
    return ast.literal_eval(config_parser.get(_DEVICE_SECTION, CONSTRUCTOR_ARGS_OPTION))


def get_client_namespace(config_parser):
    """
    Get the client namespace.

    :param config_parser: A configuration parser.
    :returns: The namespace.
    """
    return config_parser.get(_SERVER_SECTION, NAMESPACE_OPTION)


def get_client_class_name(config_parser):
    """
    Get client class name.

    :param config_parser: A configuration parser.
    :returns: The class name.
    """
    return config_parser.get(_SERVER_SECTION, CLASS_NAME_OPTION)


def get_client_args(config_parser):
    """
    Get the client constructor arguments.

    :param config_parser: A configuration parser.
    :returns: The argument tuple.
    """
    return ast.literal_eval(config_parser.get(_SERVER_SECTION, CONSTRUCTOR_ARGS_OPTION))


class ConfigParser(BuiltinConfigParser.SafeConfigParser):
    """
    An extension of the built-in SafeConfigParser.
    """

    def __init__(self):
        """
        Constructor.
        """
        # SafeConfigParser is an old style class, so we can't use super(ConfigParser, self).__init__()
        BuiltinConfigParser.SafeConfigParser.__init__(self)

    def read(self, filename):
        """
        Read configuration values from an INI file.
        """
        with open(name=filename, mode='r') as config_fd:
            self.readfp(config_fd)