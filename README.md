[![Build Status](https://travis-ci.org/openspending/gobble.svg?branch=master)](https://travis-ci.org/openspending/gobble)

# Gobble

Gobble is the client API for [Open-Spending](next.openspending.org), an international platform to package, share and visualize budget data. Gobble does exactly the same thing as the [packager interface](next.openspending.org/packager), except programatically. It can be used both as python client or a command line interface. It's compatible with versions 3.3, 3.4, 3.5. Support for 2.7 is in the works. You can install it via `pip`.

```
pip install os-gobble
```

## Fiscal Data Packages

A generic [Datapackage](http://frictionlessdata.io/data-packages/) is a lightweight container for data. A [Fiscal Data Package](http://fiscal.dataprotocols.org/) is a special type of data package for government budget and spending data. It's user-oriented and aims to be extremely easy to use, both for those publishing data (e.g. governments) and for those wanting to use the data (such as researchers and journalists). 

Technically speaking, a fiscal datapackage consists of a `JSON` descriptor pointing to data files. The `JSON` descriptor needs to follow [fiscal data specifications](http://fiscal.dataprotocols.org/spec/). A basic local fiscal data package could look like this:

```
/basepath/budget.json   
         /data/budget_2014.csv
               budget_2015.csv
```

Once your fiscal data package is ready, you can start using Gobble.

## Command line interface

Asciinema to come... 

## Python client

### Fiscal data package objects

In Gobble, fiscal data is represented by the `FiscalDataPackage` class. It's a sub-class of the `DataPackage` class, defined in the [datapackage-py](https://github.com/frictionlessdata/datapackage-py) library. To create a `FiscalDataPackage` object, pass the path of your descriptor to the constructor:

```
user = User()
budget = FiscalDataPackage('path/to/my/package/descriptor.json', user=user)
```

Note that as of today, Open-Spending only supports data files in `CSV` format, so `FiscalDataPackage` will raise a `NotImplementedError` error if you try and pass it other formats.

### Validation

To validate the fiscal datapackage schema and data:

```
bugdet.validate()
```

If the datapackage is invalid, a `ValidationError` will be raised. To get a `list` of errors instead (more helpful), set the `raise_on_error` flag to `False`.
```
budget.validate(raise_error=False)
```

### Upload

To upload a fiscal data package to Open-Spending: 

```
url = budget.upload()  # the url of your package in the Open-Spending Viewer
```

By default, uploaded packages are published straight away. You can toggle the publication state like so:

```
new_state = budget.toggle('private') # returns 'private'
```

###  Search

You can search existing fiscal data packages from the Open-Spending platform like so:

```
results = search('mexico')
results = search('MX', {'author': 'mickey_mouse'})
```

where `results` is a `list` of datapackages (`dict`). Available search keys are: `size`, `title`, `author`, `description`, `region`, `country`, `city`. 

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
