"""Rummage through the ElasticSearch database"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from pprint import pprint
from gobble.session import APISession

# TO DO: Searching a package by key value returns the whole list
# TO DO: merge the 3 search classes into one


class BadSearchKey(Exception):
    pass


class ElasticSearch(object):
    kind = None
    search = None
    searchable_keys = None

    @property
    def all(self):
        response = self.search()
        return response.json()

    def find(self, **query):
        valid_query = self.validate_query(**query)
        response = self.search(**valid_query)
        return response.json()

    def validate_query(self, **query):
        for key in query.keys():
            if key not in self.searchable_keys:
                template = 'Cannot search {kind} by {key}'
                feedback = template.format(kind=self.kind, key=key)
                raise BadSearchKey(feedback)
        return self.sanitize(query)

    @staticmethod
    def sanitize(query):
        values = ['"' + v + '"' for v in query.values()]
        return dict(zip(query.keys(), values))


class Contributors(ElasticSearch):
    kind = 'user'
    search = APISession.search_users
    searchable_keys = ['name']


class Packages(ElasticSearch):
    kind = 'package'
    search = APISession.search_packages
    searchable_keys = [
        'title',
        'author',
        'description',
        'regionCode',
        'countryCode',
        'cityCode'
    ]


if __name__ == '__main__':
    contributors = Contributors()
    packages = Packages()

    pprint(contributors.all)
    pprint(packages.all)
    pprint(contributors.find(name='aura'))
    pprint(packages.find(author='Vlad'))
