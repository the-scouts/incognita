# Incognita

[![codecov](https://codecov.io/gh/the-scouts/incognita/branch/master/graph/badge.svg)](https://codecov.io/gh/the-scouts/incognita)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Incognita is a tool to map UK Scout data and enable geospatial analysis.

We use ONS open data to link scout areas (Groups, Districts, etc.) to UK 
administrative geographies.

*Incognita comes from* Terra Incognita, *or Parts Unknown - solving the known 
unknowns!*

## Where to get it

The source code for the project is hosted on GitHub at
[the-scouts/incognita](https://github.com/the-scouts/incognita)

We **strongly** recommended using `conda` to install *incognita*, however pip 
can be used with a number of manual installation steps as below.

To install dependencies with Conda, run the following commands in the terminal
```shell
# conda
conda env update
conda activate incognita
```

```shell
# or PyPI
pip install -r requirements.txt
```
If installing with `pip`, you will need to manually install geopandas and its
dependencies. Please follow below:

### Installing geopandas:
We **strongly** recommended using `conda` to install geopandas.

However, to install geopandas using pip on Windows, follow the following steps:
1. Download the wheels for
   [GDAL](http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal),
   [Fiona](http://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona), and
   [Rtree](http://www.lfd.uci.edu/~gohlke/pythonlibs/#rtree). Choose the
   correct platform and python version (currently 3.9).
2. Install any prerequisites listed on Gohlke's site (e.g. C++ re-distributables)
3. `pip install` the wheels in the following order (preferably in a Virtual
   Environment)
    1. [GDAL](http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)
    2. [Fiona](http://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona)
    3. [Rtree](http://www.lfd.uci.edu/~gohlke/pythonlibs/#rtree)
4. `pip install geopandas`

### Dependencies
This project is written and tested in Python 3.9, and depends on:

- [geopandas](https://github.com/geopandas/geopandas),
  [pandas](https://github.com/pandas-dev/pandas) - for (geospatial) data
  transformation and arrangement
- [folium](https://github.com/python-visualization/folium) - for rendering to
  [Leaflet.js](https://github.com/Leaflet/Leaflet) maps
- [shapely](https://github.com/Toblerity/Shapely) - for manipulation and
  analysis of geometric objects
- [dash](https://github.com/plotly/dash) - for simple web-apps

## Getting Started:
You will need to obtain the latest version of the ONS Postcode Directory. Note
that this has some open licences attached to it.

If this is not May 2018, then you will need to create another child class of
ONSPostcodeDirectory in `ONS_data.py`

You will need to populate the settings.json file with the appropriate file paths

### Generating the data file
To generate the datafile needed for most operations, run `setup_data_file.py` 
with clean prototype extract.

You may also run `setup_reduce_onspd.py` to produce a smaller ONS Postcode 
Directory file to speed up lookup operations and reduce memory consumption. 

## Resources:
### Postcode Directory:
 * Latest 
   [ONS Postcode Directory](https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-modified&tags=ons%20postcode%20directory)

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

## Branches
The heroku branch is specifically for the heroku application: http://scout-mapping.herokuapp.com. It contains a cut down requirements file to ensure that it
loads into heroku correctly.

## License

***Incognita*** is naturally
[open source](https://github.com/the-scouts/incognita) and is
licensed under the **[MIT license](https://choosealicense.com/licenses/mit)**.

