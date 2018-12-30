from postcode_to_constituency import PostcodeToArea
# pandas 0.23.3

ONS_PD = r"Census 2018\pcluts_2018may\pcluts_2018may\ONSPD_MAY_2018_UK.csv"

# Input csv file must have a column called "Postcode"
input_csv = r"Census 2018 Sections Special (4) - edits.csv"

output_csv = r"Census 2018 Sections Special (4) with ONS fields.csv"

# Fields of the ONS Postcode Directory
fields = ['lsoa11','msoa11','oslaua','osward','pcon','oscty','ced','oseast1m','osnrth1m','lat','long','imd']

mapping = PostcodeToArea(ONS_PD, input_csv, output_csv, fields)
mapping.ERROR_FILE = "error_file.txt"
mapping.create_output()
