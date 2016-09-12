"""Search for users and package inside the ElasticSearch database"""


from gobble.api import search_packages, handle
from gobble.user import User


ALLOWED_KEYS = {
    'title': 'title',
    'author': 'author',
    'description': 'description',
    'region': 'regionCode',
    'country': 'countryCode',
    'city': 'cityCode'
}


def search(global_query=None, keyed_query=None, private=True, limit=None):
    """Query the packages on Open-Spending.

    You can search a package by `title`, `author`, `description`, `regionCode`,
    `countryCode` or`cityCode`. You can match all these fields at once with the
    magic `q` key.

    If authentication-token was provided, then private packages from the
    authenticated user will also be included. Otherwise, only public packages
    will be returned. You can limit the size of your results with the `size`
    parameter.

    :param global_query: an expression to search for across all keys
    :param keyed_query: a `dict` of key/value search pairs
    :param private: search private datapackages or not (default: True)
    :param limit: the number of results returned (default: None)

    :return: a dictionary with the results
    :rtype: :class: `list` of `dict`
    """

    assert global_query or keyed_query

    if keyed_query:
        _check_keys(keyed_query)
        raw_query = _prefix_keys(keyed_query)
    else:
        raw_query = {}

    if global_query:
        raw_query.update(q=global_query)

    query = _quote_values(raw_query)

    if limit:
        query.update(size=limit)

    if private:
        query.update(jwt=User().token)

    response = search_packages(params=query)
    return handle(response)


def _quote_values(query):
    values = ['"' + str(v) + '"' for v in query.values()]
    return dict(zip(query.keys(), values))


def _prefix_keys(query):
    keys = ['package.' + str(ALLOWED_KEYS[k]) for k in query.keys()]
    return dict(zip(keys, query.values()))


def _check_keys(query):
    for key in dict(query).keys():
        if key not in ALLOWED_KEYS:
            msg = 'Invalid search key "{key}"'
            raise ValueError(msg.format(key=key))


if __name__ == '__main__':
    search(global_query='loic', private=True)
