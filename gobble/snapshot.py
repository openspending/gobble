"""This module has good intentions, like helping you debug API calls"""


from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from json import loads, dumps
from os import listdir
from os.path import join, isdir
from re import search
from click import command

import io

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from gobble.config import ROOT_DIR
from gobble.logger import log
from gobble.config import settings


SNAPSHOTS_DIR = join(ROOT_DIR, 'assets', 'snapshots')


def to_json(response):
    """Safely extract the payload from the response object"""
    try:
        return response.json()
    except JSONDecodeError:
        return {}


class SnapShot(OrderedDict):
    """A chatty wrapper around the API transaction"""

    def __init__(self, endpoint, url, reponse, params,
                 headers=None, json=None, is_freeze=False):
        """Log, record and save before returning an instance"""

        self.is_freeze = is_freeze

        self.url = url
        self.endpoint = endpoint
        self.response = reponse
        self.headers = headers
        self.params = params
        self.request_payload = json

        super(OrderedDict, self).__init__(self._template)
        self.timestamp = str(datetime.now())

        self._log()
        self._record()
        self._save()

    def _log(self):
        """Is there such a thing as too much logging?"""

        code = self.response.status_code
        reason = self.response.reason
        response_json = to_json(self.response)
        begin = code, reason, self.endpoint, 'begin'
        end = code, reason, self.endpoint, 'end'
        transaction = ' [%s] %s - %s (%s) '

        log.debug('{:*^100}'.format(transaction % begin))

        messages = (
            ('Request endpoint: %s', self.endpoint.url),
            ('Request time: %s', self.response.elapsed),
            ('Request parameters: %s', self.params),
            ('Request payload: %s', self.request_payload),
            ('Request headers: %s', self.headers),
            ('Response headers: %s', self.response.headers),
            ('Response payload: %s', response_json),
            ('Response cookies: %s', self.response.cookies),
            ('Request full URL: %s', self.url),
        )
        for message in messages:
            log.debug(*message)

        indent = 4 if settings.EXPANDED_LOG_STYLE else None
        log.debug(dumps(response_json, ensure_ascii=False, indent=indent))

        log.debug('{:*^100}'.format(transaction % end))

    def _record(self):
        """Store the transaction info"""

        json = to_json(self.response)
        duplicate_json = deepcopy(json)

        self['timestamp'] = self.timestamp
        self['url'] = self.url
        self['query'] = self.params
        self['request_json'] = self.request_payload
        self['response_json'] = duplicate_json
        self['request_headers'] = self.headers
        self['response_headers'] = dict(self.response.headers)
        self['cookies'] = dict(self.response.cookies)

    @property
    def _template(self):
        return (
            ('timestamp', None),
            ('host', settings.OS_URL),
            ('url', None),
            ('method', self.endpoint.method),
            ('path', self.endpoint.path),
            ('query', None),
            ('request_json', None),
            ('response_json', None),
            ('request_headers', None),
            ('response_headers', None),
            ('cookies', None),
        )

    def _save(self):
        """Save the snapshot as JSON in the appropriate place"""
        with io.open(self._filepath, 'w+', encoding='utf-8') as file:
            file.write(dumps(self, ensure_ascii=False))
        log.debug('Saved request + response to %s', self._filepath)

    @property
    def _folder(self):
        return SNAPSHOTS_DIR if self.is_freeze else settings.USER_DIR

    @property
    def _filepath(self):
        template = '{method}.{path}.json'
        dot_path = '.'.join(self.endpoint._path).rstrip('/')
        params = {'method': self.endpoint.method, 'path': dot_path}
        filename = template.format(**params)
        return join(self._folder, filename)

    def __str__(self):
        return str(self.endpoint) + ' at ' + self.timestamp

    def __repr__(self):
        return '<SnapShot %s>' % str(self)

    @property
    def json(self):
        return dumps(self, ensure_ascii=False)


def freeze(json):
    """Recursively substitute unwanted strings inside a json-like object

    Basically, remove anything in the substitution list below, even when
    hidden in inside query strings.
    """
    subs = {
        'jwt': r'jwt=([^&^"]+)',
        "bucket_id": r'\/([\w]{32})\/',
        'Signature': r'Signature=([^&^"]+)',
        'AWSAccessKeyId': r'AWSAccessKeyId=([^&^"]+)',
        'Expires': r'Expires=([^&^"]+)',
        'Date': None,
        "Set-Cookie": None,
        'token': None,
    }

    def regex(dummy_, json_, key_, pattern_, value_):
        match = search(pattern_, value_)
        if match:
            sub = match.group(1), dummy_
            json_[key_] = value_.replace(*sub)

    if isinstance(json, list):
        for item in json:
            freeze(item)
    elif isinstance(json, dict):
        for field, pattern in subs.items():
            for key, value in json.items():
                dummy = field.upper()
                if key == field:
                    json[key] = dummy
                elif isinstance(value, str):
                    if pattern:
                        regex(dummy, json, key, pattern, value)
                elif isinstance(value, dict):
                    freeze(value)


@command
def archive(destination):
    """Freeze and move all snapshots to the destination folder."""

    if not isdir(destination):
        raise NotADirectoryError(destination)

    for file in listdir(settings.USER_DIR):
        verb = file.split('.')[0]
        if verb in ['GET', 'POST', 'PUT']:

            with io.open(file) as source:
                snapshot = loads(source.read())

            freeze(snapshot)

            # Overwrite if necessary
            output = join(destination, file)
            with io.open(output, 'w+', encoding='utf-8') as target:
                target.write(dumps(snapshot, ensure_ascii=False))
