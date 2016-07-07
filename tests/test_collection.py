"""Test the collection module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from datapackage import DataPackage
from pytest import mark

from gobble.collection import Collection
from gobble.config import EXAMPLES_DIR


collect_examples = [
    ('fiscal', 0.5, 8),
    ('default', 0.5, 9),
    ('tabular', 1, 8),
    ('fiscal', 1, 0),
    ('default', 1, 9),
    ('tabular', 1, 8)
]

flavours = [
    'default',
    'tabular',
    'fiscal'
]


# noinspection PyShadowingNames
@mark.parametrize('flavour, threshold, hits', collect_examples)
def test_collect_packages_in_examples(flavour, threshold, hits):
    collection = Collection(EXAMPLES_DIR, flavour=flavour, detection=threshold)
    assert len(collection.packages) == hits


# noinspection PyShadowingNames
@mark.parametrize('flavour', flavours)
def test_datapackage_object_ingestion(flavour):
    collection = Collection(EXAMPLES_DIR, flavour=flavour)
    assert all(map(lambda x: isinstance(x, DataPackage), collection.packages))


def test_collection_representation():
    packages = Collection(EXAMPLES_DIR)
    representation = '<Collection: 9 files in %s>' % EXAMPLES_DIR
    assert repr(packages) == representation
