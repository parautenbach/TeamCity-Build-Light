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
Various build server clients.
"""

# System imports
import urlparse

# Third-party imports
import requests


class TeamCityClient(object):
    """
    A TeamCity API client.
    """

    _COUNT_ATTRIBUTE = 'count'
    _RUNNING_BUILDS_RESOURCE_TEMPLATE = '/httpAuth/app/rest/builds/?locator=user:{username},personal:false,canceled:false,running:true,count:1'

    def __init__(self, server_url, username, password):
        """
        Constructor.

        :param server_url: The base URL to the TeamCity API.
        :param username: The username for the API, which is also the user for which the API is checked.
        :param password: The password for the provided username.
        """
        self._server_url = server_url
        self._username = username
        self._password = password
        self._session = None

    def connect(self):
        """
        Connect to the API.
        """
        self._session = requests.Session()
        self._session.auth = (self._username, self._password)
        self._session.headers.update({
            'Accept': 'application/json'
        })

    def disconnect(self):
        """
        Disconnect from the API.
        """
        self._session = None

    def any_builds_running(self):
        """
        Checks whether any builds are running or not.

        :return: True if there are one or more builds running.
        """
        resource = self._RUNNING_BUILDS_RESOURCE_TEMPLATE.format(username=self._username)
        url = urlparse.urljoin(self._server_url, resource)
        response = self._session.get(url)
        json_data = response.json()
        return self._COUNT_ATTRIBUTE in json_data
