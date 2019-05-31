# geo_scout
Mapping Scouts data to UK administrative regions.

Prerequisites:
This is written and tested in Python 3.7.2.
There are several python packages that are required to be installed, including:
pandas
geopandas
folium

Getting Started:
You will need to obtain the latest version of the ONS Postcode Directory. Note
that this has some open licences attached to it.
If this is not May 2018, then you will need to create another child class of
ONSData in ONS_data.py
You will need to populate the settings.json file with the appropriate file paths

Notes:
I suspect that this will generalise beyond the specific application to Scouts,
but I have not done so. I anticipate to progress to this point, but unfortunately
the code will only work out of the box with data structured as an extract of
the Scout Census.

The documentation and commenting are imperfect and being improved, and can be
found here: 

I would welcome any support, comments or guidance on my code.

This project is licensed under the GNU License - see the LICENSE file for details
