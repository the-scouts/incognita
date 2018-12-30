from cholopleth import CholoplethMapPlotter
import pandas as pd

# This script creates a colourful map based on data, the map is a .html file.

# There are a number of shape files (.shp) that contain the GPS coordinates of
# the boundaries of the administrative areas that can be obtained from ONS.

# A datafile located in DATA_LOC called NAME must be a .csv file with column
# names Geo_code and Score. Geo_code must be the ONS code reference to the
# administrative area contained in the shape file. Score is the scale along
# which the colour is applied.

# Edits to this script should be made on the line which creates the
# 'ChloroplethMapPlotter' object.

ENG_SHAPE = r"Boundary shape files\England_parl_2011_gen_clipped\england_parl_2011_gen_clipped.shp"
SCOT_SHAPE = r"Boundary shape files\Scotland_parlcon_2011_clipped\scotland_parlcon_2011_clipped.shp"
WELSH_SHAPE = r"Boundary shape files\Wales_parl_2011_gen_clipped\wales_parl_2011_gen_clipped.shp"
NI_SHAPE = r"Boundary shape files\NIreland_aa_2008\nireland_aa_2008.shp"

PCON_SHAPE = [r"Boundary shape files\Westminster_PCON_Dec_2017_Generalised_Clipped_UK\Westminster_Parliamentary_Constituencies_December_2017_Generalised_Clipped_Boundaries_in_the_UK.shp"]
LAD_SHAPE = [r"Boundary shape files\Local_Authority_Districts_December_2017_Clipped_UK_WGS84\Local_Authority_Districts_December_2017_Full_Clipped_Boundaries_in_United_Kingdom_WGS84.shp"]
MSOA_SHAPE = [r"Boundary shape files\Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales\Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp"]
IZ_SHAPE = [r"Boundary shape files\SG_IntermediateZoneBdry_2011\SG_IntermediateZone_Bdry_2011.shp"]
WARD_SHAPE = [r"Boundary shape files\Wards_December_2016_Generalised_Clipped_Boundaries_in_Great_Britain\Wards_December_2016_Generalised_Clipped_Boundaries_in_Great_Britain.shp"]

NAME = r"msoa11_data"
DATA_LOC = r""

scouting_level = 'Region (England/Wales'
scouting_values = ['South West']

CSV = DATA_LOC + NAME + ".csv"
OUTPUT = "Census 2018\\Maps\\"

LAD = [LAD_SHAPE,'lad17cd']
PCON = [PCON_SHAPE, 'pcon17cd']
MSOA = [MSOA_SHAPE, 'msoa11cd']
OSWARD = [WARD_SHAPE, 'wd16cd']
IZ = [IZ_SHAPE, 'InterZone']

# Highlevel overview of inputs:
# 1. Shape file  path
# 2. Data (.csv) file  path
# 3. Output (.html) file
# 4. Key name in the shape file that is in the Geo_code column
# 5. Colour scale
# 6. Threshold values, if none uses default
# 7. Legend label in the map
score_fields = [{'field_name': "%-Beavers", 'section_label': ["C"]},
                {'field_name': "%-Cubs", 'section_label': ["P"]},
                {'field_name': "%-Scouts", 'section_label': ["T"]},
                {'field_name': "%-Explorers", 'section_label': ["U","Y"]},
                {'field_name': "%-All", 'section_label': ["C","P","T","U","Y"]}]

data = pd.read_csv(CSV)

code = 'msoa11'

sections_csv = r"Census 2018 Sections Special (4) with ONS fields.csv"
sections_pd = pd.read_csv(sections_csv,encoding='latin-1')

sections = sections_pd.loc[sections_pd[scouting_level].isin(scouting_values)]
data = data.loc[data[code].isin(sections[code].unique())]

sections_pd = sections_pd.loc[(sections_pd[code].isin(data[code])) & (sections_pd["lat"] != "error")]

for score_field in score_fields[-1:]:
    print(score_field['field_name'])
    map = CholoplethMapPlotter(MSOA,data,OUTPUT + NAME + "_" + score_field['field_name'] + ".html",'YlOrRd',None,score_field['field_name'])
    map.SCORE_COL = score_field['field_name']
    map.CODE_COL = code

    map.plot()
    section = sections_pd.loc[sections_pd["Type *"].isin(score_field['section_label'])]

    for ii in section.index:
        lat = float(section.at[ii,'lat'])
        long = float(section.at[ii,'long'])
        group = section.at[ii, 'Scout Group']
        name = section.at[ii,'Name']
        type = section.at[ii,'Type *']
        yp = section.at[ii,'YP-2018']
        if type == "C":
            color = 'blue'
        elif type == "P":
            color = 'green'
        elif type == "T":
            color = 'purple'
        elif (type == "U") or (type == "Y"):
            color = 'black'
        map.add_marker(lat, long, group + " | " + name + " | " + type +" | " + "young people:" + str(yp),color)

    map.save()
    map.show()
