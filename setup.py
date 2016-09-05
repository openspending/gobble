# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from json import loads
from os.path import join, dirname
from setuptools import setup, find_packages


def read(filename):
    path = join(dirname(__file__), filename)
    with open(path, 'rt') as file:
        return file.read()


def clean(file):
    for line in file.splitlines():
        if line and not line.startswith('-r'):
            yield line


# Prepare
readme = read('README.md')
license_ = read('LICENSE.txt')
requirements = list(clean(read('requirements.txt')))
requirements_dev = list(clean(read('requirements.dev.txt')))
package = loads(read('package.json'))

# Run
setup(
    name=package['name'],
    version=package['version'],
    description=package['description'],
    long_description=readme,
    author=package['author'],
    author_email=package['author_email'],
    url=package['repository'],
    license=package['license'],
    include_package_data=True,
    packages=find_packages(exclude=['specs', 'tests']),
    package_dir={package['slug']: package['slug']},
    install_requires=requirements,
    tests_require=requirements_dev + requirements,
    test_suite='nose.collector',
    zip_safe=False,
    keywords=package['keywords'],
    classifiers=package['classifiers'],
    entry_points={'console_scripts': ['gobble = gobble.cli:gobble']}
)
