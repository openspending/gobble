"""Validate data-packages"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from json import dumps
from datetime import datetime
from future import standard_library
from collections import OrderedDict
from datapackage import DataPackage
from jsonschema.exceptions import ValidationError
from pip.utils import cached_property

from gobble.config import VALIDATION_FEEDBACK_OPTIONS

standard_library.install_aliases()


class Validator(object):
    """Validate a data-package

    The :class:``Validator`` class is a thin wrapper around the
    DataPackage class that produces a tunable, human readable report.

    :type package: :class:`DataPackage`
    :type feedback: :class:`list`
    :param feedback: choose from 'message', 'cause', 'context',
                     'validator', 'validator_value', 'path',
                     'schema_path', 'instance', 'schema', 'parent'
    """
    VALID_OPTIONS = {
        'message', 'cause', 'context',
        'validator', 'validator_value',
        'path', 'schema_path', 'instance',
        'schema', 'parent'
    }

    NOT_A_PACKAGE = 'Argument must be DataPackage object'
    INVALID_OPTION = 'Feedback must be %s' % str(VALID_OPTIONS)

    def __init__(self, package, *feedback):
        assert isinstance(package, DataPackage), self.NOT_A_PACKAGE
        assert set(feedback).issubset(self.VALID_OPTIONS), self.INVALID_OPTION

        self._feedback = feedback or VALIDATION_FEEDBACK_OPTIONS
        self._package = package
        self._report = OrderedDict()
        self.timestamp = str(datetime.now())

        self._validate()

    @cached_property
    def errors(self):
        return list(self._errors)

    @property
    def report(self):
        return self._report

    @property
    def name(self):
        return self._package.metadata.get('name')

    @property
    def is_valid(self):
        return self._report['is_valid']

    @property
    def result(self):
        return 'success' if self.is_valid else 'fail'

    def save(self, filepath):
        if not filepath.endswith('.json'):
            raise ValueError('Reports are JSON files')
        with open(filepath, 'w+') as file:
            file.write(dumps(self.report))

    @property
    def _package_info(self):
        for attribute in self._package.required_attributes:
            value = self._package.metadata.get(attribute)
            yield attribute, value

    @property
    def _errors(self):
        for error in self._package.iter_errors():
            for choice in self._feedback:
                yield getattr(error, choice)

    def _validate(self):
        self._report.update(dict(is_valid=False, timestamp=self.timestamp))
        self._report.update(dict(package_info=dict(self._package_info)))
        try:
            self._package.validate()
            self._report.update(dict(is_valid=True))
        except ValidationError:
            self._report.update(dict(errors=self.errors))

    def __repr__(self):
        parameters = (self.name, self.result.upper(), len(self.errors))
        return '<Validator for %s: %s, %s errors>' % parameters
