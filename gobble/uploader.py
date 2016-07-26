""" Upload to Open-Spending"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
from requests_futures.sessions import FuturesSession

standard_library.install_aliases()

from os.path import join, getsize
from base64 import b64encode
from hashlib import md5
import io

from gobble.conductor import API, handle
from gobble.configuration import config
from gobble.logger import log, sdumps


class Resource(object):
    block_size = config.DATAFILE_HASHING_BLOCK_SIZE

    def __init__(self, name, file, package):
        self.package = package
        self.name = name
        self.file = file
        self.upload_url = None
        self.upload_query = None
        self._stream = None
        self._size = getsize(self.filepath)
        self._md5_hash = self._compute_hash()

        template = 'Created a new resource: %s'
        log.debug(template, sdumps(self.info))

    def _compute_hash(self):
        hasher = md5()
        with self as stream:
            chunk = stream.read(self.block_size)
            while len(chunk) > 0:
                hasher.update(chunk)
                chunk = stream.read(self.block_size)
        md5_binary = hasher.digest()
        md5_bytes = b64encode(md5_binary)
        md5_unicode = md5_bytes.decode('utf-8')
        return md5_unicode

    @property
    def filepath(self):
        return join(self.package.base_path, self.file)

    @property
    def headers(self):
        return {
            'Content-Length': len(self),
            'Content-MD5': self._md5_hash
        }

    @property
    def info(self):
        return {
            'package': self.package.descriptor['name'],
            'length': len(self),
            'md5': self._md5_hash,
            'type': "text/csv",
            'name': self.name
        }

    def __len__(self):
        return self._size

    def __enter__(self):
        self._stream = io.open(self.filepath, mode='rb')
        return self._stream

    # noinspection PyUnusedLocal
    def __exit__(self, etype, value, trace):
        self._stream.close()
        return True

    def __str__(self):
        template = '{package} {name} ({length} bytes)'
        return template.format(**self.info)

    def __repr__(self):
        template = '<Resource {package}: {name}>'
        return template.format(**self.info)


class Batch(object):
    def __init__(self, user, package):
        self.name = package.descriptor['name']
        self.user = user
        self.package = package
        self.resources = {}
        self.payload = None
        self.response = None

    def prepare(self):
        self._scan_files()
        self._build_payload()
        self._request_urls()
        self._register_urls()

        message = '%s batch is ready for upload: %s'
        log.debug(message, self, list(self.resources.keys()))

        return self

    def __iter__(self):
        for name, resource in self.resources.items():
            yield name, resource

    def _scan_files(self):
        for item in self.package.descriptor['resources']:
            resource = Resource(item['name'], item['path'], self.package)
            self.resources.update({resource.name: resource})
            log.debug('Ingested %s', resource)

    def _build_payload(self):
        self.payload = {
            'filedata': dict(self._datafiles),
            'metadata': {
                'owner': self.user.profile['idhash'],
                'name': str(self)
            }
        }

    def _request_urls(self):
        log.debug('Registering %s: %s', self, sdumps(self.payload))
        permission_token = self.user.permissions['os.datastore']['token']
        query = {'json': self.payload, 'jwt': permission_token}
        self.response = handle(API.request_upload(**query))

    def _register_urls(self):
        for resource in self.response['filedata'].values():
            query = resource['upload_query'].items()
            params = {k: v[0] for k, v in query}
            name = resource['name']
            self.resources[name].query = params
            self.resources[name].url = resource['upload_url']

    @property
    def _datafiles(self):
        for _, resource in self:
            yield resource.file, resource.info

    def __len__(self):
        return len(self.resources)

    def __repr__(self):
        info = {'name': str(self), 'length': len(self)}
        template = 'Batch [{length} files]: {name}'
        return template.format(**info)

    def __str__(self):
        return self.package.descriptor['name']


class Uploader(object):
    def __init__(self, batch):
        self.session = FuturesSession()
        self.batch = batch
        self.payload = None
        self.futures = []
        self.responses = []
        self.streams = []
        self.exceptions = None

    def push(self):
        for name, resource in self.batch:
            log.debug('Pushing %s to %s', name, resource.url)
            stream = io.open(resource.filepath, mode='rb')
            future = self.session.put(
                resource.url,
                headers=resource.headers,
                data=stream,
                params=resource.query,
                background_callback=self._notify
            )
            self.streams.append(stream)
            self.futures.append(future)

    def pull(self):
        for future in self.futures:
            exception = future.exception()
            if exception:
                raise exception
            response = future.result()
            self.responses.append(response)

    # noinspection PyUnusedLocal
    @staticmethod
    def _notify(session, response):
        handle(response)

    def close(self):
        for stream in self.streams:
            stream.close()
        return True


if __name__ == '__main__':
    from gobble.user import User
    from datapackage import DataPackage
    from tests.fixtures import PACKAGE_FILE

    user_ = User()
    package_ = DataPackage(PACKAGE_FILE)
    batch_ = Batch(user_, package_).prepare()
    uploader = Uploader(batch_)
    uploader.push()
    uploader.pull()
    uploader.close()
