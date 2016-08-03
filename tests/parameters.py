"""Parameters for paramtrized tests are defined here"""

from gobble.config import Production, Development
from gobble.api import (request_upload, search_packages, update_user,
                        authorize_user, authenticate_user, oauth_callback)


# -----------------------------------------------------------------------------
configurations = [Production, Development]
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
_upload_urls = [
    (
        'http://fakes3/fake-bucket/'
        '5df4a7b06a940c992d1c44525daff47b/'
        'mexican-budget-samples/'
        'data/sample.4.csv'
    ),
    (
        'https://s3.amazonaws.com:443/'
        'datastore.openspending.org/'
        '5df4a7b06a940c992d1c44525daff47b/'
        'mexican-budget-samples/'
        'data/sample.2.csv'
    )
]
_s3_bucket_urls = [
    'http://fakes3/fake-bucket/'
    '5df4a7b06a940c992d1c44525daff47b',
    'https://s3.amazonaws.com:443/datastore.openspending.org/'
    '5df4a7b06a940c992d1c44525daff47b'
]
s3_bucket_test_cases = list(zip(_upload_urls, _s3_bucket_urls))
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
api_calls = (
    authenticate_user,
    authorize_user,
    oauth_callback,
    update_user,
    search_packages,
    request_upload,
)
endpoints = [
    ('foo', ['spam', 'eggs/']),
    ('bar', ['1', '2'])
]
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
json_objects = [
    (
        # a json dict-like object
        {
            'foo': {
                'spam': True,
                'jwt': 'secret token'
                }
        },
        {
            'foo': {
                'spam': True,
                'jwt': 'JWT'
                }
        }
    ),
    (
        # a json list-like object
        [
            {
                'foo': {
                    'spam': True,
                    'jwt': 'secret token'
                },
                'bar': [True, False]
            },

        ],
        [
            {
                'foo': {
                    'spam': True,
                    'jwt': 'JWT'
                },
                'bar': [True, False]
            },

        ]
    ),
    (
        # a json with plenty of regex to do
        {
            'foo': 'http://foo.bar?jwt=1a.2b_3c-4d.56789',
            'bar': 'http://foo.bar?foo=bar&jwt=1a.2b_3c-4d.56789&x=y',
            'eggs': 'http://foo.bar/bucket/5df4a7b06a940c992d1c44525daff47b/'
                    'data-package?foo=bar&jwt=1a.2b_3c-4d.56789&x=y'
        },
        {
            'foo': 'http://foo.bar?jwt=JWT',
            'bar': 'http://foo.bar?foo=bar&jwt=JWT&x=y',
            'eggs': 'http://foo.bar/bucket/BUCKET_ID/'
                    'data-package?foo=bar&jwt=JWT&x=y'
        },
    ),
]
# -----------------------------------------------------------------------------
