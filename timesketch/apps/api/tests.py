# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the resources exposed by Timesketch API version 1."""

import json
import mock

from django.contrib.auth.models import User
from tastypie.test import TestApiClient
from tastypie.test import ResourceTestCase

from timesketch.apps.sketch.models import EventComment
from timesketch.apps.sketch.models import SavedView
from timesketch.apps.sketch.models import Sketch


# pylint: disable=no-member, too-many-public-methods
class MockDataStore(object):
    """A mock implementation of a Datastore."""
    def __init__(self, _):
        self.index_list = []

    # pylint: disable=unused-argument
    def get_single_event(self, event_id):
        """Mock returning a single event from the datastore.

        Returns:
            A dictionary with event data.
        """
        result_dict = {
            "_index": self.index_list,
            "_id": "adc123",
            "_source": {
                "es_index": "",
                "es_id": "",
                "label": "",
                "timestamp": 1410895419859714,
                "timestamp_desc": "",
                "datetime": "2014-09-16T19:23:40+00:00",
                "source_short": "",
                "source_long": "",
                "message": "",
            }
        }
        return result_dict

    # pylint: disable=unused-argument
    @staticmethod
    def add_label_to_event(event, sketch, user, label, toggle=False):
        """ Mock adding a label to an event."""
        return

    # pylint: disable=unused-argument
    @staticmethod
    def search(sketch, query, filters):
        """Mock a search query.

        Returns:
            A dictionary with search result.
        """
        result = {
            "hits": {
                "hits": [
                    {
                        "sort": [
                            1410900180000
                        ],
                        "_type": "plaso_event",
                        "_source": {
                            "timestamp_desc": "A timestamp",
                            "timestamp": 1410900180184000,
                            "tag": [],
                            "timesketch_label": [
                                {
                                    "sketch": "1",
                                    "name": "__ts_star",
                                    "user": 1
                                }
                            ],
                            "message": "Test event",
                            "datetime": "2014-09-16T20:43:00+00:00",
                        },
                        "_score": "null",
                        "_index": "abc123",
                        "_id": "def345"
                    }
                ],
                "total": 1,
                "max_score": "null"
            },
            "_shards": {
                "successful": 15,
                "failed": 0,
                "total": 15
            },
            "took": 24,
            "timed_out": "false"
        }
        return result


class BaseResourceTest(ResourceTestCase):
    """Base class that creates common objects and handles authentication."""
    def setUp(self):
        super(BaseResourceTest, self).setUp()
        # Create a user
        self.username = 'john'
        self.password = 'pass'
        self.user = User.objects.create_user(
            self.username, 'john@example.com', self.password)
        # Create a sketch, comment and a saved view to use in the tests.
        self.sketch = Sketch.objects.create(user=self.user, title="Test")
        self.comment = EventComment.objects.create(
            user=self.user, body="test", sketch=self.sketch,
            datastore_id="test", datastore_index="test")
        self.view = SavedView.objects.create(
            user=self.user, sketch=self.sketch, query="Test",
            filter=json.dumps({'foo': 'bar'}), name="Test")
        # This is a test client from the tastypie project.
        self.api_client = TestApiClient()

    def get_credentials(self):
        """Performs Django session based authentication."""
        return self.api_client.client.login(
            username=self.username, password=self.password)


class CommentResourceTest(BaseResourceTest):
    """Test the comment API resource."""
    @mock.patch(
        'timesketch.lib.datastores.elasticsearch_datastore.ElasticSearchDataStore',
        MockDataStore)
    def test_create_comment(self):
        """Send a request to the API to create a comment."""
        # Data to send in the request.
        data = {
            'data': {
                'sketch': 1,
                'id': 'test',
                'index': 'test',
                'body': 'test'
            }
        }
        response = self.api_client.post(
            '/api/v1/comment/', format='json',
            authentication=self.get_credentials(), data=data)
        # The API will return the created comment object in the response because
        # we need it for the UI for displaying the comment without reload.
        created_comment_dict = self.deserialize(response)
        self.assertHttpCreated(response)
        self.assertEqual(len(created_comment_dict['data']), 6)

        expected_keys = [
            u'body',
            u'updated',
            u'created',
            u'user',
            u'datastore_id',
            u'datastore_index',
            u'data',
            u'resource_uri'
        ]

        self.assertKeys(created_comment_dict, expected_keys)

    def test_get_comments_unauthorized(self):
        """Access the comment resource with a unauthenticated session."""
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/comment/', format='json'))

    def test_get_comments(self):
        """Send a request to the API to retrieve a list of comments."""
        # Data to send in the request.
        data = {
            'id': 'test',
            'index': "test",
            "sketch": 1
        }
        response = self.api_client.get(
            '/api/v1/comment/', format='json',
            authentication=self.get_credentials(), data=data)
        comment_dict = self.deserialize(response)['objects']
        self.assertValidJSONResponse(response)
        self.assertEqual(len(comment_dict), 1)

        expected_keys = [
            u'body',
            u'updated',
            u'created',
            u'user',
            u'datastore_id',
            u'datastore_index',
            u'resource_uri']

        self.assertKeys(comment_dict[0], expected_keys)


