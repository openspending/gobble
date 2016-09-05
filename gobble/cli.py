"""The command line interface for Gobble"""

import io

from collections import defaultdict
from json import dumps, loads
from os import getcwd
from os.path import join, splitext, basename
from shutil import rmtree
from click import (Choice,
                   command,
                   argument,
                   Path,
                   group,
                   option,
                   echo,
                   secho,
                   edit,
                   version_option,
                   pass_context)

from gobble.config import ROOT_DIR, settings
from gobble.fiscal import FiscalDataPackage, OS_DATA_FORMATS
from gobble.search import search, SEARCH_ALIASES
from gobble.user import create_user, User


# Gobble: parent command
# -----------------------------------------------------------------------------

def _get_package(key):
    filepath = join(ROOT_DIR, 'package.json')
    with io.open(filepath) as json:
        package = loads(json.read())
        return package[key]


@group(
    invoke_without_command=True,
    context_settings={'help_option_names': ['-h', '--help']}
)
@version_option(
    version=_get_package('version'),
    prog_name=_get_package('slug'),
    is_flag=True,
)
def gobble():
    pass


# View: sub-command
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
    epilog='FILE: %s' % ', '.join(_FILES)
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
            secho('Saved changes to %s' % filepath, fg='green')

    else:
        try:
            with io.open(filepath) as cache:
                echo(cache.read())
        except FileNotFoundError:
            secho('%s could not be found' % filepath, fg='red')


# User: sub-command
# -----------------------------------------------------------------------------

_ACTIONS = ['create', 'delete']


@command()
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
        user_ = User()
        rmtree(settings.USER_DIR)
        echo('Deleted %s\' cache' % user_)


# Check: sub-command
# -----------------------------------------------------------------------------

@command()
@argument(
    'target',
    required=True,
    type=Path(exists=True, resolve_path=True)
)
@option(
    '--data',
    help='Treat this JSON file as a data file.',
    is_flag=True
)
@option(
    '--package',
    help='Validate both schema and data files.',
    is_flag=True
)
@pass_context
def check(context, target, data, package):
    """Validate a fiscal data-package.

    The TARGET is the relative or absolute path to a descriptor or data file.
    JSON files are assumed to be descriptor files, unless the --data option is
    passed. To validate and entire fiscal data-package (i.e. both the schema
    and the data files), point to the package descriptor with the --package
    flag.
    """
    _, extension = splitext(target)

    if extension == '.json' and not data:
        fiscal_package = FiscalDataPackage(target)
        errors = fiscal_package.validate(raise_error=False)
        if errors:
            for error in errors:
                message = '%s | ERROR | %s'
                args = basename(target), error
                secho(message % args, fg='red', bold=True)
        else:
            message = '%s | SUCCESS | valid schema'
            secho(message % basename(target), fg='green')
        if package:
            resources = fiscal_package.descriptor['resources']
            paths = [file['path'] for file in resources]
            context.package = fiscal_package
        else:
            paths = []
    else:
        paths = [target]

    for path in paths:
        _, extension = splitext(path)
        if extension in OS_DATA_FORMATS:
            message = '%s: data validation not supported yet'
            secho(message % path, fg='white')
        else:
            message = '%s: extension not supported by Open-Spending'
            secho(message % basename(path), fg='blue')


# Push: sub-command
# -----------------------------------------------------------------------------

@command()
@argument(
    'target',
    type=Path(exists=True, resolve_path=True),
    required=True
)
@pass_context
def push(context, target):
    """Upload a fiscal package to Open-Spending.


    """
    if hasattr(context, 'package'):
        package = context.package
    else:
        user_ = User()
        package = FiscalDataPackage(target, user=user_)

    package.upload()


# Pull: sub-command
# -----------------------------------------------------------------------------

@command()
def pull(name, owner, data=False, destination=getcwd()):
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


@command()
@argument(
    'expression',
    required=False
)
@option(
    '--where',
    help='Search a specific field (may be repeated).',
    type=(Choice(list(SEARCH_ALIASES.keys())), str),
    nargs=2,
    metavar='FIELD VALUE',
    multiple=True
)
@option(
    '--limit',
    help='Limit the number of results.',
    default=False,
    type=int
)
@option(
    '--raw',
    help='Return the raw JSON response.',
    default=False,
    is_flag=True
)
def search(expression, where, limit, raw):
    """Search fiscal packages on Open-Spending.

    You can search for an EXPRESSION across all fields or restrict yourself to
    specific fields using the --where option. You can also combine both
    approaches. Allowed search fields are: "title", "author", "description",
    "region", "country" and "city".

    The command returns a one line summary of each matching fiscal package. To
    return the complete search results as JSON, pass the --raw flag. Results
    always include private unpublished packages if a Gobble user is set up.
    """
    results = search(value=expression, query=where, limit=limit)

    if raw:
        echo(results[0] if len(results) == 1 else results)
    else:
        if results:
            for result in results:
                template = '[{countryCode}] "{title}" by {author}'
                info = defaultdict(lambda: 'unknown', **result)
                secho(template, **info)
        else:
            message = 'No online packages match your criteria.'
            secho(message, fg='yellow')


gobble.add_command(check)
gobble.add_command(pull)
gobble.add_command(push)
gobble.add_command(user)
gobble.add_command(view)
gobble.add_command(search)
