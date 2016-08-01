"""Expose the command line API"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()

from os.path import isfile, isdir
from datapackage import DataPackage
from os import getcwd
from click.decorators import command

from gobble.collection import Collection
from gobble.downloader import Downloader
from gobble.uploader import Uploader
from gobble.elasticsearch import ElasticSearch
from gobble.user import User
from gobble.validation import Validator


def resolve(target=None):
    """Return a list of data-packages

    If the target is a data-package file, return it in a list. If it's
    a directory, recursively find all data-packages inside the directory.
    If it's neither, look for data-packages inside the current directory.
    Raise an ValueError if nothing is found.
    """
    if isfile(target):
        packages = [DataPackage(metadata=target)]
    else:
        target = target if isdir(target) else getcwd()
        packages = Collection(target).packages

    if not packages:
        raise ValueError('No data-fiscal-packages in %s', target)

    return packages


@command
def configure(action):
    """Set up command line user"""
    user = User()
    return getattr(user, action)


@command
def validate(packages, *feedback):
    """Certify a data-package descriptor"""
    for package in packages:
        return Validator(package, *feedback)


@command
def find(kind, **query):
    """Look for contributors and packages on Open-Spending"""
    elastic = ElasticSearch()
    return elastic.search(kind, **query)


@command
def upload(packages):
    """Upload fiscal data into Open-Spending"""
    for package in packages:
        return Uploader(package)._upload_batch()


@command
def download(ids):
    """Download fiscal data from Open-Spending"""
    for id_ in ids:
        return Downloader(id_).pull()


@command
def show(package):
    """Preview tabular data in the shell"""
    return package
