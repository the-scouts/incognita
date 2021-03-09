# geo_mapping
Mapping Scouts data to UK administrative regions.

[![Build Status](https://travis-ci.com/the-scouts/geo_mapping.svg?branch=master)](https://travis-ci.com/the-scouts/geo_mapping)
[![codecov](https://codecov.io/gh/the-scouts/geo_mapping/branch/master/graph/badge.svg)](https://codecov.io/gh/the-scouts/geo_mapping)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Prerequisites:
This is written and tested in Python 3.8.

This project is largely dependent on `geopandas` and `pandas`, along with `folium`, `dash`, and `shapely`.

For testing we use `pytest` and `coverage`, with `black` as our codestyle.

## Getting Started:
You will need to obtain the latest version of the ONS Postcode Directory. Note
that this has some open licences attached to it.

If this is not May 2018, then you will need to create another child class of
ONSPostcodeDirectory in `ONS_data.py`

You will need to populate the settings.json file with the appropriate file paths

### Installing required packages:
It is highly recommended to use conda to install this project, however pip can be used with a number of manual installation steps listed below.


#### Installing with Conda:
To install dependencies with Conda, run the following commands in the terminal

`conda env update`

`conda env list` (Check that `scouts_mapping` is listed)

`conda activate scouts_mapping`

#### Installing with Pip
To install dependencies with Conda, run the following commands in the terminal

`pip install -r requirements.txt`

To install geopandas and its dependencies, follow below

##### Installing geopandas:
It is highly recommended to use conda to install geopandas.

However, to install geopandas using pip on windows, follow the following steps:
* Download the wheels for [GDAL](http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal), [Fiona](http://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona), and [Rtree](http://www.lfd.uci.edu/~gohlke/pythonlibs/#rtree). Choose the correct python version (currently 3.8) and platform
* Install any prerequisites listed on Gohlke's site (e.g. C++ redistributables)
* `pip install` the wheels in the following order (preferably in a Virtual Environment)
    1. [GDAL](http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)
    2. [Fiona](http://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona)
    3. [Rtree](http://www.lfd.uci.edu/~gohlke/pythonlibs/#rtree)
* `pip install geopandas`

### Generating datafile
To generate the datafile needed for most operations, run `setup_data_file.py` with clean prototype extract.

You may also run `setup_reduce_onspd.py` to produce a smaller ONS Postcode Directory file to speed up lookup operations and reduce memory consumption. 

## Resources:
### Postcode Directory:
 * Latest ONS Postcode Directory ([link](https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-modified&tags=ons%20postcode%20directory))

### Shapefiles:
#### Administrative/Electoral Geographies:
_Use the same boundary resolution for each of the following (BFE, BFC, BGC, BUC)_
###### BFE: Full Extent of the Realm; BFC: Full Extent Clipped; BGC: Generalised Clipped; BSC: Super Generalised Clipped
 * Local Authority Districts Boundaries UK BGC ([link](https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-modified&tags=bdy_lad))
 * Counties and Unitary Authorities Boundaries UK BGC ([link](https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-modified&tags=BDY_CTYUA))
 * Wards Generalised Clipped Boundaries UK ([link](https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-modified&tags=BDY_WD))
 * Westminster Parliamentary Constituencies UK BGC ([link](https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-modified&tags=BDY_PCON))

#### Census Geographies:
##### England and Wales:
 * Lower Layer Super Output Areas ([link](https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-modified&tags=BDY_LSOA%2CDEC_2011))
 * Middle Layer Super Output Areas ([link](https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-modified&tags=BDY_MSOA))
##### Scotland:
 * Data Zones
 * Intermediate Geographies ([link](https://data.gov.uk/dataset/133d4983-c57d-4ded-bc59-390c962ea280/intermediate-zone-boundaries-2011))
##### Northern Ireland:

### Single year of age profiles:
#### Westminster Parliamentary Constituencies:
 * England and Wales ([link](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/parliamentaryconstituencymidyearpopulationestimates))
 * Northern Ireland ([link](https://www.nisra.gov.uk/publications/2018-mid-year-population-estimates-northern-ireland))
 * Scotland ([link](https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/population/population-estimates/2011-based-special-area-population-estimates/ukpc-population-estimates))

### Other useful data sources
 * School locations: https://get-information-schools.service.gov.uk/

### Guide:
The Beginner's Guide to UK Geography ([link](https://geoportal.statistics.gov.uk/search?collection=Document&sort=name&tags=DOC_BGG)) can be useful as an introduction for those new to GIS.

## Directory Structure:
* data/
    * ONS_PD_**DATE**/
    * Scout Census Data/
        * _Census Extract Files_

## Notes
I suspect that this will generalise beyond the specific application to Scouts,
but I have not done so. I anticipate to progress to this point, but unfortunately
the code will only work out of the box with data structured as an extract of
the Scout Census.

The documentation and commenting are imperfect and being improved, and can be
found here:

I would welcome any support, comments or guidance on my code.

## Branches
The heroku branch is specifically for the heroku application: http://scout-mapping.herokuapp.com. It contains a cut down requirements file to ensure that it
loads into heroku correctly.

*This project is licensed under the GNU License - see the LICENSE file for details*
