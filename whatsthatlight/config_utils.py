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
Configuration helper utilities.
"""

# System imports
import argparse
import importlib
import logging
import logging.config
import os

# Local imports
from whatsthatlight import config


def create_config_parser(config_path):
    """
    Create the config from file.

    :config_path: The configuration file path.
    """
    config_parser = config.ConfigParser()
    try:
        config_parser.read(config_path)
        return config_parser
    except IOError, io_error:
        raise Exception('Invalid config file "{0}": {1} ({2})'.format(config_path, io_error.strerror, io_error.errno))


def create_logger(config_path):
    """
    Create the logger.

    :param config_path: The configuration file path.
    """
    logging.config.fileConfig(config_path)
    return logging.getLogger()


def load_device(config_parser):
    """
    Load a device from config.

    :param config_parser: A parsed configuration.
    :return: An instance of the class.
    """
    namespace = config.get_device_namespace(config_parser)
    class_name = config.get_device_class_name(config_parser)
    args_list = list(config.get_device_args(config_parser))
    args_list[2] = importlib.import_module(args_list[2])
    args = tuple(args_list)
    return construct_class(namespace, class_name, args)


def load_client(config_parser):
    """
    Load a build server client from config.

    :param config_parser: A parsed configuration.
    :return: An instance of the class.
    """
    namespace = config.get_client_namespace(config_parser)
    class_name = config.get_client_class_name(config_parser)
    args = config.get_client_args(config_parser)
    return construct_class(namespace, class_name, args)


def try_get_config_path(arguments, global_config_path, local_config_path):
    """
    Try to get a valid configuration file path.

    :param arguments: Parsed arguments.
    """
    if arguments.config:
        if os.path.exists(arguments.config):
            return arguments.config
        else:
            raise Exception('Please specify a valid config file.')
    elif os.path.exists(global_config_path):
        return global_config_path
    elif os.path.exists(local_config_path):
        return local_config_path
    else:
        raise Exception('Unable to locate a config file in the default locations. Please specify a valid one.')


def create_argument_parser(application_name, application_version):
    """
    Get command-line arguments and options for the coordinator.

    :param application_name: The application's name.
    :param application_version: The application's version.
    :return: An argument parser.
    """
    description = '{0} for sending records to models.'.format(application_name)
    parser = argparse.ArgumentParser(description=description, version='{0} v{1}'.format(application_name, application_version))
    parser.add_argument('--config', help=('Path to the application\'s configuration file. Default search locations, '
                                          'if no configuration file is specified, are /etc/whatsthatlight/ and ./conf/ '
                                          '(in that order).'))
    return parser


def construct_class(namespace, class_name, args):
    """
    Helper function to dynamically construct a class from configuration.

    :param namespace: The namespace where the class resides.
    :param class_name: The class to construct.
    """
    module = importlib.import_module(name=namespace)
    class_ = getattr(module, class_name)
    return class_(*args)


class UnsupportedConfigError(Exception):
    """
    Raised when an unsupported config value is read.
    """