class EventResourceTest(BaseResourceTest):
    """Test the event API resource."""
    def test_get_event_unauthorized(self):
        """Access the event resource with a nauthenticated session."""
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/event/', format='json'))

    def test_get_event(self):
        """Send a request to the API to retrieve an event."""
        # Data to send in the request.
        data = {
            'id': 'test_id',
            'index': 'test_index'
        }
        response = self.api_client.get(
            '/api/v1/event/', format='json',
            authentication=self.get_credentials(), data=data)
        event_dict = self.deserialize(response)['objects'][0]
        self.assertValidJSONResponse(response)

        expected_keys = [
            u'parser',
            u'datetime',
            u'tag',
            u'allocated',
            u'filename',
            u'inode',
            u'message',
            u'size',
            u'display_name',
            u'uuid',
            u'hostname',
            u'label',
            u'source_short',
            u'username',
            u'store_number',
            u'data_type',
            u'timestamp',
            u'store_index',
            u'source_long',
            u'es_index',
            u'offset',
            u'timestamp_desc',
            u'fs_type',
            u'es_id',
            u'resource_uri']

        self.assertKeys(event_dict, expected_keys)


class SearchResourceTest(BaseResourceTest):
    """Test the search API resource."""
    def test_search_unauthorized(self):
        """Access the search resource with a unauthenticated session."""
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/search/', format='json'))

    def test_search(self):
        """Send a request to the API to perform a search."""
        # Data to send in the request.
        data = {
            'q': 'test',
            'filter': json.dumps({'foo': 'bar'}),
            'indexes': 'test',
            'sketch': 1
        }
        response = self.api_client.get(
            '/api/v1/search/', format='json',
            authentication=self.get_credentials(), data=data)
        search_result_dict = self.deserialize(response)['objects'][0]
        self.assertValidJSONResponse(response)

        expected_keys = [
            u'timestamp_desc',
            u'timestamp',
            u'label',
            u'tag',
            u'es_index',
            u'es_id',
            u'message',
            u'datetime',
            u'resource_uri']

        self.assertKeys(search_result_dict, expected_keys)


class UserProfileResourceTest(BaseResourceTest):
    """Test the user profile API resource."""
    def test_get_profile_unauthorized(self):
        """Access the user profile resource with a unauthenticated session."""
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/userprofile/', format='json'))

    def test_get_profile(self):
        """Send a request to the API to get user profiles."""
        response = self.api_client.get(
            '/api/v1/userprofile/', format='json',
            authentication=self.get_credentials())
        userprofile_dict = self.deserialize(response)['objects'][0]
        self.assertValidJSONResponse(response)

        expected_keys = [
            u'avatar',
            u'resource_uri']

        self.assertKeys(userprofile_dict, expected_keys)


class UserResourceTest(BaseResourceTest):
    """Test the user API resource."""
    def test_get_user_unauthorized(self):
        """Access the user resource with a unauthenticated session."""
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/user/', format='json'))

    def test_get_user(self):
        """Send a request to the API to get users."""
        response = self.api_client.get(
            '/api/v1/user/', format='json',
            authentication=self.get_credentials())
        user_dict = self.deserialize(response)['objects'][0]
        self.assertValidJSONResponse(response)

        expected_keys = [
            u'profile',
            u'username',
            u'first_name',
            u'last_name',
            u'resource_uri']

        self.assertKeys(user_dict, expected_keys)


class SketchAclResourceTest(BaseResourceTest):
    """Test the sketch ACL API resource."""
    def test_create_acl(self):
        """Test to create a ACL on a specific sketch."""
        # Data to send in the request.
        data = {
            'data': {
                'sketch': 1,
                'sketch_acl': 'public'
            }
        }
        response = self.api_client.post(
            '/api/v1/sketch_acl/', format='json',
            authentication=self.get_credentials(), data=data)
        self.assertHttpCreated(response)

    def test_get_acl_unauthorized(self):
        """Access the sketch ACL resource with a unauthenticated session."""
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/sketch_acl/', format='json'))


class ViewResourceTest(BaseResourceTest):
    """Test the view API resource."""
    def test_create_view(self):
        """Test to create a view."""
        # Data to send in the request.
        data = {
            'data': {
                'sketch': 1,
                'name': 'test',
                'query': "test query",
                'query_filter': json.dumps({'foo': 'bar'})
            }
        }
        response = self.api_client.post(
            '/api/v1/view/', format='json',
            authentication=self.get_credentials(), data=data)
        self.assertHttpCreated(response)

    def test_get_views_unauthorized(self):
        """Access the view resource with a unauthenticated session."""
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/view/', format='json'))

    def test_get_views(self):
        """Send a request to the API to get views."""
        # Data to send in the request.
        data = {
            'sketch': 1,
            'view': 1
        }
        response = self.api_client.get(
            '/api/v1/view/', format='json',
            authentication=self.get_credentials(), data=data)
        view_dict = self.deserialize(response)['objects'][0]
        self.assertValidJSONResponse(response)
        self.assertHttpOK(response)

        expected_keys = [
            u'updated',
            u'name',
            u'created',
            u'filter',
            u'query',
            u'id',
            u'resource_uri']

        self.assertKeys(view_dict, expected_keys)


class LabelResourceTest(BaseResourceTest):
    """Test the label API resource."""
    def test_create_label(self):
        """Send a request to the API to create a label."""
        # Data to send in the request.
        data = {
            'data': {
                'sketch': 1,
                'id': 'test',
                'index': 'test',
                'label': "test",
            }
        }
        response = self.api_client.post(
            '/api/v1/label/', format='json',
            authentication=self.get_credentials(), data=data)
        # The API will return the created label object in the response because
        # we need it for the UI for displaying the label without reload.
        created_label_dict = self.deserialize(response)['data']
        self.assertHttpCreated(response)

        expected_keys = [
            u'index',
            u'sketch',
            u'id',
            u'label']

        self.assertKeys(created_label_dict, expected_keys)

    def test_get_labels_unauthorized(self):
        """Access the label resource with a unauthenticated session."""
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/label/', format='json'))
