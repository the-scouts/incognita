import csv
import pandas as pd
from postcode_to_constituency import PostcodeToArea

ONSPD_POSTCODE_FIELD = 'osward'
output_file = ONSPD_POSTCODE_FIELD + '_data.csv'

names = {'pcon': 'Westminster Parliamentary Constituency names and codes UK as at 12_14.csv',
              'osward': 'Ward names and codes UK as at 05_18.csv',
              'msoa11': 'MSOA (2011) names and codes UK as at 12_12.csv',
              'oslaua': 'LA_UA names and codes UK as at 12_18.csv'}

# Takes postcodes and returns the Westminster Constituencies
ONS_PD = r"pcluts_2018may\pcluts_2018may\ONSPD_MAY_2018_UK.csv"
# Input csv file must have a column called "Postcode"
input_csv = r"Census 2018 Sections Special (4) with ONS fields.csv"

input_pd = pd.read_csv(input_csv,encoding='latin-1')

map_file = 'pcluts_2018may\\pcluts_2018may\\Documents\\' + names.get(ONSPD_POSTCODE_FIELD)

if ONSPD_POSTCODE_FIELD in list(input_pd):
    data_file = input_csv
else:
    if 'Postcode' in list(input_pd):
        print('Constituencies not in file, so generating constituencies from postcodes')
        output_csv = r"Output\Census 2018 Sections Special (4) with pcon.csv"

        fields = [ONSPD_POSTCODE_FIELD]

        mapping = PostcodeToArea(ONS_PD, input_csv, output_csv, fields)
        mapping.SECTIONS = ["C","P","T","U","Y"]
        mapping.CENSUS_TYPE_HEADING = "Type *"
        mapping.CENSUS_TYPE_GROUP = "G"
        mapping.CENSUS_TYPE_DISTRICT = "E"
        mapping.CENSUS_TYPE_ENTITY = [mapping.CENSUS_TYPE_GROUP, mapping.CENSUS_TYPE_DISTRICT]
        mapping.create_output()
        data_file = output_csv
    else:
        print("Error: Invalid input file. Must contain either " + ONSPD_POSTCODE_FIELD + "or 'Postcode'")

section_data = pd.read_csv(data_file,encoding='latin-1')
groups_data = section_data.loc[section_data['Type *'] == "G"]
district_data = section_data.loc[section_data['Type *'] == "E"]

code_map = pd.read_csv(map_file,dtype='str',encoding='latin-1')

output_data = pd.DataFrame(columns=["Name", ONSPD_POSTCODE_FIELD, "Groups", "Beavers", "Cubs", "Scouts", "Explorers", "Waiting List"])
for ii in code_map.index:
    code = code_map.iloc[ii, 0]
    constituency_sections = section_data.loc[section_data[ONSPD_POSTCODE_FIELD] == code]
    constituency_groups = constituency_sections['G_ID'].unique()
    constituency_districts = constituency_sections['D_ID'].unique()

    constituency_group_names = [x.strip() for x in constituency_sections['Scout Group'].unique()]
    if "District" in constituency_group_names:
        constituency_group_names.remove("District")
    group_string = ""
    for group in constituency_group_names:
        group_string += str(group).strip()
        if group != constituency_group_names[-1]:
            group_string += "\n"

    beaver_sections = constituency_sections.loc[constituency_sections['Type *'] == "C"]
    cub_sections = constituency_sections.loc[constituency_sections['Type *'] == "P"]
    scout_sections = constituency_sections.loc[constituency_sections['Type *'] == "T"]
    explorer_sections = constituency_sections.loc[constituency_sections['Type *'] == "U"]
    yl_sections = constituency_sections.loc[constituency_sections['Type *'] == "Y"]
    #network_sections = constituency_sections.loc[constituency_sections['Type *'] == "N"]

    groups = groups_data.loc[groups_data['G_ID'].isin(constituency_groups)]
    explorer_waiting = district_data.loc[district_data['D_ID'].isin(district_data)]
    nu_waiting = groups['W-2018'].sum() + explorer_waiting['W-2018'].sum()

    nu_beavers = beaver_sections['YP-2018'].sum()
    nu_cubs = cub_sections['YP-2018'].sum()
    nu_scouts = scout_sections['YP-2018'].sum()
    nu_explorers = explorer_sections['YP-2018'].sum() + yl_sections['YP-2018'].sum()
    #nu_network = network_sections['YP-2018'].sum()

    #nu_adults = int(group_sections['L-2018'].sum()) + int(group_sections['SA-2018'].sum())
    #nu_young_vols = constituency_sections['YL-2018'].sum()
    constituency_data = pd.DataFrame([[code_map.iloc[ii, 1], code, group_string, nu_beavers, nu_cubs, nu_scouts, nu_explorers, nu_waiting]],columns=["Name", ONSPD_POSTCODE_FIELD, "Groups", "Beavers", "Cubs", "Scouts", "Explorers", "Waiting List"])
    output_data = output_data.append(constituency_data)

output_data.to_csv(output_file)
