#!/usr/bin/env python
#
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
#
# NOTE: INVOKE THE ALTERNATIVE SCRIPT build_light_dev IN A DEVELOPMENT SETTING
# IN ORDER FOR THE PYTHON PATH TO BE CORRECTLY SET TO FIND THE PACKAGE UNDER DEVELOPMENT
# AND NOT THE SITE-WIDE PACKAGE. IF ANY IS INSTALLED, IT IS RECOMMENDED THAT YOU
# UNINSTALL IT TO PREVENT POSSIBLE STRANGE AND CONFUSING BEHAVIOUR.

# System imports
from __future__ import print_function
import os
import signal
import sys
import threading

# Constants
_APPLICATION_NAME = 'Build Light'
_CONFIG_FILE = 'build_light.ini'
_GLOBAL_CONFIG_PATH = '/etc/whatsthatlight/{0}'.format(_CONFIG_FILE)
_LOCAL_CONFIG_PATH = 'conf/{0}'.format(_CONFIG_FILE)

# Globals
_config_path = None
_logger = None
_models = None
_decision_model = None
_service = None
_event = threading.Event()
_is_running = False

# Application imports
try:
    # noinspection PyUnresolvedReferences
    import whatsthatlight
except ImportError:
    print(('The whatsthatlight package could not be found. If this is a PRODUCTION environment, '
           'the package may not be installed. If this is a DEVELOPMENT environment, please execute '
           'the build_light_dev script or update the PYTHONPATH environment variable.'),
          file=sys.stderr)
    exit(1)


# noinspection PyUnusedLocal
def _stop_handler(_signum, _frame):
    """
    A handler to stop the system.

    :param _signum: Ignored.
    :param _frame: Ignored.
    """
    global _logger, _service, _event, _is_running
    _logger.info('Shutdown requested')
    if _is_running:
        _service.stop()
        _is_running = False
    _event.set()


# noinspection PyUnusedLocal
def _reload_config_handler(_signum, _frame):
    """
    A handler to reload the configuration.

    :param _signum: Ignored.
    :param _frame: Ignored.
    """
    global _config_path, _logger, _models, _decision_model, _service
    _logger.info('Reload requested')
    _logger.info('Configuration file location: {0}'.format(_config_path))
    try:
        config_parser = config_utils.create_config_parser(_config_path)
    except Exception, exception:
        _logger.info('Reload failed')
        _logger.error(exception)
        return
    # This works because the processors have references to these variables.
    # Consider adding setters to the processors to set new models more explicitly.
    _logger.info('Reloading processor models')
    _models = config_utils.load_models(config_parser)
    _logger.info('Reloading decision model')
    _decision_model = config_utils.load_decision_model(config_parser)
    _logger.info('Reloading main service')
    _service.reload()
    _logger.info('Reloaded')


def _register_signal_handlers():
    """
    Register signal handlers.
    """
    # And now to hook up the signals to reload and stop
    signal.signal(signal.SIGTERM, _stop_handler)
    signal.signal(signal.SIGINT, _stop_handler)
    signal.signal(signal.SIGHUP, _reload_config_handler)


def main():
    """
    Main application.
    """
    # We need these -- everywhere -- and we need them as e.g. signal handlers can't take these as arguments.
    global _logger, _config_path, _models, _decision_model, _service, _event, _is_running

    # Configuration
    parser = config_utils.create_argument_parser(application_name=_APPLICATION_NAME,
                                                 application_version=whatsthatlight.VERSION)
    arguments = parser.parse_args()
    try:
        _config_path = config_utils.try_get_config_path(arguments, _GLOBAL_CONFIG_PATH, _LOCAL_CONFIG_PATH)
        config_parser = config_utils.create_config_parser(_config_path)
    except Exception, exception:
        print('{0}\n'.format(exception.message), file=sys.stderr)
        parser.print_usage()
        sys.exit(1)

    # Logging
    _logger = config_utils.create_logger(_config_path)
    _logger.info('Initialising system')
    _logger.info('Configuration file location: {0}'.format(_config_path))
    _logger.info('Process running with PID {0}'.format(os.getpid()))

    # Assemble

    # Start
    _register_signal_handlers()
    _service.start()

    # We need to keep this process alive
    _event.clear()
    _is_running = True
    while _is_running:
        _event.wait(10)
    _logger.info('Terminating')


if __name__ == '__main__':
    main()