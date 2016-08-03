# Gobble

Gobble is the client API for [Open-Spending](next.openspending.org), an international platform to package, share and visualize budget data. Gobble does exactly the same thing as the [packager interface](next.openspending.org/packager), except programatically. It can be used both as python client or a command line interface. It's compatible with versions 2.7, 3.3, 3.4 and 3.5. You can install it via `pip`.

```
pip install gobble
```

## Fiscal Data Packages

A generic [Datapackage](http://frictionlessdata.io/data-packages/) is a lightweight container for data. A [Fiscal Data Package](http://fiscal.dataprotocols.org/) is a special type of data package for government budget and spending data. It's user-oriented and aims to be extremely easy to use, both for those publishing data (e.g. governments) and for those wanting to use the data (such as researchers and journalists). 

Technically speaking, a fiscal datapackage consists of a `JSON` descriptor pointing to data files. The `JSON` descriptor needs to follow [fiscal data specifications](http://fiscal.dataprotocols.org/spec/). A basic local fiscal data package could look like this:

```
/basepath/budget.json   
         /data/budget_2014.csv
               budget_2015.csv
```

Once your fiscal data package is ready, you can start using Gooble.

## Command line interface

Asciinema to come... 

## Python client

### Fiscal data package objects

In Gobble, fiscal data is represented by the `FiscalDataPackage` class. It's a sub-class of the `DataPackage` class, defined in the [datapackage-py](https://github.com/frictionlessdata/datapackage-py) library. To create a `FiscalDataPackage` object, pass the path of your descriptor to the constructor:

```
budget = FiscalDataPackage('path/to/my/package/descriptor.json')
```

Note that as of today, Open-Spending only supports data files in `CSV` format, so `FiscalDataPackage` will raise a `NotImplemented` error if you try and pass it other formats.

### Validation

To validate the fiscal datapackage descriptor schema:

```
bugdet.validate()
```

If the descriptor schema is invalid, a `ValidationError` will be raised. To get a `list` of errors instead, set the `raise_error` flag to `False`.
```
budget.validate(raise_error=False)
```

### Upload

To upload a fiscal data package to Open-Spending: 

```
url = budget.upload()  # the url of your new package on Open-Spending
```

By default, uploaded packages are private. You can toggle the publication state like so:

```
new_state = budget.toggle('public') # returns 'public'
```

###  Search

You can search (and download) the descriptor file of existing fiscal data packages from the Open-Spending platform like so:

```
query = {'countryCode': 'MX'}
results = search(query)
```

where `results` is list of `JSON` package descriptors (as `dict`). Valid search keys are: `size`, `title`, `author`, `description`, `regionCode`, `countryCode`, `cityCode`. Or you can use the magic  `q` key to search all fields at once.

You can limit search results and include you private packages in the results like so:

```
query = {'author': 'mickey_mouse'}
results = search(query, limit=5, private=True)
```

## Resources

- [Open-Spending web platform](next.openspending.org) 
- [Open-Spending docs for developers](http://docs.openspending.org/en/latest/)
- [datapackage-py package repository](http://frictionlessdata.io/data-packages/) 
- [Fiscal Data Package homepage](http://fiscal.dataprotocols.org/)
- [Open-Knowledge Foundation](https://okfn.org)

## License

Gobble is under [MIT License](https://opensource.org/licenses/MIT).

## Contributions

We welcome feedback, issues and pull-requests. Please check out the [contribution guidelines](https://github.com/okfn/coding-standards). 