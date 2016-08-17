"""Command line interface for Gobble"""

import io

from json import dumps
from os import getcwd
from os.path import join
from shutil import rmtree

from click import (Choice,
                   command,
                   argument,
                   Path,
                   group,
                   option,
                   echo,
                   secho,
                   edit)

from gobble.config import ROOT_DIR, settings
from gobble.fiscal import FiscalDataPackage
from gobble.search import search
from gobble.user import create_user, User


FILES = [
    'log',
    'package',
    'settings',
    'token',
    'authentication',
    'permissions'
]


@group()
def gobble():
    pass


@command()
@argument('file', type=Choice(FILES), metavar='[' + '|'.join(FILES) + ']')
@option('--editor', is_flag=True, help='Open the file inside an editor')
def display(file, editor):
    """Display (or edit) various Gobble files.

    This is a convienience command to quickly display various Gobble files.
    Pass the --editor option if you want to open the file inside an editor
    instead of just printing it. Only the settings file is really meant to be
    manually edited though.
    """

    extension = '.log' if file == 'log' else '.json'
    file = 'gobble' if file == 'log' else file
    folder = ROOT_DIR if file == 'package' else settings.USER_DIR
    filepath = join(folder, file + extension)

    if editor:
        edit(filename=filepath)
        secho('Saved changes to %s' % filepath, fg='green')

    else:
        try:
            with io.open(filepath) as cache:
                echo(cache.read())
        except FileNotFoundError:
            secho('%s could not be found' % filepath, fg='red')


@command()
def log():
    """Display the Gobble log file."""

    filepath = join(settings.USER_DIR, 'gobble.log')
    try:
        with io.open(filepath) as cache:
            echo(cache.read())
    except FileNotFoundError:
        secho('Sorry, %s could not be found' % filepath, fg='red')


@command(short_help='Manage the Gobble user')
@option('--create', is_flag=True, help='Create a new user or refresh token')
@option('--delete', is_flag=True, help='Delete the user cache')
def setup(create, delete, show):
    """Manage the Gobble user

    To create a new Gobble user, you need to be registered online. Gobble only
    supports a single user. To switch user account, just create a new user but
    make sure that you copy-paste the authorization link inside a private
    browser window when prompted.
    """

    if create:
        echo('Welcome to Open-Spending %s' % create_user())
    elif delete:
        rmtree(settings.USER_DIR)
        echo('Deleted local user cache for %s' % User())
    else:
        echo(User._uncache(show) or 'There is no %s cached' % show)


@command(short_help='Validate a datapackage descriptor')
@argument('filepath', type=Path(exists=True), metavar='path to datapackage')
def check(filepath):
    package = FiscalDataPackage(filepath, )
    package.validate(raise_error=False)


@command(short_help='Download a fiscal package from Open-Spending')
def pull(package_id, data=False, destination=getcwd()):
    """Download a fiscal package from Open-Spending.

    If no destination folder is provided, the fiscal data package will be
    downloaded to the current working directory. By default, only the package
    JSON descriptor is downloaded, not the data. To include data too, set
    the --data option to `True`.
    """
    if data:
        raise NotImplemented('Gobble does not yet support data downlaods')

    query = {'title': package_id}
    descriptor = search(query, private=True, limit=1)

    filepath = join(destination, descriptor['title'] + 'json')
    json = dumps(descriptor, ensure_ascii=False, indent=4)
    with io.open(filepath, 'w+', encoding='utf-8') as output:
        output.write(json)

    echo(json)


@command(short_help='Download package descriptors from Open-Spending')
@argument('query_all', required=False)
@option('--private', default=True, help='include private packages')
@option('--limit', default=50, help='limit the search result')
@option('--title', default=None, help='search package title')
@option('--author', default=None, help='search packages by author')
@option('--description', default=None, help='search packages by description')
@option('--region', default=None, help='search packages by region')
@option('--country', default=None, help='search packages by 2-digit country code')
@option('--city', default=None, help='search packages by city')
def search(private,
           limit,
           query_all,
           title,
           author,
           description,
           region,
           country,
           city):
    """Search fiscal packages on Open-Spending.

    You can search a package by `title`, `author`, `description`, `region`,
    `country`, or `city`, or you can match all these fields at once with the magic `q` key.
    Private user packages are included by default if a Gobble user is set up.
    You can limit the size of your results with the `size` parameter.
    """
    search_options = (
        ('title', title),
        ('author', author),
        ('description', description),
        ('regionCode', region),
        ('countryCode', country),
        ('cityCode', city)
    )

    if query_all:
        query = {'q': query_all}
    else:
        query = {key: value for key, value in search_options if value}

    results = search(query, private=private, limit=limit)
    echo(results)


@command(short_help='Upload a datapackage to Open-Spending')
@argument('filepath', type=Path(exists=True))
def push(filepath):
    package = FiscalDataPackage(filepath, user=User())
    package.upload()


gobble.add_command(check)
gobble.add_command(pull)
gobble.add_command(push)
gobble.add_command(setup)
gobble.add_command(display)
gobble.add_command(log)
