""" Collect files automatically"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from logging import getLogger
from os.path import join
from datapackage import DataPackage
from fnmatch import filter
from os import walk

from gobble.config import (
    FISCAL_SCHEMA,
    DATAPACKAGE_SCHEMA,
    TABULAR_SCHEMA,
    SCHEMA_DETECTION_THRESHOLD as THRESHOLD
)

log = getLogger(__name__)


class Collection(object):
    extensions = []

    def __init__(self, folder, detection=THRESHOLD):
        self.root = folder
        self.detection = detection
        self.packages = list(self.collect_all())

    def get_filepaths(self):
        for root, folders, files in walk(self.root):
            for extension in self.extensions:
                for file in filter(files, '*.' + extension):
                    yield join(root, file)

    def collect_all(self):
        for filepath in self.get_filepaths():
            item = self.collect(filepath)
            if self.loose_match(item):
                yield item

    def loose_match(self, filepath):
        pass

    def collect(self, filepath):
        pass

    def __repr__(self):
        info = {
            'class': self.__class__.__name__,
            'folder': self.root,
            'nb': len(self.packages)}
        return '<{class}: {nb} files in {folder}>'.format(**info)

    def validate(self):
        pass


class PackageCollection(Collection):
    extensions = ['json']

    def collect(self, filepath):
        return DataPackage(metadata=filepath,
                           schema=DATAPACKAGE_SCHEMA)

    def loose_match(self, item):
        # Perform a loose match so that the
        # correct descriptor files get detected even
        # though they may not be completely valid.

        found_keys = set(item.to_dict().keys())
        required_keys = set(item.required_attributes)
        common_keys = found_keys & required_keys
        key_ratio = len(common_keys) / len(required_keys)

        if key_ratio >= self.detection:
            return True
        else:
            template = '%s required %s but found %s (min=%1.1f), skipping %s'
            parameters = (self.__class__.__name__,
                          required_keys,
                          found_keys,
                          self.detection,
                          item.base_path)
            log.warn(template, *parameters)


class TabularCollection(PackageCollection):
    def collect(self, filepath):
        return DataPackage(metadata=filepath, schema=TABULAR_SCHEMA)


class FiscalCollection(PackageCollection):
    def collect(self, filepath):
        return DataPackage(metadata=filepath, schema=FISCAL_SCHEMA)
