""" Collect files automatically"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from datapackage.exceptions import DataPackageException
from logging import getLogger
from os.path import join
from datapackage import DataPackage
from fnmatch import filter
from os import walk

from gobble.config import DATAPACKAGE_DETECTION_THRESHOLD as THRESHOLD

log = getLogger(__name__)


class Collection(object):
    """A collection of local data-packages

    Recursively collect all data-packages inside a folder. Perform a
    loose match so that descriptor files get detected even though
    they may not be completely valid.
    """
    BAD_MATCH_MSG = '%s schema requires %s, found %s (min=%1.1f), skipping %s'
    BAD_PACKAGE_MSG = 'Skipping %s: %s'

    def __init__(self, folder, schema='base', detection=THRESHOLD):
        self.root = folder
        self.detection = detection
        self.schema = schema
        self.packages = []

        self._collect()

    def _collect(self):
        for root, folders, files in walk(self.root):
            for filename in filter(files, '*.json'):
                filepath = join(root, filename)
                package = self.ingest(filepath)
                if self.is_match(package):
                    self._register(package, filepath)

    def _register(self, package, filepath):
        package.__setattr__('filepath', filepath)
        self.packages.append(package)

    def ingest(self, filepath):
        try:
            package = DataPackage(metadata=filepath, schema=self.schema)
            return package
        except DataPackageException as error:
            log.warn(self.BAD_PACKAGE_MSG, filepath, error)

    def is_match(self, item):
        found_keys = set(item.to_dict().keys())
        required_keys = set(item.required_attributes)
        common_keys = found_keys & required_keys
        key_ratio = len(common_keys) / len(required_keys)

        if key_ratio >= self.detection:
            return True
        else:
            parameters = (self.schema.upper(),
                          required_keys,
                          found_keys,
                          self.detection,
                          item.base_path)
            log.warn(self.BAD_MATCH_MSG, *parameters)

    def __repr__(self):
        info = {
            'class': self.__class__.__name__,
            'folder': self.root,
            'nb': len(self.packages)}
        return '<{class}: {nb} files in {folder}>'.format(**info)
