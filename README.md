# Gobble

[Open-Spending](next.openspending.org) is a web platform for  provides a web-inteface to package and upload data. You can do the same thing programatically `gobble` is a both client and a command line interface  written in Python. It's compatible with versions2.7, 3.3, 3.4 and 3.5. You can install it via `pip`.

```
pip install gobble
```

## Fiscal Data Packages

A [Datapackage](http://frictionlessdata.io/data-packages/) is a lightweight container for data. A [Fiscal Data Package](http://fiscal.dataprotocols.org/) is an open technical specification for government budget and spending data. It user-oriented and aims to be extremely easy to use, both for those publishing data (e.g. governments) and for those wanting to use the data (such as researchers and journalists). Basically, a is a simple `JSON` file schema, whose specifications you can find [here](http://fiscal.dataprotocols.org/spec/). 

In Gobble, fiscal data is represented by the `FiscalDataPackage` class. It's a sub-class of the `DataPackage` class, implemented bu the {datapackage-py library](https://github.com/frictionlessdata/datapackage-py). To create a local `FiscalDataPackage` you will to create directory structure that looks like this:

```
/basepath/descriptor.json   
         /data/file1.csv
               file2.csv

```



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
budget.check_schema()
```

## Upload

To upload a fiscal data package to Open-Spending: 

```
url = budget.upload()  # the url of the package on Open-Spending
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
- [Open]

## License

Gobble is under MIT License.

## Contributions

Gobble is in Alpha release. We welcome feedback, issues and pull-requests. You can find []