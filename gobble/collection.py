""" Collect files automatically"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
from requests import get

standard_library.install_aliases()

from logging import getLogger
from os.path import join
from datapackage import DataPackage
from fnmatch import filter
from os import walk

from gobble.config import SCHEMA_DETECTION_THRESHOLD as THRESHOLD, SCHEMAS_HOST

log = getLogger(__name__)


class Collection(object):
    """A collection of data-packages

    Recursively collect all data-packages inside a folder. Perform a
    loose match so that descriptor files get detected even though
    they may not be completely valid.
    """

    def __init__(self, folder, flavour='default', detection=THRESHOLD):
        self.root = folder
        self.detection = detection
        self.flavour = flavour
        self.schema = self.get_schema(flavour)

        self.packages = list(self.all)

    @property
    def filepaths(self):
        for root, folders, files in walk(self.root):
            for file in filter(files, '*.json'):
                yield join(root, file)

    @property
    def all(self):
        for filepath in self.filepaths:
            package = self.ingest(filepath)
            if self.is_match(package):
                yield package

    @staticmethod
    def get_schema(schema):
        prefix = '%s-' % schema if schema != 'default' else ''
        response = get(SCHEMAS_HOST + prefix + 'data-package.json')
        return response.json()

    def validate(self):
        pass

    def ingest(self, filepath):
        return DataPackage(metadata=filepath, schema=self.schema)

    def is_match(self, item):
        found_keys = set(item.to_dict().keys())
        required_keys = set(item.required_attributes)
        common_keys = found_keys & required_keys
        key_ratio = len(common_keys) / len(required_keys)

        if key_ratio >= self.detection:
            return True
        else:
            template = '%s data-package requires %s, ' \
                       'found %s (min=%1.1f), skipping %s'
            parameters = (self.flavour.upper(),
                          required_keys,
                          found_keys,
                          self.detection,
                          item.base_path)
            log.warn(template, *parameters)

    def __repr__(self):
        info = {
            'class': self.__class__.__name__,
            'folder': self.root,
            'nb': len(self.packages)}
        return '<{class}: {nb} files in {folder}>'.format(**info)
