"""Test the collection module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import map
from future import standard_library
standard_library.install_aliases()

from datapackage import DataPackage
from pytest import mark

from gobble.collection import Collection
from gobble.config import EXAMPLES_DIR


collect_examples = [
    ('fiscal', 0.5, 8),
    ('base', 0.5, 8),
    ('tabular', 1, 8),
    ('fiscal', 1, 2),
    ('base', 1, 8),
    ('tabular', 1, 8)
]

schemas = [
    'base',
    'tabular',
    'fiscal'
]


# noinspection PyShadowingNames
@mark.parametrize('schema, threshold, hits', collect_examples)
def test_collect_packages_in_examples(schema, threshold, hits):
    collection = Collection(EXAMPLES_DIR, schema=schema, detection=threshold)
    assert len(collection.packages) == hits


# noinspection PyShadowingNames
@mark.parametrize('schema', schemas)
def test_datapackage_object_ingestion(schema):
    collection = Collection(EXAMPLES_DIR, schema=schema)
    assert all(map(lambda x: isinstance(x, DataPackage), collection.packages))


def test_collection_representation():
    collection = Collection(EXAMPLES_DIR)
    template = '<Collection: %s files in %s>'
    representation = template % (len(collection.packages), EXAMPLES_DIR)
    assert repr(collection) == representation
