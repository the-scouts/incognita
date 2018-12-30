# geo_scout
Using GeoJSON data to map data to UK administrative regions

The major object based files are:
cholopleth.py
postcode_to_constituency.py

Files that begin with script_* use these objects to perform analysis.
script_census_postcode_lookup.py is an example of using postcode_to_constituency
script_parl_con_report.py is an example of using postcode_to_constituency and data analysis
script_constituency_heat_map.py is an example of using cholopleth

PostcodeToArea is an object defined in postcode_to_constituency
The constructor takes the following arguments:
1. data_csv - path to an ONS Postcode Directory .csv file
2. input_csv - path to a csv file where exactly one column has CENSUS_POSTCODE_HEADING as a heading.
               Supports 'latin-1' encoding of text.
3. output_csv - path to location of where the output should be stored. The output is the
                original csv with the additional column 'clean_postcode' and the administrative
				areas specified by fields
4. field - this is a list of column headings to be extracted from the ONS Postcode Directory

Additionally the following properties, or member variables may be set:
DEFAULT_VALUE - the string assigned to the new columns that represent the administrative areas
CLEAN_POSTCODE - the string that is the heading of the new 'clean_postcode' field
SECTIONS - a list of strings that identify the record as belonging to a Section
ONSPD_POSTCODE_FIELD - the string that identifies the column in the ONS PD that is consulted for
                       the postcode
CENSUS_GROUP_ID - the string that is the column heading of the unique identifier for the Group
CENSUS_DISTRICT_ID - the string that is the column heading of the unique identifier for the District
CENSUS_TYPE_GROUP - string that identifies the record as a Group
CENSUS_TYPE_DISTRICT - string that identifes the record as a District
CENSUS_TYPE_ENTITY - a list of strings that contains indicators of not being a Section
CENSUS_TYPE_HEADING - the string that is the column heading containing the type of record in the Scout Census
CENSUS_POSTCODE_HEADING - the string that is the column heading containing the postcodes in the input_csv
ERROR_FILE - name of the error file that the unrecognised postcodes are written to
postcode_re - a result of re.compile that is a compiled regular expression to compare strings against
              to determined the validity of the postcode.

Once the PostcodeToArea object is created run self.create_ouput() to produce an output csv in the location
specified by self.output_csv, that contains the original data with the additional columns containing the 
cleaned postcode and the administrative areas that have been looked up.

In addition the following additional functions are defined, which are not part of the API:
_write_row(self, row_index, sub_data)
Copys the information from the first row of sub_data into row_index of the input file.
_row_from_field(self, field, value)
Returns the rows that in the column specified by field have that value in the ONS Postcode Directory (self.data)
postcode_cleaner(self, postcode)
Given a postcode in any format, returns a cleaned postcode in the 7 character format.

CholoplethMapPlotter is an object defined in cholopleth.py
The constructor takes the following arguments:
1. shape_files - a list of strings which are paths to '.shp' files
2. csv_file - a .csv file with columns 'Geo_code' and 'Score'. The 'Geo_code' column contains the key used
              in the lookup to find the GPS coordinates in the shape_files. The Score is the parameter used
			  to colour the area.
3. out_file - the path ending in '.html' of the html file where the map is saved to
4. code_name - the name of field in the '.shp' file which matches the values in the 'Geo_code' column of the
               csv_file
5. color - The colourscale used. May be one of the scales recognised by ColorBrewer, which is one of the following strings:
           'BuGn','BuPu','GnBu','OrRd','PuBu','PuBuGn','PuRd','RdPu','YlGn','YlGnBu','YlOrBr','YlOrRd','BrBg','PiYG','PRGn','PuOr',
           'RdBu','RdGy','RdYlBu','RdYlGn','Spectral','Accent','Dark2','Paired','Pastel1','Pastel2','Set1', 'Set2', 'Set3'
6. scale - a list of numbers at which the thresholds should be set. Up to 6 values may be entered in ascending order.
           Ensure the lowest value in 'Score' in csv_file is higher than the lowest threshold value, and the highest 'Score' is
		   lower than the highest threshold value.
7. legend_label - The string to go alongside the legend, to explain the values

The main usage is calling the constructor, then the plot method which creates the map. Then to see the map, the show method
will open the .html map in a webbrowser (alternatively the .html file may be opened manually).

In addition there is a method convert_shape_to_geojson, which converts the .shp files in self.shape_files to GeoJSON format.