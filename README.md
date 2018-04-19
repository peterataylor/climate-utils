# climate-utils

Python module for manipulating climate data,

Includes:

* disaggregating daily rainfall to hourly based on 

Boughton, W., _A Model for Disaggrgating Daily to Hourly Rainfalls for Design Flood Estimation_, Technical Report 00/15, CRC for Catchment Hydrology, November 2000. Available from [CRC for Catchment Hydrology Archives](http://www.ewater.org.au/archive/crcch/archive/pubs/1000046.html).

* computing areal average time series

## Installation

You'll need Python 3

```
pip install https://github.com/flowmatters/climate-utils/archive/master.zip
```

At this stage we haven't tagged releases so you just install from the latest version.

To upgrade, uninstall the one you've got, then install again

```
pip uninstall climate-utils
pip install https://github.com/flowmatters/climate-utils/archive/master.zip
```

**Note:** The areal average time series relies on a fork of the python-rasterstats package - if you already have python-rasterstats you'll need to replace it:

```
pip uninstall python-rasterstats
pip install https://github.com/joelrahman/python-rasterstats/archive/percent_cover.zip
```

