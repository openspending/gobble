"""Search for users and package inside the ElasticSearch database"""


from gobble.api import search_packages, handle
from gobble.user import user


SEARCH_KEYS = ['q', 'size', 'title', 'author', 'description',
               'regionCode', 'countryCode', 'cityCode']


def search(query, private=True, limit=None):
    """Query the packages on Open-Spending.

    You can search a package by `title`, `author`, `description`, `regionCode`,
    `countryCode` or`cityCode`. You can match all these fields at once with the
    magic `q` key.

    If authentication-token was provided, then private packages from the
    authenticated user will also be included. Otherwise, only public packages
    will be returned. You can limit the size of your results with the `size`
    parameter.

    :param query: a `dict` of key value pairs
    :param private: show private datapackages
    :param limit: the number of results returned

    :type query: `dict`
    :rtype private: `bool'
    :rtype size: `int'

    :return: a dictionary with the results
    :rtype: :class: `list` of `dict`
    """
    _validate(query)

    if limit:
        query.update(size=limit)

    quoted_query = _sanitize(query)

    if private:
        quoted_query.update(jwt=user.token)

    response = search_packages(params=quoted_query)
    return handle(response)


def _sanitize(query):
    keys = ['package.' + str(k) for k in query.keys()]
    values = ['"' + str(v) + '"' for v in query.values()]
    return dict(zip(keys, values))


def _validate(query):
    for key in query.keys():
        if key not in SEARCH_KEYS:
            msg = 'Invalid search key "{key}" for package'
            raise ValueError(msg.format(key=key))
