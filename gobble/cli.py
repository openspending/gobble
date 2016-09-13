"""The command line interface for Gobble"""

import io
import sys
from collections import defaultdict
from json import loads, dumps
from os.path import join, splitext, basename
from shutil import rmtree

from datapackage.exceptions import ValidationError
from gobble.config import ROOT_DIR, settings
from gobble.fiscal import FiscalDataPackage
from gobble.search import search as elasticsearch, ALLOWED_KEYS
from gobble.user import create_user, User
from click import (Choice,
                   command,
                   argument,
                   Path,
                   group,
                   option,
                   echo,
                   secho,
                   edit,
                   version_option)


DEFAULT_STYLE = dict(fg='white', bold=True)
ERROR_STYLE = dict(fg='red', bold=True)
SUCCESS_STYLE = dict(fg='green', bold=True)
ITEM_STYLE = dict(fg='yellow')

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


# Main command
# -----------------------------------------------------------------------------

def _get_package(key):
    filepath = join(ROOT_DIR, 'package.json')
    with io.open(filepath) as json:
        package = loads(json.read())
        return package[key]


@group(context_settings=CONTEXT_SETTINGS)
@version_option(
    version=_get_package('version'),
    prog_name=_get_package('slug'),
    is_flag=True,
)
def gobble():
    pass


# View
# -----------------------------------------------------------------------------

_FILES = [
    'log',
    'package',
    'settings',
    'token',
    'authentication',
    'permissions'
]


@command(
    epilog='FILE: %s' % ', '.join(_FILES),
    context_settings=CONTEXT_SETTINGS
)
@argument(
    'file',
    type=Choice(_FILES),
)
@option(
    '-e', '--editor',
    help='Open the file inside an editor.',
    is_flag=True
)
def view(file, editor):
    """Display (or edit) various Gobble files.

    Use the --editor option if you want to open the file inside an editor.
    Note that only the settings file is meant to be manually edited.
    """
    extension = '.log' if file == 'log' else '.json'
    file = 'gobble' if file == 'log' else file
    folder = ROOT_DIR if file == 'package' else settings.USER_DIR
    filepath = join(folder, file + extension)

    if editor:
        saved = edit(filename=filepath)
        if saved:
            secho('Saved changes to %s' % filepath, **SUCCESS_STYLE)

    else:
        try:
            with io.open(filepath) as cache:
                echo(cache.read())
        except FileNotFoundError:
            secho('%s could not be found' % filepath, **ERROR_STYLE)


# User
# -----------------------------------------------------------------------------

_ACTIONS = ['create', 'delete']


@command(context_settings=CONTEXT_SETTINGS)
@argument(
    'action',
    required=True,
    type=Choice(_ACTIONS),
    metavar='[' + '|'.join(_ACTIONS) + ']'
)
def user(action):
    """Create or delete a user.

    To create a new Gobble user, you need to be registered online. Gobble only
    supports a single user at a time. A work-around to switch user accounts is
    to delete and recreate a new user. Just make sure that you copy-paste the
    authorization link inside a private browser window when prompted.
    """
    if action == 'create':
        echo('Welcome to Open-Spending %s' % create_user())
    elif action == 'delete':
        rmtree(settings.USER_DIR)

        try:
            username = User.uncache('authentication')['username']
        except FileNotFoundError:
            username = 'user unknown'

        args = (settings.USER_DIR, username)
        secho('Deleted %s (%s)' % args, **DEFAULT_STYLE)


# Validate
# -----------------------------------------------------------------------------

@command(context_settings=CONTEXT_SETTINGS)
@argument(
    'filepath',
    required=True,
    type=Path(exists=True, resolve_path=True)
)
@option(
    '-s', '--schema',
    help='Validate only the schema.',
    is_flag=True
)
def validate(filepath, schema):
    """Validate a fiscal data-package.

    The FILEPATH is the relative or absolute path to a datapackage. By default,
    the command validates both the schema and the data files.
    """
    _, extension = splitext(filepath)
    filename = basename(filepath)

    if extension != '.json':
        secho('Expecting %s to be JSON file' % filepath, **ERROR_STYLE)
        sys.exit(1)

    package = FiscalDataPackage(filepath)
    error_messages = package.validate(raise_on_error=False, schema_only=schema)

    if error_messages:
        for error_message in error_messages:
            secho(error_message, **ERROR_STYLE)
    else:
        secho('SUCCESS! %s is valid' % filename, **SUCCESS_STYLE)


