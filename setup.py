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

# Required imports
from __future__ import print_function
from setuptools import setup, find_packages
import os
import platform
# noinspection PyPackageRequirements
import pip.req
# noinspection PyPackageRequirements
import pypandoc
import sys


# TODO: Prompt for username, password, server URL, vendor ID and product ID

# Check whether we can install
if not platform.system() in ('Linux', 'Darwin'):
    print('ERROR: This package can only be installed on a *nix-like platform.', file=sys.stderr)
    sys.exit(1)

# We can only install system files if we're root
data_files = []
if os.geteuid() == 0:
    # Note: /etc/init/ is for Ubuntu's upstart scripts and must not be /etc/init.d/ (it also requires root access).
    data_files = [('/etc/init/', ['conf/some.conf']),
                  ('/etc/whatsthatlight/', ['conf/some.ini'])]
else:
    print('WARNING: System files of the package can only be installed using root privileges.')

# Gather requirements
install_requirements = pip.req.parse_requirements('requirements.txt')
requirements = [str(install_requirement.req) for install_requirement in install_requirements]

# Convert the README from MD to reST
readme = pypandoc.convert('README.md', 'rst')

# Install
setup(name='whatsthatlight',
      version='0.0.0.0',
      description='TeamCity blink(1) build light',
      long_description=readme,
      # https://pypi.python.org/pypi?:action=list_classifiers
      classifiers=['Development Status :: 2 - Pre-Alpha',
                   'Intended Audience :: Developers',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Software Development :: Build Tools'],
      keywords='continuous integration feedback device build light teamcity',
      url='http://www.whatsthatlight.com/',
      author='Pieter Rautenbach',
      author_email='parautenbach@gmail.com',
      license='Apache License, Version 2.0',
      data_files=data_files,
      # This installs to some location like /usr/bin, but most likely <VIRTUAL_ENV>/bin (it depends on the environment).
      # scripts=['scripts/'],
      packages=find_packages(),
      requires=[],
      install_requires=requirements,
      include_package_data=True,
      zip_safe=False)

# TODO: Post-install stuff
