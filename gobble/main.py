"""The Gobble the command line API"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from click.decorators import command
from datapackage import DataPackage
from future import standard_library
from jsonschema import ValidationError

from gobble.upload import Batch, Bucket
from gobble.search import search_packages
from gobble.snapshot import archive
from gobble.upload import report_validation_errors
from gobble.user import User, create_user


standard_library.install_aliases()
user = User()


@command
def start():
    """Obtain token and set up the user."""
    return create_user()


@command
def validate(filepath, schema='fiscal'):
    package = DataPackage(filepath, schema=schema)
    try:
        package.validate()
    except ValidationError:
        report_validation_errors(package)


@command
def pull(query=None, private=True, limit=None):
    """Download fiscal datapackages from Open-Spending."""

    jwt = user.token if private else None
    return search_packages(query=query, jwt=jwt, size=limit)


@command
def push(filepath):
    """Upload a fiscal datapackages into Open-Spending."""

    package = DataPackage(filepath)

    batch = Batch(user, package)
    batch.request_s3_upload()
    bucket = Bucket(batch)
    bucket.start_uploads()

    bucket.collect_s3_results()


@command
def freeze(destination):
    """Generate quasi-specs from the request snapshots"""
    archive(destination)