# Upload
# -----------------------------------------------------------------------------

@command(context_settings=CONTEXT_SETTINGS)
@argument(
    'filepath',
    type=Path(exists=True, resolve_path=True),
    required=True
)
@option(
    '-s', '--skip',
    help='Skip validation (not recommended).',
    is_flag=True
)
@option(
    '-p', '--private',
    help='Keep the online data-package private.',
    is_flag=True
)
def upload(filepath, private, skip):
    """Upload a fiscal package to Open-Spending.

    The FILEPATH is the relative or absolute path to the data-package file.
    The data is always validated before upload, unless validation is skipped
    explicitely. This is not recommended. Once uploaded, the data-package will
    published, unless you pass the --private flag.
    """

    user_ = User()
    package = FiscalDataPackage(filepath, user=user_)

    args = package, len(package), package.bytes
    message = 'Uploading %s to Open-Spending (%s files, %s bytes)...'
    secho(message % args, **DEFAULT_STYLE)

    try:
        url = package.upload(publish=not private, skip_validation=skip)

        state = 'privately' if private else 'publicly'
        args = package, state, url
        message = 'Congratulations! %s is now %s available online: %s.'

        secho(message % args, **SUCCESS_STYLE)

    except ValidationError:
        message = (
            'Upload aborted due to invalid data schema or data file. \n'
            'Use the validate command to find out more about the problem.'
        )
        secho(message, **ERROR_STYLE)


# Search
# -----------------------------------------------------------------------------

@command(context_settings=CONTEXT_SETTINGS)
@argument(
    'expression',
    required=False
)
@option(
    '-w', '--where',
    help='Search a specific field (may be repeated).',
    type=(Choice(list(ALLOWED_KEYS.keys())), str),
    nargs=2,
    metavar='KEY VALUE',
    multiple=True
)
@option(
    '-l', '--limit',
    help='Limit the number of results.',
    default=False,
    type=int
)
@option(
    '-p', '--private',
    help='Include private packages belonging to the user.',
    is_flag=True
)
@option(
    '-r', '--raw',
    help='Return the results as JSON.',
    is_flag=True
)
def search(expression, where, limit, private, raw):
    """Search fiscal packages on Open-Spending.

    You can search for an EXPRESSION across all keys or restrict yourself to
    specific keys using the --where option. You can also combine both
    approaches. Allowed search keys are:

    \b
        - title,
        - author
        - description
        - region
        - country
        - city

    The command returns a short summary of each matching fiscal package. To
    return the complete search results as JSON, pass the --raw flag. Results
    do not include the private packages of the current user by default.
    """
    results = elasticsearch(
        global_query=expression,
        keyed_query=dict(where),
        limit=limit,
        private=private
    )
    template = ('Country: {countryCode} \n'
                'Begin: {begin} \n'
                'End: {end} \n'
                'Author: {author} \n'
                'ID: {id}')

    if not raw:
        if results:
            for result in results:
                package = result['package']
                package.update(id=result['id'])

                if 'fiscalPeriod' in package:
                    begin = package['fiscalPeriod'].get('start', 'unknown')
                    end = package['fiscalPeriod'].get('end', 'unknown')
                    package.update(begin=begin)
                    package.update(end=end)

                info = defaultdict(lambda: 'unknown', **result['package'])
                url = '/'.join([settings.OS_URL, 'viewer', result['id']])

                secho('Title: %s' % package['title'], **ITEM_STYLE)
                secho(template.format(**info), **DEFAULT_STYLE)
                secho('View: %s' % url)
                secho('Download: %s \n' % result['origin_url'])

            summary = '%s packages matched your criteria.'
            secho(summary % len(results), **SUCCESS_STYLE)

        else:
            message = 'No online packages matched your criteria.'
            secho(message, **ERROR_STYLE)

    else:
        secho(dumps(results, ensure_ascii=False, indent=4))


gobble.add_command(validate)
gobble.add_command(upload)
gobble.add_command(user)
gobble.add_command(view)
gobble.add_command(search)
