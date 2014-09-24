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
    _BUILD_TYPE_ATTRIBUTE = 'buildType'
    _ID_ATTRIBUTE = 'id'
    _RUNNING_BUILDS_RESOURCE_TEMPLATE = '/httpAuth/app/rest/builds/?locator=user:{username},personal:false,canceled:false,running:true,count:1'
    _BUILD_TYPES_RESOURCE = '/httpAuth/app/rest/buildTypes'
    _BUILD_TYPE_RESOURCE_TEMPLATE = ('/httpAuth/app/rest/builds/?locator=buildType:{build_type_id},status:FAILURE,user:{username},personal:false,'
                                     'canceled:false,running:any,count:1,sinceBuild:status:SUCCESS')

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

    def any_build_failures(self):
        """
        Checks whether any build are in a failed state or not.

        :return: True if there are one or more builds have failed or are failing.
        """
        any_build_failures = False
        build_types_url = urlparse.urljoin(self._server_url, self._BUILD_TYPES_RESOURCE)
        build_types_response = self._session.get(build_types_url)
        build_types_json_data = build_types_response.json()
        if self._COUNT_ATTRIBUTE in build_types_json_data:
            for build_type in build_types_json_data[self._BUILD_TYPE_ATTRIBUTE]:
                build_type_resource = self._BUILD_TYPE_RESOURCE_TEMPLATE.format(username=self._username,
                                                                                build_type_id=build_type[self._ID_ATTRIBUTE])
                build_type_url = urlparse.urljoin(self._server_url, build_type_resource)
                build_type_response = self._session.get(build_type_url)
                build_type_json_data = build_type_response.json()
                if self._COUNT_ATTRIBUTE in build_type_json_data:
                    any_build_failures = True
                    break
        return any_build_failures
