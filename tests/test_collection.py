"""Test the collection module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from datapackage import DataPackage
from future import standard_library
standard_library.install_aliases()

from pytest import mark

from gobble.config import EXAMPLES_DIR
from gobble.collection import (FiscalCollection,
                               PackageCollection,
                               TabularCollection)

collect_examples = [
    (FiscalCollection, 0.5, 8),
    (PackageCollection, 0.5, 9),
    (TabularCollection, 1, 8),
    (FiscalCollection, 1, 0),
    (PackageCollection, 1, 9),
    (TabularCollection, 1, 8)
]

make_collection = [
    PackageCollection,
    TabularCollection,
    FiscalCollection
]


# noinspection PyShadowingNames
@mark.parametrize('make_collection, threshold, hits', collect_examples)
def test_collect_packages_in_examples(make_collection, threshold, hits):
    collection = make_collection(EXAMPLES_DIR, detection=threshold)
    assert len(collection.packages) == hits


# noinspection PyShadowingNames
@mark.parametrize('make_collection', make_collection)
def test_datapackage_object_ingestion(make_collection):
    collection = make_collection(EXAMPLES_DIR)
    assert all(map(lambda x: isinstance(x, DataPackage), collection.packages))


def test_collection_representation():
    packages = PackageCollection(EXAMPLES_DIR)
    representation = '<PackageCollection: 9 files in %s>' % EXAMPLES_DIR
    assert repr(packages) == representation
