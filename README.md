ebcrawler
=========

This is a simple tool to download your EB history from the SAS website, either for
viewing or in a format suitable for example to import into Excel.

Requirements
------------

* Python3
* requests library (can usually be installed with `pip install requests`)

Everything else should be included in python3 by default.

Usage
-----

```
usage: ebcrawler.py [--password PASSWORD] [--all] [--pages PAGES]
                    [--csv CSV]
                    ebnumber
```

`ebnumber` is the EB number (9 digits, do not include the prefix).

If `password` is not specified, it will be prompted for.

By default, one page of transactions (20 transactions) is fetched. By
specifying `--all`, all pages available will be fetched, and by
specifying `--pages PAGES`, the specified number of pages will be fetched.

By default, the results are printed to the output in a readable format.
If `--csv filename.csv` is specified, the output will be written to the file
`filename.csv` in a format suitable for importing into for example a
spreadsheet.
