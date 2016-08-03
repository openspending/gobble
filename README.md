# Gobble

[Open-Spending](next.openspending.org) is an international platform to package, share and visualize budget data. Gobble does exactly the same thing as the [packager module](next.openspending.org/packager), but programatically. It can be used both as python client or a command line interface. It's compatible with versions 2.7, 3.3, 3.4 and 3.5. You can install it via `pip`.

```
pip install gobble
```

## Fiscal Data Packages

A [Datapackage](http://frictionlessdata.io/data-packages/) is a lightweight container for data. A [Fiscal Data Package](http://fiscal.dataprotocols.org/) is a data package for government budget and spending data. It's user-oriented and aims to be extremely easy to use, both for those publishing data (e.g. governments) and for those wanting to use the data (such as researchers and journalists). 

Technically speaking, a fiscal datapackage consists of a `JSON` descriptor asociated with data files. The JSON descriptor needs to follow the specifications described [here](http://fiscal.dataprotocols.org/spec/). A basic local fiscal data package looks like this:

```
/basepath/budget.json   
         /data/budget_2014.csv
               budget_2015.csv

```


## Command line interface

Asciinema to come... 


## Fiscal data package objects

In Gobble, fiscal data is represented by the `FiscalDataPackage` class. It's a sub-class of the `DataPackage` class, defined by the [datapackage-py](https://github.com/frictionlessdata/datapackage-py) library. To create a `FiscalDataPackage`, pass the path of you descriptor to the constructor:

```
budget = FiscalDataPackage('path/to/my/bad/package/descriptor.json')

```

Once you have you fiscal data package object, you can play with it like an ordinary `DataPackage`. You can for example iterate over the data. Note that as of today, Open-Spending only supports data files in CSV format.

## Validation

To validate the fiscal datapackage descriptor file:

```
bugdet.validate()
```

If the descriptor schema is invalid, a `ValidationError` will be raised. To get a `list` of errors instead, use the `check` method. 
```
budget.check()
```

## Upload

To upload a fiscal data package to Open-Spending: 

```
url = budget.upload()  # the url of your new package on Open-Spending
```

By default, uploaded packages are private, to publish them, do:

```
new_state = budget.toggle('public') # should return 'public'
```

## Search and downloand

You can search and download fiscal data packages from the Open-Spending platform using the `pull` function, like so:

```
query = {'countryCode': 'MX'}
results = pull(query)
```

The `results` is a `dict`. Valid search keys are: `size`, `title`, `author`, `description`, `regionCode`, `countryCode`, `cityCode`. Or you can use the magic  `q` key to search all fields at once.

## Resources

- [Open-Spending web platform](next.openspending.org) 
- [Open-Spending docs for developers](http://docs.openspending.org/en/latest/)
- [datapackage-py package repository](http://frictionlessdata.io/data-packages/) 
- [Fiscal Data Package homepage](http://fiscal.dataprotocols.org/)
- [Open-Knowledge Foundation](https://okfn.org)

## License

Gobble is under MIT License.

## Contributions

We welcome feedback, issues and pull-requests. You can find []