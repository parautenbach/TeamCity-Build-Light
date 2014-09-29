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
import abc
import urlparse

# Third-party imports
import requests


class BaseClient(object):
    """
    An abstract build server client.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, server_url, username, password):
        """
        Constructor.

        :param server_url: The base URL to the build server's API.
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

    @abc.abstractmethod  # pragma: no cover
    def any_builds_running(self):
        """
        Checks whether any builds are running or not.

        :return: True if there are one or more builds running.
        """

    @abc.abstractmethod  # pragma: no cover
    def any_build_failures(self):
        """
        Checks whether any build are in a failed state or not.

        :return: True if there are one or more builds have failed or are failing.
        """


class TeamCityClient(BaseClient):
    """
    A TeamCity API client.
    """

    # Attributes
    _COUNT_ATTRIBUTE = 'count'
    _HREF_ATTRIBUTE = 'href'
    _BUILD_TYPE_ATTRIBUTE = 'buildType'
    _BUILD_ATTRIBUTE = 'build'
    _ID_ATTRIBUTE = 'id'
    _TRIGGERED_ATTRIBUTE = 'triggered'
    _TYPE_ATTRIBUTE = 'type'
    _TYPE_USER = 'user'
    _USER_ATTRIBUTE = 'user'
    _USERNAME_ATTRIBUTE = 'username'
    _CHANGES_ATTRIBUTE = 'changes'
    _CHANGE_ATTRIBUTE = 'change'

    # Resources
    _RUNNING_BUILDS_RESOURCE = '/httpAuth/app/rest/builds/?locator=personal:false,canceled:false,running:true'
    _BUILD_TYPES_RESOURCE = '/httpAuth/app/rest/buildTypes'
    _BUILD_TYPE_RESOURCE_TEMPLATE = ('/httpAuth/app/rest/builds/?locator=buildType:{build_type_id},status:FAILURE,personal:false,'
                                     'canceled:false,running:any,sinceBuild:status:SUCCESS')

    def _get_resource(self, resource):
        """
        Get a resource on the API.

        :param resource: The HTTP resource.
        :return: A dictionary of JSON.
        """
        url = urlparse.urljoin(self._server_url, resource)
        return self._session.get(url).json()

    def _get_running_builds(self):
        """
        Get all running builds.

        :return: A list of builds.
        """
        running_builds = self._get_resource(self._RUNNING_BUILDS_RESOURCE)
        if self._COUNT_ATTRIBUTE in running_builds and running_builds[self._COUNT_ATTRIBUTE] > 0:
            return running_builds[self._BUILD_ATTRIBUTE]
        return []

    def _get_failed_builds(self):
        """
        Get all failed builds.

        :return: A list of builds.
        """
        # CONSIDER: Omit archived projects?
        builds = []
        build_types = self._get_resource(self._BUILD_TYPES_RESOURCE)
        if self._COUNT_ATTRIBUTE in build_types and build_types[self._COUNT_ATTRIBUTE] > 0:
            for build_type in build_types[self._BUILD_TYPE_ATTRIBUTE]:
                build_type_id = build_type[self._ID_ATTRIBUTE]
                build_type_resource = self._BUILD_TYPE_RESOURCE_TEMPLATE.format(build_type_id=build_type_id)
                failed_builds = self._get_resource(build_type_resource)
                if self._COUNT_ATTRIBUTE in failed_builds and failed_builds[self._COUNT_ATTRIBUTE] > 0:
                    builds.extend(failed_builds[self._BUILD_ATTRIBUTE])
        return builds

    def _is_triggered_by_user(self, build):
        """
        Determines whether the build was triggered by the user.

        :param build: The build JSON.
        :return: True if the build was triggered by the user.
        """
        trigger = build[self._TRIGGERED_ATTRIBUTE]
        return trigger[self._TYPE_ATTRIBUTE] == self._TYPE_USER and trigger[self._USER_ATTRIBUTE][self._USERNAME_ATTRIBUTE] == self._username

    def _user_is_contributor_to_build(self, build):
        """
        Determines whether the user is a contributor to the build.

        :param build: The build JSON.
        :return: True if the user is a contributor to the build.
        """
        changes_resource = build[self._CHANGES_ATTRIBUTE]
        changes = self._get_resource(changes_resource[self._HREF_ATTRIBUTE])
        if self._COUNT_ATTRIBUTE in changes and changes[self._COUNT_ATTRIBUTE] > 0:
            for change in changes[self._CHANGE_ATTRIBUTE]:
                change_detail = self._get_resource(change[self._HREF_ATTRIBUTE])
                user = change_detail[self._USER_ATTRIBUTE]
                if user[self._USERNAME_ATTRIBUTE] == self._username:
                    return True
        return False

    def _is_affected_by_user(self, build):
        """
        Determines whether the build was affected by the user.

        :param build: The build JSON.
        :return: True if the build was affected by the user.
        """
        return self._user_is_contributor_to_build(build) or self._is_triggered_by_user(build)

    def _any_builds_helper(self, builds):
        """
        Iterate over builds returned by the callable method and return True if any build is affected by the user.

        :param builds: A list of builds.
        :return: True if a build is affected by the user.
        """
        for build in builds:
            build_details = self._get_resource(build[self._HREF_ATTRIBUTE])
            if self._is_affected_by_user(build_details):
                return True
        return False

    def any_builds_running(self):
        """
        Checks whether any builds are running or not.

        :return: True if there are one or more builds running.
        """
        return self._any_builds_helper(self._get_running_builds())

    def any_build_failures(self):
        """
        Checks whether any build are in a failed state or not.

        :return: True if there are one or more builds have failed or are failing.
        """
        return self._any_builds_helper(self._get_failed_builds())
