import pandas as pd
import numpy as np
from src.map_plotter import ChoroplethMapPlotter
from src.census_data import CensusData
from src.census_merge_data import CensusMergePostcode
import src.log_util as log_util
import folium
import branca
import geopandas as gpd
import shapely
import collections
from itertools import cycle
import json


class ScoutMap:
    """Provides access to manipulate and process data

    :param str census_csv_path: A path to a .csv file that contains Scout Census data

    :var dict ScoutMap.SECTIONS: Holds information about scout sections
    """

    SECTIONS = {
        'Beavers': {'field_name': '%-Beavers', 'ages': [(6, 1), (7, 1)]},
        'Cubs': {'field_name': '%-Cubs', 'ages': [(8, 1), (9, 1), (10, 0.5)]},
        'Scouts': {'field_name': '%-Scouts', 'ages': [(10, 0.5), (11, 1), (12, 1), (13, 1)]},
        'Explorers': {'field_name': '%-Explorers', 'ages': [(14, 1), (15, 1), (16, 1), (17, 1)]}
    }

    def __init__(self, census_csv_path):

        # Loads Scout Census Data
        self.census_data = CensusData(census_csv_path)

        # Set by ScriptHandler as 'parent'
        self.ons_data = None
        self.boundary_report = {}
        self.district_mapping = {}

        self.boundary_dict = None
        self.boundary_regions_data = None

        # Can be set by set_region_of_color
        self.region_of_color = None

        # Load the settings file
        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]

        # Folder to save output files to
        self.OUTPUT = self.settings["Output folder"]

        # Facilitates logging
        self.logger = log_util.create_logger(__name__,)

    def merge_ons_postcode_directory(self, ONS_postcode_directory):
        """Merges CensusData object with ONSPostcodeDirectory object and outputs to csv

        :param ONS_postcode_directory: Refers to the ONS Postcode Directory
        :type ONS_postcode_directory: ONSPostcodeDirectory object
        """
        # Modifies self.census_postcode_data with the ONS fields info, and saves the output
        ons_fields_data_types = {
            'categorical': ['lsoa11', 'msoa11', 'oslaua', 'osward', 'pcon', 'oscty', 'ctry', 'rgn'],
            'int': ['oseast1m', 'osnrth1m', 'lat', 'long', 'imd'],
        }

        self.logger.debug("Initialising merge object")
        merge = CensusMergePostcode(
            self.census_data,
            self.census_data.sections_file_path[:-4] + f" with {ONS_postcode_directory.PUBLICATION_DATE} fields.csv", )

        self.logger.info("Cleaning the postcodes")
        merge.clean_and_verify_postcode(self.census_data.data, CensusData.column_labels['POSTCODE'])

        self.logger.info("Adding ONS postcode directory data to Census and outputting")

        # initially merge just Country column to test what postcodes can match
        self.census_data.data = merge.merge_data(
            self.census_data.data,
            ONS_postcode_directory.data['ctry'],
            "clean_postcode", )

        # attempt to fix invalid postcodes
        self.census_data.data = merge.try_fix_invalid_postcodes(
            self.census_data.data,
            ONS_postcode_directory.data['ctry'], )

        # fully merge the data
        self.census_data.data = merge.merge_data(
            self.census_data.data,
            ONS_postcode_directory.data,
            "clean_postcode", )

        # fill unmerged rows with default values
        self.logger.info("filling unmerged rows")
        self.census_data.data = merge.fill_unmerged_rows(
            self.census_data.data,
            CensusData.column_labels['VALID_POSTCODE'],
            ons_fields_data_types, )

        # save the data to CSV and save invalid postcodes to an error file
        merge.output_data(
            self.census_data.data,
            "clean_postcode", )

    def has_ons_data(self):
        """Finds whether ONS data has been added

        :returns: Whether the Scout Census data has ONS data added
        :rtype: bool
        """
        return self.census_data.has_ons_data()

    def filter_records(self, field, value_list, mask=False, exclusion_analysis=False):
        """Filters the Census records by any field in ONS PD.

        :param str field: The field on which to filter
        :param list value_list: The values on which to filter
        :param bool mask: If True, keep the values that match the filter. If False, keep the values that don't match the filter.
        :param bool exclusion_analysis:

        :returns None: Nothing
        """
        # Count number of rows
        original_records = len(self.census_data.data.index)

        # Filter records
        if not mask:
            self.logger.info(f"Selecting records that satisfy {field} in {value_list} from {original_records} records.")
            if exclusion_analysis:
                excluded_data = self.census_data.data.loc[~self.census_data.data[field].isin(value_list)]
            self.census_data.data = self.census_data.data.loc[self.census_data.data[field].isin(value_list)]
        else:
            self.logger.info(f"Selecting records that satisfy {field} not in {value_list} from {original_records} records.")
            if exclusion_analysis:
                excluded_data = self.census_data.data.loc[self.census_data.data[field].isin(value_list)]
            self.census_data.data = self.census_data.data.loc[~self.census_data.data[field].isin(value_list)]

        remaining_records = len(self.census_data.data.index)
        self.logger.info(f"Resulting in {remaining_records} records remaining.")

        if exclusion_analysis:
            # Calculate the number of records that have been filtered out
            excluded_records = original_records - remaining_records
            self.logger.info(f"{excluded_records} records were removed ({excluded_records / original_records * 100}% of total)")

            # Prints number of members and % of members filtered out for each section
            for section in CensusData.column_labels['sections'].keys():
                self.logger.debug(f"Analysis of {section} member exclusions")
                section_type = CensusData.column_labels['sections'][section]["type"]
                section_dict = CensusData.column_labels['sections'][section]

                excluded_sections = excluded_data.loc[excluded_data[CensusData.column_labels['UNIT_TYPE']] == section_type]
                self.logger.debug(f"Excluded sections\n{excluded_sections}")
                self.logger.debug(f"Finding number of excluded {section} by summing {section_dict['male']} and {section_dict['female']}")
                excluded_members = excluded_sections[section_dict["male"]].sum() + excluded_sections[section_dict["female"]].sum()
                self.logger.debug(f"{excluded_members} {section} excluded")

                sections = self.census_data.data.loc[self.census_data.data[CensusData.column_labels['UNIT_TYPE']] == section_type]
                counted_members = sections[section_dict["male"]].sum() + sections[section_dict["female"]].sum()

                original_members = counted_members + excluded_members

                if original_members > 0:
                    self.logger.info(f"{excluded_members} {section} members were removed ({excluded_members / original_members * 100}%) of total")
                else:
                    self.logger.info(f"There are no {section} members present in data")

    def set_boundary(self, geography_name):
        """Sets the boundary_dict and boundary_regions_data members

        :param str geography_name: The type of boundary, e.g. lsoa11, pcon etc. Must be a key in ONSPostcodeDirectory.BOUNDARIES.

        :var dict self.boundary_dict: information about the boundary type
        :var self.boundary_regions_data: table of region codes and human-readable names for those codes

        :returns None: Nothing
        """
        self.logger.info(f"Setting the boundary to {geography_name}")

        if geography_name in self.ons_data.BOUNDARIES.keys():
            self.boundary_dict = self.ons_data.BOUNDARIES[geography_name]
            names_and_codes_file_path = self.boundary_dict["codes"].get("path")
            self.boundary_regions_data = pd.read_csv(self.ons_data.NAMES_AND_CODES_FILE_LOCATION + names_and_codes_file_path,
                                                     dtype={
                                                        self.boundary_dict["codes"]["key"]: self.boundary_dict["codes"]["key_type"],
                                                        self.boundary_dict["codes"]["name"]: "object"
                                                        })
        elif geography_name in self.settings["Scout Mappings"].keys():
            self.boundary_dict = self.settings["Scout Mappings"][geography_name]
            names_and_codes_file_path = self.boundary_dict["codes"].get("path")
            self.boundary_regions_data = pd.read_csv(names_and_codes_file_path,
                                                     dtype={
                                                        self.boundary_dict["codes"]["key"]: self.boundary_dict["codes"]["key_type"],
                                                        self.boundary_dict["codes"]["name"]: "object"
                                                        })
        else:
            raise Exception(f"{geography_name} is an invalid boundary.\nValid boundaries include: {self.ons_data.BOUNDARIES.keys() + self.settings['Scout Mapping'].keys()}")

    def filter_boundaries(self, field, value_list):
        """Filters the boundary_regions_data table by if the area code is within both value_list and the census_data table.

        Requires set_boundary to have been called.
        Uses ONS Postcode Directory to find which of set boundaries are within
        the area defined by the value_list.

        :param str field: The field on which to filter
        :param list value_list: The values on which to filter

        :returns None: Nothing
        """

        if not self.boundary_dict:
            raise Exception("boundary_dict has not been set, or there is no data in it") # Has ScoutMap.set_boundary() been called?

        name = self.boundary_dict["name"]
        codes_key = self.boundary_dict["codes"]["key"]

        self.logger.info(f"Filtering {len(self.boundary_regions_data.index)} {name} boundaries by {field} being in {value_list}")
        # Filters ons data table if field column is in value_list. Returns ndarray of unique area codes
        boundary_subset = self.ons_data.ons_field_mapping(field, value_list, name)
        self.logger.debug(f"This corresponds to {len(boundary_subset)} {name} boundaries")

        # Filters the boundary names and codes table by areas within the boundary_subset list
        self.boundary_regions_data = self.boundary_regions_data.loc[self.boundary_regions_data[codes_key].isin(boundary_subset)]
        self.logger.info(f"Resulting in {len(self.boundary_regions_data.index)} {name} boundaries")

    def ons_from_scout_area(self, ons_code, column, value_list):
        """Produces list of ONS Geographical codes that exist within a subset
        of the Scout Census data.

        :param ons_code: A field of the ONS Postcode Directory
        :param column: A field of the Scout Census data
        :param value_list: Values to accept

        :type ons_code: str
        :type column: str
        :type value_list: list

        :returns: List of ONS Geographical codes of type ons_code.
        :rtype: list
        """
        self.logger.debug(f"Finding the ons areas that exist with {column} in {value_list}")
        records = self.census_data.data.loc[self.census_data.data[column].isin(value_list)]
        self.logger.debug(f"Found {len(records.index)} records that match {column} in {value_list}")
        ons_codes = records[ons_code].unique()
        self.logger.debug(f"Found raw {len(ons_codes)} {ons_code}s that match {column} in {value_list}")
        if CensusData.DEFAULT_VALUE in ons_codes:
            ons_codes.remove(CensusData.DEFAULT_VALUE)
        ons_codes = [code for code in ons_codes if (isinstance(code, str) or (isinstance(code, np.int32) and not np.isnan(code)))]
        self.logger.debug(f"Found clean {len(ons_codes)} {ons_code}s that match {column} in {value_list}")
        return ons_codes

    def districts_from_ons(self, ons_code, ons_codes):
        """Produces list of districts that exist within boundary defined by
        ons_codes

        :param ons_code: A field of the ONS Postcode Directory
        :param ons_codes: Values to filter the records on

        :type ons_code: str
        :type ons_codes: list

        :returns: List of District IDs
        :rtype: list
        """
        oslaua_records = self.census_data.data.loc[self.census_data.data[ons_code].isin(ons_codes)]
        district_ids = oslaua_records[CensusData.column_labels['id']["DISTRICT"]].unique()
        district_ids = [str(district_id) for district_id in district_ids]
        if "nan" in district_ids:
            district_ids.remove("nan")
        return district_ids

    def ons_to_district_mapping(self, ons_code):
        """Create json file, containing which scout districts are within an each ONS area, and how many ONS areas those districts are in.

        :param ons_code: A field in the modified census report corresponding to an administrative region (lsoa11, msoa11, oslaua, osward, pcon, oscty, ctry, rgn)
        :type ons_code: str

        :returns: Nothing
        :rtype: None
        """

        self.logger.debug("Creating mapping from ons boundary to scout district")
        codes_key = self.boundary_dict["codes"]["key"]

        region_type = ons_code  # Census column heading for the region geography type
        district_id_column = CensusData.column_labels['id']["DISTRICT"]

        region_ids = self.boundary_regions_data[codes_key].dropna().drop_duplicates()

        district_ids_by_region = self.census_data.data.loc[self.census_data.data[region_type].isin(region_ids), [region_type, district_id_column,]].dropna().drop_duplicates()
        district_ids = district_ids_by_region[district_id_column].dropna().drop_duplicates()

        region_ids_by_district = self.census_data.data.loc[self.census_data.data[district_id_column].isin(district_ids), [district_id_column, region_type]]
        region_ids_by_district = region_ids_by_district.loc[~(region_ids_by_district[region_type] == CensusData.DEFAULT_VALUE)].dropna().drop_duplicates()

        count_regions_in_district = region_ids_by_district.groupby(district_id_column).count().rename(columns={region_type: "count"})  # count of how many regions the district occupies
        count_by_district_by_region = pd.merge(left=district_ids_by_region, right=count_regions_in_district, on=district_id_column)

        count_by_district_by_region = count_by_district_by_region.set_index([region_type, district_id_column])

        nested_dict = collections.defaultdict(dict)
        for keys, value in count_by_district_by_region["count"].iteritems():
            nested_dict[keys[0]][keys[1]] = value
        mapping = dict(nested_dict)

        self.district_mapping[ons_code] = mapping
        self.logger.debug("Finished mapping from ons boundary to district")
        # with open("district_mapping.json", 'w') as f:
        #     json.dump(mapping, f)

    # def load_ons_to_district_mapping(self, file_name, ons_code):
    #     """Reads a district mapping file (e.g. as created by ons_to_district_mapping)
    #
    #     :param file_name: Location of the json file
    #     :param ons_code: The ONS field that the file contains
    #
    #     :type file_name: str
    #     :type ons_code: str
    #
    #     :returns: Nothing
    #     :rtype: None
    #     """
    #     with open(file_name, 'r') as f:
    #         self.district_mapping[ons_code] = json.load(f)

    def create_boundary_report(self, options=["Groups", "Section numbers", "6 to 17 numbers", "awards", "waiting list total"], historical=False):
        """Produces .csv file summarising by boundary provided.

        Requires self.boundary_data to be set, preferably by :meth:scout_map.set_boundary

        :param options: List of data to be included in report
        :param historical: Check to ensure that multiple years of data are intentional

        :type options: list
        :type historical: bool

        :returns: Nothing
        :rtype: None
        """
        if isinstance(options, str):
            options = [options]

        name = self.boundary_dict.get("name")  # e.g oslaua osward pcon
        if not name:
            raise Exception("Function set_boundary must be run before a boundary report can be created")
        self.logger.info(f"Creating report by {name} with {', '.join(options)} from {len(self.census_data.data.index)} records")

        min_year, max_year = ScoutMap.years_of_return(self.census_data.data)
        years_in_data = range(min_year, max_year + 1)

        #years_in_data = self.census_data.data[CensusData.column_labels['YEAR']].unique().tolist()
        #years_in_data = [int(year) for year in years_in_data]
        #years_in_data.sort()
        #years_in_data = [str(year) for year in years_in_data]
        if historical:
            self.logger.info(f"Historical analysis including {years_in_data}")
        else:
            if len(years_in_data) > 1:
                self.logger.error(f"Historical option not selected, but multiple years of data selected ({years_in_data})")

        output_columns = ["Name", self.boundary_dict["name"]]

        if "Groups" in options:
            output_columns.append("Groups")
        if "Section numbers" in options:
            for year in years_in_data:
                output_columns += [f"Beavers-{year}", f"Cubs-{year}", f"Scouts-{year}", f"Explorers-{year}"]
                if "6 to 17 numbers" in options:
                    output_columns.append(f"All-{year}")
        if ("6 to 17 numbers" in options) and not ("Section numbers" in options):
            for year in years_in_data:
                output_columns.append(f"All-{year}")
        if "awards" in options:
            output_columns.append("%-" + CensusData.column_labels['sections']["Beavers"]["top_award"])
            output_columns.append("QSA")
            output_columns.append("%-QSA")
            awards_mapping = self.district_mapping.get(name)
            if not awards_mapping:
                if name in self.ons_data.BOUNDARIES.keys():
                    self.ons_to_district_mapping(name)
                    awards_mapping = self.district_mapping.get(name)
        if "waiting list total" in options:
            for year in years_in_data:
                output_columns.append(f"Waiting List-{year}")

        output_data = pd.DataFrame(columns=output_columns)
        self.logger.debug(f"Report contains the following data:\n{output_columns}")

        district_id_column = CensusData.column_labels['id']["DISTRICT"]
        for ii in range(len(self.boundary_regions_data.index)):
            self.logger.debug(f"{ii+1} out of {len(self.boundary_regions_data.index)}")
            boundary_data = {
                "Name": self.boundary_regions_data.iloc[ii, 1],
                name: self.boundary_regions_data.iloc[ii, 0]}
            code = boundary_data[name]  # == self.boundary_regions_data.iloc[ii, 0]

            records_in_boundary = self.census_data.data.loc[self.census_data.data[name] == code]
            self.logger.debug(f"Found {len(records_in_boundary.index)} records with {name} == {code}")

            # list_of_groups = records_in_boundary[CensusData.column_labels['id']["GROUP"]].unique()
            # list_of_districts = records_in_boundary[CensusData.column_labels['id']["DISTRICT"]].unique()

            if "Groups" in options:
                # Used to list the groups that operate within the boundary
                group_names_in_boundary = [str(x).strip() for x in records_in_boundary[CensusData.column_labels['name']["GROUP"]].unique()]
                if "nan" in group_names_in_boundary:
                    group_names_in_boundary.remove("nan")
                group_string = ""
                for group in group_names_in_boundary:
                    group_string += str(group).strip()
                    if group != group_names_in_boundary[-1]:
                        group_string += "\n"
                boundary_data["Groups"] = group_string

            if ("Section numbers" in options) or ("6 to 17 numbers" in options) or ("waiting list total" in options):
                self.logger.debug(f"Obtaining Section numbers and waiting list for {year}")
                for year in years_in_data:
                    year_records = records_in_boundary.loc[records_in_boundary[CensusData.column_labels['YEAR']] == year]
                    # beaver_sections = year_records.loc[year_records[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections']["Beavers"]]
                    # cub_sections = year_records.loc[year_records[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections']["Cubs"]]
                    # scout_sections = year_records.loc[year_records[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections']["Scouts"]]
                    # explorer_sections = year_records.loc[year_records[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections']["Explorers"]]
                    #
                    # group_records = year_records.loc[year_records[CensusData.column_labels['UNIT_TYPE']] == self.census_data.CENSUS_TYPE_GROUP]
                    # explorer_waiting = year_records.loc[year_records[CensusData.column_labels['UNIT_TYPE']] == self.census_data.CENSUS_TYPE_DISTRICT]
                    boundary_data[f"Waiting List-{year}"] = 0
                    for section in [section for section in CensusData.column_labels['sections'].keys() if CensusData.column_labels['sections'][section].get("waiting_list")]:
                        boundary_data[f"Waiting List-{year}"] += year_records[CensusData.column_labels['sections'][section]["waiting_list"]].sum()

                    boundary_data[f"All-{year}"] = 0
                    for section in CensusData.column_labels['sections'].keys():
                        # sections = year_records.loc[year_records[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections'][section]["type"]]
                        boundary_data[f"{section}-{year}"] = year_records[CensusData.column_labels['sections'][section]["male"]].sum() + year_records[CensusData.column_labels['sections'][section]["female"]].sum()
                        boundary_data[f"All-{year}"] += boundary_data[f"{section}-{year}"]

            if "awards" in options:
                eligible = records_in_boundary[CensusData.column_labels['sections']["Beavers"]["top_award_eligible"]].sum()
                awards = records_in_boundary[CensusData.column_labels['sections']["Beavers"]["top_award"]].sum()
                if eligible > 0:
                    boundary_data["%-" + CensusData.column_labels['sections']["Beavers"]["top_award"]] = (awards * 100) / eligible
                else:
                    boundary_data["%-" + CensusData.column_labels['sections']["Beavers"]["top_award"]] = np.NaN

                if name == "D_ID":
                    districts = {code: 1}
                else:
                    districts = awards_mapping[code]  # self.district_mapping.get(name)[code] == self.district_mapping.get(name)[boundary_data[name]]
                    #                                   self.district_mapping[ons_name][region][district_id]

                boundary_data["QSA"] = 0
                qsa_eligible = 0

                # calculates the nominal QSAs per ONS region specified.
                # Divides total # of awards by the number of Scout Districts that the ONS Region is in
                for district_id in districts.keys():  # district_id within ONS region
                    number_of_ons_regions_district_is_in = districts[district_id]
                    self.logger.debug(f"{district_id} in {number_of_ons_regions_district_is_in} ons boundaries")

                    district_records = self.census_data.data.loc[self.census_data.data[district_id_column] == district_id]  # Records for current district ID

                    QSA_achieved_in_district_divided_by_number_of_regions_district_is_in = district_records["Queens_Scout_Awards"].sum() / number_of_ons_regions_district_is_in
                    boundary_data["QSA"] += QSA_achieved_in_district_divided_by_number_of_regions_district_is_in

                    YP_eligible_for_QSA_in_district_divided_by_number_of_regions_district_is_in = district_records["Eligible4QSA"].sum() / number_of_ons_regions_district_is_in
                    qsa_eligible += YP_eligible_for_QSA_in_district_divided_by_number_of_regions_district_is_in

                if qsa_eligible > 0:
                    boundary_data["%-QSA"] = (boundary_data["QSA"] * 100) / qsa_eligible
                else:
                    boundary_data["%-QSA"] = np.NaN

            self.logger.debug(f"Adding data from {code}\n{boundary_data}")
            boundary_data_df = pd.DataFrame([boundary_data], columns=output_columns)
            output_data = pd.concat([output_data, boundary_data_df], axis=0, sort=False)

        if "awards" in options:
            max_value = output_data["%-" + CensusData.column_labels['sections']["Beavers"]["top_award"]].quantile(0.95)
            output_data["%-" + CensusData.column_labels['sections']["Beavers"]["top_award"]].clip(upper=max_value, inplace=True)

        if name == "lsoa11":
            self.logger.debug(f"Output_data so far:\n{output_data}")
            data_to_merge = self.ons_data.data[["lsoa11", "imd"]].drop_duplicates("lsoa11")
            self.logger.debug(f"Merging with\n{data_to_merge}")
            output_data = pd.merge(left=output_data, right=data_to_merge , how="left", on="lsoa11", validate="1:1")
            output_data = self.country_add_IMD_decile(output_data, "E92000001")

        output_data.reset_index(drop=True, inplace=True)
        self.boundary_report[self.boundary_dict["name"]] = output_data
        return output_data

    def load_boundary_report(self, boundary_report_csv_path):
        """Load a boundary report created with the :meth:scout_map.create_boundary_report

        :returns: Nothing
        :rtype: None
        """
        self.boundary_report[self.boundary_dict["name"]] = pd.read_csv(f"{self.settings['Output folder']}{boundary_report_csv_path}.csv")

    def create_uptake_report(self):
        """Creates an report by the boundary that has been set, requires
        a boundary report to already have been run.
        Requires population data by age for the specified boundary.

        :returns: Uptake data of Scouts in the boundary
        :rtype: pandas.DataFrame
        """
        boundary = self.boundary_dict["name"]
        boundary_report = self.boundary_report.get(self.boundary_dict["name"], "Boundary report doesn't exist")

        if isinstance(boundary_report, str):
            self.create_boundary_report(boundary)
            boundary_report = self.boundary_report[self.boundary_dict["name"]]

        age_profile_path = self.boundary_dict.get("age_profile").get("path")
        if age_profile_path:
            data_types = {str(key): "Int16" for key in range(5,26)}
            age_profile_pd = pd.read_csv(self.settings["National Statistical folder"] + age_profile_path, dtype=data_types)
        else:
            raise Exception(f"Population by age data not present for this {boundary}")

        min_year, max_year = ScoutMap.years_of_return(self.census_data.data)
        years_in_data = range(min_year, max_year + 1)

        start_default_val = np.NaN
        empty_val = np.NaN

        for section in ScoutMap.SECTIONS.keys():
            boundary_report[f'Pop_{section}'] = start_default_val
        boundary_report['Pop_All'] = start_default_val

        for year in years_in_data:
            for section in ScoutMap.SECTIONS.keys():
                boundary_report[f'%-{section}-{year}'] = start_default_val
            boundary_report[f'%-All-{year}'] = start_default_val

        for area_row in range(len(boundary_report.index)):
            boundary_row = boundary_report.iloc[area_row]

            area_code = boundary_row.at[boundary]
            area_pop = age_profile_pd.loc[age_profile_pd[self.boundary_dict["age_profile"]["key"]] == area_code]

            if not area_pop.empty:
                for section in ScoutMap.SECTIONS.keys():
                    section_total = 0
                    for age in ScoutMap.SECTIONS[section]["ages"]:
                        section_total += area_pop.iloc[0][str(age[0])] * age[1]
                    boundary_row.at[f'Pop_{section}'] = section_total
                    for year in years_in_data:
                        if section_total > 0:
                            boundary_row.at[f'%-{section}-{year}'] = (boundary_row.at[f"{section}-{year}"] / section_total) * 100
                        else:
                            if boundary_row.at[f'{section}-{year}'] == 0:
                                # No Scouts and no eligible population in the geographic area
                                boundary_row.at[f'%-{section}-{year}'] = empty_val
                            else:
                                # There are Scouts but no eligible population in the geographic area
                                boundary_row.at[f'%-{section}-{year}'] = 100

                section_total = 0
                for age in range(6, 18):
                    section_total += area_pop.iloc[0][str(age)]
                boundary_row.at['Pop_All'] = section_total
                for year in years_in_data:
                    if section_total > 0:
                        boundary_row.at[f'%-All-{year}'] = (boundary_row.at[f"All-{year}"] / section_total) * 100
                    else:
                        if boundary_row.at[f'%-All-{year}'] == 0:
                            # No Scouts and no eligible population in the geographic area
                            boundary_row.at[f'%-All-{year}'] = empty_val
                        else:
                            # There are Scouts but no eligible population in the geographic area
                            boundary_row.at[f'%-All-{year}'] = 100

            else:
                for section in ScoutMap.SECTIONS.keys():
                    boundary_row.at[f"%-{section}"] = empty_val
                boundary_row.at[f'%-All-{section}'] = empty_val

            boundary_report.iloc[area_row] = boundary_row

        for section in ScoutMap.SECTIONS.keys():
            for year in years_in_data:
                col_name = f"%-{section}-{year}"
                max_value = boundary_report[col_name].quantile(0.975)
                boundary_report[col_name].clip(upper=max_value, inplace=True)
        max_value = boundary_report[f"%-All-{year}"].quantile(0.975)
        boundary_report[f"%-All-{year}"].clip(upper=max_value, inplace=True)

        return boundary_report

    def create_section_maps(self, output_file_name, static_scale, value_type="Percentages", cluster_markers=False):
        min_year, max_year = ScoutMap.years_of_return(self.census_data.data)
        if min_year != max_year:
            self.logger.warning(f"Only using latest year {max_year} to create map")

        for section_label in ScoutMap.SECTIONS.keys():
            section = ScoutMap.SECTIONS[section_label]
            if value_type == "Numbers":
                self.create_map(f"{section_label}-{max_year}", section_label, output_file_name + "_" + section_label, f"Number of {section_label} in {max_year}", static_scale, cluster_markers)
            elif value_type == "Percentages":
                self.create_map(f"%-{section_label}-{max_year}", section_label, output_file_name + "_" + section_label, f"% uptake of {section_label} in {max_year}", static_scale, cluster_markers)
            self.add_single_section_to_map(section_label, self.district_color_mapping(), ["youth membership"])
            self.save_map()

    def create_6_to_17_map(self, output_file_name, static_scale, value_type="Percentages"):
        min_year, max_year = ScoutMap.years_of_return(self.census_data.data)
        if min_year != max_year:
            self.logger.warning(f"Only using latest year {max_year} to create map")

        if value_type == "Percentages":
            self.create_map(f"%-All-{max_year}", "% 6-17 Uptake", output_file_name, "% 6-17 Uptake", static_scale)
        elif value_type == "Numbers":
            self.create_map(f"All-{max_year}", "Under 18s", output_file_name, "Number of Scouts aged 6 to 17", static_scale)

        self.add_all_sections_to_map(self.district_color_mapping(), ["youth membership"])
        self.save_map()

    def district_color_mapping(self):
        colors = cycle(['cadetblue', 'lightblue', 'blue', 'beige', 'red', 'darkgreen', 'lightgreen', 'purple', 'lightgrayblack',
                'orange', 'pink', 'white', 'darkblue', 'darkpurple', 'darkred', 'green', 'lightred'])
        district_ids = self.census_data.data[CensusData.column_labels['id']["DISTRICT"]].unique()
        mapping = {}
        for district_id in district_ids:
            mapping[district_id] = next(colors)
        colour_mapping = {"census_column": CensusData.column_labels['id']["DISTRICT"], "mapping": mapping}
        return colour_mapping

    def create_map(self, score_col, display_score_col, name, legend_label, static_scale=None, cluster_markers=False):
        self.logger.info(f"Creating map from {score_col} with name {name}")

        data_codes = {
            "data": self.boundary_report[self.boundary_dict["name"]],
            "code_col": self.boundary_dict["name"],
            "score_col": score_col,
            "score_col_label": display_score_col
        }

        if not (score_col in list(data_codes["data"].columns)):
            raise Exception(f"The column {score_col} does not exist in data.\nValid columns are {list(data_codes['data'].columns)}")

        self.map = ChoroplethMapPlotter(self.boundary_dict["boundary"],
                                        data_codes,
                                        self.settings["Output folder"] + name,
                                        cluster_markers)

        non_zero_score_col = data_codes["data"][score_col].loc[data_codes["data"][score_col] != 0]
        non_zero_score_col.dropna(inplace=True)
        min_value = data_codes["data"][score_col].min()
        max_value = data_codes["data"][score_col].max()
        self.logger.info(f"Minimum data value: {min_value}. Maximum data value: {max_value}")
        colormap = branca.colormap.LinearColormap(colors=['#ca0020', '#f4a582', '#92c5de', '#0571b0'],
                                                  index=non_zero_score_col.quantile([0, 0.25, 0.75, 1]),
                                                  vmin=min_value,
                                                  vmax=max_value)
        non_zero_score_col.sort_values(axis=0, inplace=True)
        colormap = colormap.to_step(data=non_zero_score_col, quantiles=[0, 0.2, 0.4, 0.6, 0.8, 1])
        self.logger.info(f"Colour scale boundary values\n{non_zero_score_col.quantile([0, 0.2, 0.4, 0.6, 0.8, 1])}")
        colormap.caption = legend_label
        self.map.plot(legend_label, show=True, boundary_name=self.boundary_dict["boundary"]["name"], colormap=colormap)

        if static_scale:
            colormap_static = branca.colormap.LinearColormap(colors=['#ca0020', '#f7f7f7', '#0571b0'],
                                                             index=static_scale["index"],
                                                             vmin=static_scale["min"],
                                                             vmax=static_scale["max"])\
                .to_step(index=static_scale["boundaries"])
            colormap_static.caption = legend_label + " (static)"
            self.map.plot(legend_label + " (static)", show=False, boundary_name=self.boundary_dict["boundary"]["name"], colormap=colormap_static)

    def add_all_sections_to_map(self, colour, marker_data):
        """Adds sections from latest year of data as markers on map

        Plots all Beaver Colonies, Cub Packs, Scout Troops and Explorer Units,
        who have returned in the latest year of the dataset.

        :param str/dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        """
        min_year, max_year = self.years_of_return(self.census_data.data)
        latest_year_records = self.census_data.data.loc[self.census_data.data["Year"] == max_year]
        self.add_sections_to_map(latest_year_records.loc[latest_year_records[CensusData.column_labels['UNIT_TYPE']].isin(self.census_data.get_section_type([CensusData.UNIT_LEVEL_GROUP, CensusData.UNIT_LEVEL_DISTRICT]))], colour, marker_data)

    def add_single_section_to_map(self, section, colour, marker_data):
        """Plots the section specified by section onto the map, in markers of
        colour identified by colour, with data indicated by marker_data.

        :param str section: One of Beavers, Cubs, Scouts, Explorers, Network
        :param str/dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        """
        self.add_sections_to_map(self.census_data.data.loc[self.census_data.data[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections'][section]["type"]], colour, marker_data)

    def add_sections_to_map(self, sections, colour, marker_data):
        """Adds the sections provided as markers to map with the colour, and data
        indicated by marker_data.

        :param DataFrame sections: Census records relating to Sections with lat and long Columns
        :param str/dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        """
        self.logger.info("Adding section markers to map")

        valid_points = self.census_data.data.loc[self.census_data.data[CensusData.column_labels['VALID_POSTCODE']] == 1]

        # Sets the map so it opens in the right area
        self.map.set_bounds([[valid_points["lat"].min(), valid_points["long"].min()],
                              [valid_points["lat"].max(), valid_points["long"].max()]])

        postcodes = sections[CensusData.column_labels['POSTCODE']].unique()
        postcodes = [str(postcode) for postcode in postcodes]
        if "nan" in postcodes:
            postcodes.remove("nan")

        increment = len(postcodes) / 100
        count = 1
        old_percentage = 0
        for postcode in postcodes:
            new_percentage = round(count / increment)
            if new_percentage > old_percentage:
                self.logger.info(f"% of sections added to map {new_percentage}")
                old_percentage = new_percentage
            count += 1

            self.logger.debug(postcode)
            # Find all the sections with the same postcode
            colocated_sections = sections.loc[sections[CensusData.column_labels['POSTCODE']] == postcode]
            colocated_district_sections = colocated_sections.loc[colocated_sections[CensusData.column_labels['UNIT_TYPE']].isin(self.census_data.get_section_type('District'))]
            colocated_group_sections = colocated_sections.loc[colocated_sections[CensusData.column_labels['UNIT_TYPE']].isin(self.census_data.get_section_type('Group'))]

            lat = float(colocated_sections.iloc[0]['lat'])
            long = float(colocated_sections.iloc[0]['long'])

            # Construct the html to form the marker popup
            # District sections first followed by Group sections
            html = ""

            districts = colocated_district_sections[CensusData.column_labels['id']["DISTRICT"]].unique()
            for district in districts:
                district_name = colocated_district_sections.iloc[0][CensusData.column_labels['name']["DISTRICT"]] + " District"
                html += (f"<h3 align=\"center\">{district_name}</h3><p align=\"center\">"
                         f"<br>")
                colocated_in_district = colocated_district_sections.loc[colocated_district_sections[CensusData.column_labels['id']["DISTRICT"]] == district]
                for section_id in colocated_in_district.index:
                    type = colocated_in_district.at[section_id, CensusData.column_labels['UNIT_TYPE']]
                    name = colocated_in_district.at[section_id, 'name']
                    html += f"{name} : "
                    section = self.section_from_type(type)
                    if "youth membership" in marker_data:
                        male_yp = int(colocated_in_district.at[section_id, CensusData.column_labels['sections'][section]["male"]])
                        female_yp = int(colocated_in_district.at[section_id, CensusData.column_labels['sections'][section]["female"]])
                        yp = male_yp + female_yp
                        html += f"{yp} {section}<br>"
                html += "</p>"

            groups = colocated_group_sections[CensusData.column_labels['id']["GROUP"]].unique()
            self.logger.debug(groups)
            for group in groups:
                colocated_in_group = colocated_sections.loc[colocated_sections[CensusData.column_labels['id']["GROUP"]] == group]
                group_name = colocated_in_group.iloc[0][CensusData.column_labels['name']["GROUP"]] + " Group"

                html += (f"<h3 align=\"center\">{group_name}</h3><p align=\"center\">"
                         f"<br>")
                for section_id in colocated_in_group.index:
                    type = colocated_in_group.at[section_id, CensusData.column_labels['UNIT_TYPE']]
                    name = colocated_in_group.at[section_id, 'name']
                    section = self.section_from_type(type)
                    district_id = colocated_in_group.at[section_id, CensusData.column_labels['id']["DISTRICT"]]

                    html += f"{name} : "
                    if "youth membership" in marker_data:
                        male_yp = int(colocated_in_group.at[section_id, CensusData.column_labels['sections'][section]["male"]])
                        female_yp = int(colocated_in_group.at[section_id, CensusData.column_labels['sections'][section]["female"]])
                        yp = male_yp + female_yp
                        html += f"{yp} {section}<br>"
                    if "awards" in marker_data:
                        awards = int(colocated_in_group.at[section_id, CensusData.column_labels['sections'][section]["top_award"]])
                        eligible = int(colocated_in_group.at[section_id, CensusData.column_labels['sections'][section]["top_award_eligible"]])
                        if section == "Beavers":
                            html += f"{awards} Bronze Awards of {eligible} eligible<br>"

                html += "</p>"

            # Fixes physical size of popup
            if len(groups) == 1:
                height = 120
            else:
                height = 240
            iframe = folium.IFrame(html=html, width=350, height=100)
            popup = folium.Popup(iframe, max_width=2650)

            if isinstance(colour, dict):
                census_column = colour["census_column"]
                colour_mapping = colour["mapping"]
                value = colocated_sections.iloc[0][census_column]
                marker_colour = colour_mapping[value]
            else:
                marker_colour = colour

            # Areas outside the region_of_color have markers coloured grey
            if self.region_of_color:
                if colocated_sections.iloc[0][self.region_of_color["column"]] not in self.region_of_color["value_list"]:
                    marker_colour = 'gray'

            self.logger.debug(f"Placing {marker_colour} marker at {lat},{long}")
            self.map.add_marker(lat, long, popup, marker_colour)

    @staticmethod
    def section_from_type(type):
        for section in CensusData.column_labels['sections'].keys():
            if type == CensusData.column_labels['sections'][section]["type"]:
                return section

    def filter_set_boundaries_in_scout_area(self, column, value_list):
        records_in_scout_area = self.census_data.data.loc[self.census_data.data[column].isin(value_list)]
        boundaries_in_scout_area = records_in_scout_area[self.boundary_dict["name"]].unique()
        self.boundary_regions_data = self.boundary_regions_data.loc[self.boundary_regions_data[self.boundary_dict["codes"]["key"]].isin(boundaries_in_scout_area)]

    def filter_boundaries_by_scout_area(self, boundary, column, value_list):
        """Filters the boundaries, to include only those boundaries which have
        Sections that satisfy the requirement that the column is in the value_list.

        :param str boundary: ONS boundary to filter on
        :param str column: Scout boundary (e.g. C_ID)
        :param list value_list: List of values in the Scout boundary
        """
        ons_value_list = self.ons_from_scout_area(boundary, column, value_list)
        self.filter_boundaries(boundary, ons_value_list)

    def filter_records_by_boundary(self):
        """Selects the records that are with the boundary specified"""
        self.filter_records(self.boundary_dict["name"], self.boundary_regions_data[self.boundary_dict["codes"]["key"]])

    def set_region_of_color(self, column, value_list):
        self.region_of_color = {"column": column, "value_list": value_list}

    def save_map(self):
        self.map.save()

    def show_map(self):
        self.map.show()

    def group_history_summary(self, years):
        self.logger.info("Beginning group_history_summary")
        return self.history_summary(years, "Group ID", CensusData.column_labels['id']["GROUP"])

    def section_history_summary(self, years):
        # Works effectively for years after 2017
        self.logger.info("Beginning section_history_summary")
        return self.history_summary(years, "compass ID", "compass")

    def history_summary(self, years, id_name, census_col):
        # Must have imd scores and deciles already in census_postcode_data.
        section_numbers = []
        for year in years:
            for section in CensusData.column_labels['sections'].keys():
                if section != "Explorers":
                    section_numbers.append(section + "-" + year)
            section_numbers.append("Adults-" + year)

        output_columns = [id_name, "Type", "Group", "District", "County", "Region", "Scout Country", "Postcode", "IMD Country", "IMD Rank", "IMD Decile", "First Year", "Last Year"] + section_numbers
        output_data = pd.DataFrame(columns=output_columns)
        # find the list groups, by applying unique to group_id col
        group_list = self.census_data.data[census_col].unique()
        self.census_data.data["imd"] = pd.to_numeric(self.census_data.data["imd"], errors='coerce')
        group_list = [group for group in group_list if str(group) != "nan"]

        self.logger.info(f"Producing summary of {len(group_list)}")

        increment = len(group_list) / 100
        old_percentage = 0
        for index, group in enumerate(group_list):
            new_percentage = index // increment
            if new_percentage > old_percentage:
                self.logger.info("% completion = " + str(index // increment))
                old_percentage = new_percentage
            self.logger.debug(group)
            group_data = {}
            # find records in group
            group_records = self.census_data.data[self.census_data.data[census_col] == group]
            first_year, last_year = self.years_of_return(group_records)
            if str(first_year) == years[0]:
                group_data["First Year"] = years[0] + " or before"
            else:
                group_data["First Year"] = str(first_year)
            if str(last_year) == years[-1]:
                group_data["Last Year"] = "Open in " + years[-1]
            else:
                group_data["Last Year"] = str(last_year)

            group_data[id_name] = group
            group_data["Type"] = group_records[CensusData.column_labels['UNIT_TYPE']].unique()[0]
            group_data["Group"] = group_records[CensusData.column_labels['name']["GROUP"]].unique()[0]
            # As district, region and county must be the same for all sections
            # in a Group - just get the first one.
            group_data["District"] = group_records[CensusData.column_labels['name']["DISTRICT"]].unique()[0]
            group_data["County"] = group_records["C_name"].unique()[0]
            group_data["Region"] = group_records["R_name"].unique()[0]
            group_data["Scout Country"] = group_records["X_name"].unique()[0]

            # For each year, calculate and add number of beavers, cubs, scouts.
            # Explorers deliberately omitted.
            for year in years:
                group_records_year = group_records.loc[group_records["Year"] == year]
                for section in CensusData.column_labels['sections'].keys():
                    if section != "Explorers":
                        group_data[section + "-" + year] = group_records_year[CensusData.column_labels['sections'][section]["male"]].sum() + group_records_year[CensusData.column_labels['sections'][section]["female"]].sum()
                group_data["Adults-" + year] = group_records_year["Leaders"].sum() + group_records_year["SectAssistants"].sum() + group_records_year["OtherAdults"].sum()

            # To find the postcode and IMD for a range of Sections and Group
            # records across several years. Find the most recent year, and then
            # choose the Postcode, where the IMD Rank is the lowest.
            most_recent_year = str(last_year)
            group_records_most_recent = group_records.loc[group_records["Year"] == most_recent_year]
            min_imd_rank = group_records_most_recent["imd"].min()
            min_imd_records = group_records_most_recent.loc[group_records_most_recent["imd"] == min_imd_rank]
            # add postcode
            if min_imd_records.empty:
                group_records_with_postcode = group_records.loc[group_records["lat"] != "error"]
                min_imd_rank = group_records_with_postcode["imd"].min()
                min_imd_records = group_records_with_postcode.loc[group_records_with_postcode["imd"] == min_imd_rank]

                if min_imd_records.empty:
                    min_imd_records = group_records

            group_data["Postcode"] = min_imd_records[CensusData.column_labels['POSTCODE']].unique()[0]
            country = self.ons_data.COUNTRY_CODES.get(min_imd_records["ctry"].unique()[0])
            if country:
                group_data["IMD Country"] = country
            else:
                group_data["IMD Country"] = CensusData.DEFAULT_VALUE
            # add IMD rank and score and decile
            # group_data["IMD Score"] = min_imd_records["imd_score"].unique()[0]
            group_data["IMD Decile"] = min_imd_records["imd_decile"].unique()[0]
            group_data["IMD Rank"] = min_imd_rank
            # output_data.append(group_data, ignore_index=True)
            group_data_df = pd.DataFrame([group_data], columns=output_columns)
            output_data = pd.concat([output_data, group_data_df], axis=0, sort=False)

        output_data.reset_index(drop=True, inplace=True)
        return output_data

    def new_section_history_summary(self, years):
        # Given data on all sections, provides summary of all new sections, and
        # copes with the pre-2017 section reporting structure
        self.logger.info(f"Beginning new_section_history_summary for {years}")
        new_section_ids = []

        self.logger.info("Finding new Beaver, Cub and Scout Sections")
        # Iterate through Groups looking for new Sections
        group_ids = self.census_data.data[CensusData.column_labels['id']["GROUP"]].unique()
        group_ids = [str(x).strip() for x in group_ids]
        if "nan" in group_ids:
            group_ids.remove("nan")

        for group_id in group_ids:
            group_records = self.census_data.data.loc[self.census_data.data[CensusData.column_labels['id']["GROUP"]] == group_id]

            for section in self.census_data.get_section_names('Group'):
                nu_sections = []
                for year in years:
                    group_records_year = group_records.loc[group_records["Year"] == year]
                    nu_sections.append(group_records_year[CensusData.column_labels['sections'][section]["unit_label"]].sum())
            #    if self.has_increase(nu_sections):
                increments = [nu_sections[ii + 1] - nu_sections[ii] for ii in range(len(nu_sections) - 1)]
                nu_sections_by_year = dict(zip(years, nu_sections))
                if max(increments) > 0:
                    self.logger.debug(f"Identified year profile of sections: {nu_sections_by_year}")
                    opened_sections = []
                    closed_sections = []
                    for year in years[1:]:
                        change = nu_sections_by_year[year] - nu_sections_by_year[str(int(year)-1)]
                        if change > 0:
                            # Extent life of current sections
                            for open_sections in opened_sections:
                                open_sections["years"].append(year)
                            # Create new section record
                            for ii in range(change):
                                self.logger.debug(f"New {section} found for {group_id} in {year}")
                                opened_sections.append({"id": group_id, "section": section, "years": [year], "nu_sections": nu_sections_by_year})
                        elif change == 0:
                            # Lengthens all sections by a year
                            for open_sections in opened_sections:
                                open_sections["years"].append(year)
                        elif change < 0:
                            for ii in range(-change):
                                # Close sections in newest first
                                if len(opened_sections) > 0:
                                    self.logger.debug(f"{section} closed for {group_id} in {year}")
                                    closed_sections.append(opened_sections.pop(-1))
                            # Lengthens remaining open sections by a year
                            for open_sections in opened_sections:
                                open_sections["years"].append(year)

                    self.logger.debug(f"For {group_id} adding\n{opened_sections + closed_sections}")
                    new_section_ids += opened_sections
                    new_section_ids += closed_sections

        self.logger.info("Finding new Explorer Sections")
        # Iterate through District looking for new Sections
        district_ids = self.census_data.data[CensusData.column_labels['id']["DISTRICT"]].unique()
        district_ids = [str(x).strip() for x in district_ids]
        if "nan" in district_ids:
            district_ids.remove("nan")

        for district_id in district_ids:
            district_records = self.census_data.data.loc[self.census_data.data[CensusData.column_labels['id']["DISTRICT"]] == district_id]
            nu_sections = []
            for year in years:
                district_records_year = district_records.loc[district_records["Year"] == year]
                nu_sections.append(district_records_year[CensusData.column_labels['sections']["Explorers"]["unit_label"]].sum())

            increments = [nu_sections[ii + 1] - nu_sections[ii] for ii in range(len(nu_sections) - 1)]
            nu_sections_by_year = dict(zip(years, nu_sections))
            if max(increments) > 0:
                opened_sections = []
                closed_sections = []
                for year in years[1:]:
                    change = nu_sections_by_year[year] - nu_sections_by_year[str(int(year)-1)]
                    if change > 0:
                        # Extent life of current sections
                        for open_sections in opened_sections:
                            open_sections["years"].append(year)
                        # Create new section record
                        for ii in range(change):
                            opened_sections.append({"id": district_id, "section": "Explorers", "years": [year], "nu_sections": nu_sections_by_year})
                    elif change == 0:
                        # Lengthens all sections by a year
                        for open_sections in opened_sections:
                            open_sections["years"].append(year)
                    elif change < 0:
                        for ii in range(-change):
                            # Close sections in oldest order
                            if len(opened_sections) > 0:
                                closed_sections.append(opened_sections.pop(-1))
                        for open_sections in opened_sections:
                            open_sections["years"].append(year)

                self.logger.debug(f"For {district_id} adding\n{opened_sections + closed_sections}")
                new_section_ids += opened_sections
                new_section_ids += closed_sections

        section_details = []
        for year in years:
            # section_details.append(year + "_Units")
            if int(year) >= 2018:
                section_details.append(year + "_Members")
            else:
                section_details.append(year + "_Est_Members")

        output_columns = ["Object_ID", "Section Name", "Section", "Group_ID", "Group", "District_ID", "District", "County", "Region", "Scout Country", "Postcode", "IMD Country", "IMD Rank", "IMD Decile", "First Year", "Last Year", years[0] + "_sections"] + section_details
        output_data = pd.DataFrame(columns=output_columns)

        self.logger.info(f"Start iteration through {len(new_section_ids)} new Sections")
        used_compass_ids = set()
        count = 0
        total = len(new_section_ids)
        for new_sections_id in new_section_ids:
            section_data = {}
            self.logger.debug(f"Recording {new_sections_id}")
            count += 1
            self.logger.info(f"{count} of {total}")
            section_id = new_sections_id["id"]
            open_years = new_sections_id["years"]
            section = new_sections_id["section"]

            if section in self.census_data.get_section_names('Group'):
                records = self.census_data.data.loc[self.census_data.data[CensusData.column_labels['id']["GROUP"]] == section_id]
                section_data["Group_ID"] = records[CensusData.column_labels['id']["GROUP"]].unique()[0]
                section_data["Group"] = records[CensusData.column_labels['name']["GROUP"]].unique()[0]
            elif section in self.census_data.get_section_names('District'):
                records = self.census_data.data.loc[self.census_data.data[CensusData.column_labels['id']["DISTRICT"]] == section_id]
                section_data["Group_ID"] = ""
                section_data["Group"] = ""
            else:
                raise Exception(f"{section} neither belongs to a Group or District. id = {new_sections_id}")

            for year in open_years:
                year_records = records.loc[records["Year"] == year]
                if int(year) >= 2018:
                    compass_id = section_data.get("Object_ID")
                    section_year_records = year_records.loc[records[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections'][section]["type"]]

                    if compass_id:
                        section_record = section_year_records.loc[section_year_records["Object_ID"] == compass_id]
                        section_data[year + "_Members"] = section_record[CensusData.column_labels['sections'][section]["male"]].sum() + section_record[CensusData.column_labels['sections'][section]["female"]].sum()
                    else:
                        section_year_ids = section_year_records["Object_ID"].unique()
                        if int(open_years[0]) >= 2018:
                            # If section became open after 31st January 2017 then can identify by Object_ID id
                            last_year_records = records.loc[records["Year"] == str(int(year) - 1)]
                            old_section_ids = last_year_records["Object_ID"].unique()
                            opened_section_ids = [section_id for section_id in section_year_ids if section_id not in old_section_ids]
                            if len(opened_section_ids) > 1:
                                self.logger.info(f"{len(opened_section_ids)} sections opened")
                                temp_compass_id = opened_section_ids[0]
                                ii = 0
                                continue_search = True
                                while (temp_compass_id in used_compass_ids) and continue_search:
                                    if ii < len(opened_section_ids):
                                        temp_compass_id = opened_section_ids[ii]
                                        ii += 1
                                    else:
                                        continue_search = False
                                compass_id = temp_compass_id
                            elif len(opened_section_ids) == 0:
                                self.logger.error(f"No sections opened\n{year}: {section_year_ids}\n{int(year)-1}: {old_section_ids}")
                            elif len(opened_section_ids) == 1:
                                compass_id = opened_section_ids[0]
                                self.logger.debug(f"Assigned id: {compass_id}")

                            section_data["Object_ID"] = compass_id
                            used_compass_ids.add(compass_id)
                            section_record = section_year_records.loc[section_year_records["Object_ID"] == compass_id]
                            section_data[year + "_Members"] = section_record[CensusData.column_labels['sections'][section]["male"]].sum() + section_record[CensusData.column_labels['sections'][section]["female"]].sum()
                        else:
                            compass_id = max(section_year_ids)
                            if compass_id in used_compass_ids:
                                section_year_ids.sort()
                                ii = 0
                                while compass_id in used_compass_ids:
                                    compass_id = section_year_ids[-ii]
                                    ii += 1
                            section_data["Object_ID"] = compass_id
                            used_compass_ids.add(compass_id)
                            section_record = section_year_records.loc[section_year_records["Object_ID"] == compass_id]
                            male_members = section_record[CensusData.column_labels['sections'][section]["male"]].sum()
                            female_members = section_record[CensusData.column_labels['sections'][section]["female"]].sum()
                            self.logger.debug(f"{section} in {section_id} in {year} found {male_members + female_members} members")
                            section_data[year + "_Members"] = male_members + female_members
                else:
                    year_before_section_opened = str(int(open_years[0])-1)
                    year_before_records = records.loc[records["Year"] == year_before_section_opened]

                    number_of_new_sections = new_sections_id["nu_sections"][open_years[0]] - new_sections_id["nu_sections"][year_before_section_opened]

                    old_male_members = year_before_records[CensusData.column_labels['sections'][section]["male"]].sum()
                    old_female_members = year_before_records[CensusData.column_labels['sections'][section]["female"]].sum()
                    old_members = old_male_members + old_female_members

                    new_male_members = year_records[CensusData.column_labels['sections'][section]["male"]].sum()
                    new_female_members = year_records[CensusData.column_labels['sections'][section]["female"]].sum()
                    new_members = new_male_members + new_female_members

                    additional_members = (new_members - old_members) / number_of_new_sections
                    if additional_members < 0:
                        self.logger.warning(f"{section_id} increased number of {section} sections but membership decreased by {additional_members}")

                    self.logger.debug(f"{section} in {section_id} in {year} found {additional_members} members")
                    section_data[year + "_Est_Members"] = additional_members

            closed_years = [year for year in years if year not in open_years]
            for year in closed_years:
                if int(year) >= 2018:
                    section_data[year + "_Members"] = 0
                else:
                    section_data[year + "_Est_Members"] = 0

            section_data[years[0] + "_sections"] = new_sections_id["nu_sections"][years[0]]

            if section_data.get("Object_ID"):
                section_records = records.loc[records["Object_ID"] == section_data.get("Object_ID")]
                section_data["Section Name"] = section_records["name"].unique()[0]
            else:
                if int(open_years[-1]) < 2017:
                    if section in self.census_data.get_section_names('Group'):
                        section_records = records.loc[records[CensusData.column_labels['UNIT_TYPE']] == self.census_data.UNIT_LEVEL_GROUP]
                    elif section in self.census_data.get_section_names('District'):
                        section_records = records.loc[records[CensusData.column_labels['UNIT_TYPE']] == self.census_data.UNIT_LEVEL_DISTRICT]
                elif int(open_years[-1]) == 2017:
                    section_records = records.loc[records[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections'][section]["type"]]
                else:
                    raise Exception(f"Unable to find section records for {new_section_ids}")

            section_data["Section"] = section
            section_data["District_ID"] = section_records[CensusData.column_labels['id']["DISTRICT"]].unique()[0]
            section_data["District"] = section_records[CensusData.column_labels['name']["DISTRICT"]].unique()[0]
            section_data["County"] = section_records["C_name"].unique()[0]
            section_data["Region"] = section_records["R_name"].unique()[0]
            section_data["Scout Country"] = section_records["X_name"].unique()[0]

            if open_years[0] == years[0]:
                section_data["First Year"] = years[0] + " or before"
            else:
                section_data["First Year"] = open_years[0]
            if open_years[-1] == years[-1]:
                section_data["Last Year"] = "Open in " + years[-1]
            else:
                section_data["Last Year"] = open_years[-1]

            # To find the postcode and IMD for a range of Sections and Group
            # records across several years. Find the most recent year, and then
            # choose the Postcode, where the IMD Rank is the lowest.
            most_recent_year = open_years[-1]
            most_recent = section_records.loc[section_records["Year"] == most_recent_year]
            if most_recent.shape[0] == 1:
                most_recent = most_recent.iloc[0]
            elif most_recent.shape[0] == 0:
                self.logger.warning("Inconsistent ids")
                if section in self.census_data.get_section_names('Group'):
                    # In the event that the Object_IDs aren't consistent, pick a section in the group that's most recent
                    # is only applicable after 2017, so sections are assumed to exist.
                    self.logger.debug(f"There are {records.shape[0]} group records")
                    group_sections = records.loc[records[CensusData.column_labels['id']["GROUP"]] == section_data["Group_ID"]]
                    self.logger.debug(f"There are {group_sections.shape[0]} group records")
                    section_rec = group_sections.loc[group_sections[CensusData.column_labels['UNIT_TYPE']] == CensusData.column_labels['sections'][section]["type"]]
                    self.logger.debug(f"There are {section_rec.shape[0]} group records in {section}")
                    most_recent_sec = section_rec.loc[section_rec["Year"] == most_recent_year]
                    self.logger.debug(f"There are {most_recent_sec.shape[0]} group records in {section} in {most_recent_year}")
                    most_recent = most_recent_sec.iloc[0]
                elif section in self.census_data.get_section_names('District'):
                    district_sections = records.loc[records[CensusData.column_labels['id']["DISTRICT"]] == section_data["District_ID"]]
                    section_rec = district_sections.loc[district_sections[CensusData.column_labels['UNIT_TYPE']] == section]
                    most_recent = section_rec.loc[section_rec["Year"] == most_recent_year].iloc[0]
            else:
                self.logger.warning("Multiple sections found, assigning a section")
                most_recent = most_recent.iloc[0]

            postcode_valid = most_recent.at["postcode_is_valid"]
            # self.logger.debug(f"Identified:\n{most_recent} determined postcode valid:\n{postcode_valid}\n{postcode_valid == 1}\n{int(postcode_valid) == 1}")
            # add postcode
            if postcode_valid == "1":
                self.logger.debug(f"Adding postcode {most_recent.at[CensusData.column_labels['POSTCODE']]}")
                section_data["Postcode"] = most_recent.at[CensusData.column_labels['POSTCODE']]
                country = self.ons_data.COUNTRY_CODES.get(most_recent.at["ctry"])
                if country:
                    section_data["IMD Country"] = country
                else:
                    section_data["IMD Country"] = CensusData.DEFAULT_VALUE
                section_data["IMD Decile"] = most_recent.at["imd_decile"]
                section_data["IMD Rank"] = most_recent.at["imd"]
            else:
                section_data["Postcode"] = CensusData.DEFAULT_VALUE
                section_data["IMD Country"] = CensusData.DEFAULT_VALUE
                section_data["IMD Decile"] = CensusData.DEFAULT_VALUE
                section_data["IMD Rank"] = CensusData.DEFAULT_VALUE

            section_data_df = pd.DataFrame([section_data], columns=output_columns)
            output_data = pd.concat([output_data, section_data_df], axis=0)

        output_data.reset_index(drop=True, inplace=True)
        return output_data

    def add_IMD_decile(self):
        self.logger.info("Adding Index of Multiple Deprivation Decile")

        self.census_data.data["imd_decile"] = self.census_data.data.apply(lambda row:
            self.calc_imd_decile(int(row["imd"]), row["ctry"]) if row["imd"] != "error" else "error", axis=1)

        return self.census_data.data

    def country_add_IMD_decile(self, data, country):
        """Used to add IMD data to DataFrames that aren't the core census data

        For example used to add IMD deciles to Lower Super Output Area boundary
        reports.

        All boundaries must be from the same country.

        :param DataFrame data: Data to add IMD decile to. Must have 'imd' column
        :param str country: Country code

        :returns DataFrame: Original DataFrame with extra imd_decile column
        """
        data["imd_decile"] = data.apply(lambda row: self.calc_imd_decile(int(row["imd"]), country) if row["imd"] != "error" else "error", axis=1)
        return data

    def calc_imd_decile(self, rank, ctry):
        country = self.ons_data.COUNTRY_CODES.get(ctry)
        if country:
            # upside down floor division to get ceiling
            return -((-rank * 10) // self.ons_data.IMD_MAX[country])
        else:
            return "error"

    def group_IDs_from_fields(self, group_details, census_cols):
        groups = self.census_data.data.loc[self.census_data.data[CensusData.column_labels['UNIT_TYPE']] == self.census_data.UNIT_LEVEL_GROUP]
        input_cols = list(group_details.columns.values)
        output_columns = input_cols + [CensusData.column_labels['id']["GROUP"]] + census_cols
        output_pd = pd.DataFrame(columns=output_columns)

        paired_cols = list(zip(input_cols, census_cols))

        for group in group_details.itertuples():
            self.logger.debug(group)
            group_data = {}
            dict_group = group._asdict()
            for col in input_cols:
                group_data[col] = dict_group[col]

            for col in census_cols:
                group_data[col] = None

            for paired_columns in paired_cols:
                group_record = groups.loc[groups[paired_columns[1]] == str(dict_group[paired_columns[0]]).strip()]
                matching_group_ids = group_record[CensusData.column_labels['id']["GROUP"]].unique()
                self.logger.debug(f"Group matched: {matching_group_ids}")
                if len(matching_group_ids) == 1:
                    self.logger.info(f"Matched group")
                    group_data[CensusData.column_labels['id']["GROUP"]] = matching_group_ids[0]
                    for col in census_cols:
                        group_data[col] = group_record[col].unique()[0]
                elif len(matching_group_ids) > 1:
                    self.logger.error(f"Error. Multiple Group IDs possible for: {group} looking for {paired_columns[0]}")
                elif len(matching_group_ids) == 0:
                    self.logger.error(f"No group matches {group} looking for {paired_columns[0]}")

            group_data_df = pd.DataFrame([group_data], columns=output_columns)
            output_pd = pd.concat([output_pd, group_data_df], axis=0)

        output_pd.reset_index(drop=True, inplace=True)
        return output_pd

    def create_district_boundaries(self):
        """
        Creates a GeoJSON file for the District Boundaries of the Scout Census.

        Aims to create a circular boundary around every section of maximal size
        that doesn't overlap or leave gaps between Districts.
        """

        if not self.has_ons_data():
            raise Exception("Must have ons data added before creating district boundaries")

        # Find all the District IDs and names
        districts = self.census_data.data[[CensusData.column_labels['id']["DISTRICT"], CensusData.column_labels['name']["DISTRICT"]]].drop_duplicates()

        # Finds all the records with valid postcodes in the Scout Census
        valid_locations = self.census_data.data.loc[self.census_data.data[CensusData.column_labels['VALID_POSTCODE']] == 1]

        # Creates a new dataframe with a subset of columns resulting in
        # each location being a distinct row
        all_locations = pd.DataFrame(columns=["D_ID", "D_name", "lat", "long"])
        all_locations[["D_name", "Object_ID"]] = valid_locations[["D_name", "Object_ID"]]
        all_locations[["D_ID", "lat", "long"]] = valid_locations[["D_ID", "lat", "long"]].apply(pd.to_numeric, errors='coerce')
        all_locations.drop_duplicates(subset=["lat", "long"], inplace=True)

        # Uses the lat and long co-ords from above to create a GeoDataFrame
        all_points = gpd.GeoDataFrame(all_locations, geometry=gpd.points_from_xy(all_locations.long, all_locations.lat))
        all_points.crs = {'init': 'epsg:4326'}

        # Converts the co-ordinate reference system into OS36 which uses
        # (x-y) coordinates in metres, rather than (long, lat) coordinates.
        all_points = all_points.to_crs({'init': 'epsg:27700'})
        all_points.reset_index(inplace=True)

        self.logger.info(f"Found {len(all_points.index)} different Section points")

        # Calculates all the other points within twice the distance of the
        # closest point from a neighbouring district
        all_points["nearest_points"] = all_points.apply(lambda row: self.nearest_other_points(row, all_points.loc[all_points["D_ID"] != row["D_ID"]]), axis=1)
        all_points["buffer_distance"] = 0

        # Initial calcuation of the buffer distances
        self.logger.info("Calculating buffer distances of " + str(all_points["buffer_distance"].value_counts().iloc[0]) + " points")
        all_points["buffer_distance"] = all_points.apply(lambda row: self.buffer_distance(row, all_points), axis=1)
        self.logger.info("On first pass " + str(all_points["buffer_distance"].value_counts().iloc[0]) + " missing buffer distance")

        old_number = all_points["buffer_distance"].value_counts().iloc[0]
        new_number = 0
        # The algorithm is iterative, so stop when no more points have their
        # buffers identified
        while new_number < old_number:
            old_number = all_points["buffer_distance"].value_counts().iloc[0]
            all_points["buffer_distance"] = all_points.apply(lambda row: self.buffer_distance(row, all_points), axis=1)
            new_number = all_points["buffer_distance"].value_counts().iloc[0]
            self.logger.info(f"On next pass {new_number} missing buffer distance")
            _ = all_points.loc[all_points["buffer_distance"] == 0]
            self.logger.debug(f"The following points do not have buffer distances defined:\n{_}")

        # Create the GeoDataFrame that will form the GeoJSON
        output_columns = ["id", "name"]
        output_gpd = gpd.GeoDataFrame(columns=output_columns)
        district_nu = 0
        for count, district in districts.iterrows():
            if str(district["D_ID"]) != "nan":
                district_nu += 1
                data = {
                    "id": [district["D_ID"]],
                    "name": [district["D_name"]]
                }
                self.logger.info(f"{district_nu}/{len(districts)} calculating boundary of {district['D_name']}")

                district_points = all_points.loc[all_points["D_ID"] == district["D_ID"]]

                # For each of the points in the district, produces a polygon to
                # represent the buffered point from the buffer distances
                # calculated above
                buffered_points = district_points.apply(lambda row: row["geometry"].buffer(row["buffer_distance"]), axis=1)

                # Unifies the polygons created from each point in the District
                # into one polygon for the District.
                district_polygon = shapely.ops.unary_union(buffered_points)

                data_df = gpd.GeoDataFrame(data, columns=output_columns, geometry=[district_polygon])
                output_gpd = gpd.GeoDataFrame(pd.concat([output_gpd, data_df], axis=0, sort=False))

        output_gpd.crs = {'init': 'epsg:27700'}

        # Convert co-ordinates back to WGS84, which uses latitude and longditude
        output_gpd = output_gpd.to_crs({'init': 'epsg:4326'})
        output_gpd.reset_index(drop=True, inplace=True)

        self.logger.debug(f"output gpd\n{output_gpd}")
        output_gpd[["id"]] = output_gpd[["id"]].apply(pd.to_numeric, errors='coerce')
        self.logger.debug(f"output gpd\n{output_gpd}")
        output_gpd.to_file("districts_buffered.geojson", driver='GeoJSON')

    def buffer_distance(self, point_details, all_points):
        obj_id = point_details["Object_ID"]
        self.logger.debug(f"Finding buffer distance of {point_details.index} with object ID {obj_id}")
        distance = 0
        nearest_points = point_details["nearest_points"]
        if point_details["buffer_distance"] == 0:
            valid = True
            for nearby_point in nearest_points:
                point_obj = nearby_point["Point"]
                buffer = self.buffer_distance_from_point(point_obj, all_points)
                if buffer != 0:
                    new_distance = nearby_point["Distance"] - buffer
                    if distance == 0:
                        distance = new_distance
                    elif new_distance < distance:
                        distance = new_distance
                else:
                    if (distance == 0) or (distance > (nearby_point["Distance"] / 2)):
                        # Decide if these two points are a 'pair'.
                        # I.e. if the restricting factor is just their
                        # mutual closeness.
                        nearby_point_details = all_points.loc[all_points["geometry"] == point_obj]
                        nearest_to_nearby = nearby_point_details["nearest_points"].iloc[0]
                        unset_nearby = [p["Point"] for p in nearest_to_nearby if self.buffer_distance_from_point(p["Point"], all_points) == 0]
                        if unset_nearby:
                            closer_set = []
                            ii = 0
                            while nearest_to_nearby[ii]["Point"] != unset_nearby[0]:
                                closer_set.append(nearest_to_nearby[ii])
                                ii += 1
                            buffers = [self.buffer_distance_from_point(p["Point"], all_points) for p in closer_set]
                            if 0 in buffers:
                                # Means that there is a closer point with no buffer defined
                                valid = False
                            elif buffers and (max(buffers) > nearby_point["Distance"] / 2):
                                # Means that there is closer point with a buffer big enough to make a difference
                                valid = False
                            else:
                                if unset_nearby[0] == point_details["geometry"]:
                                    # The closest unset point to this near point we are considering is the original point
                                    distance = nearby_point["Distance"] / 2
                                else:
                                    valid = False
            if not valid:
                distance = 0
        else:
            distance = point_details["buffer_distance"]
        return distance

    @staticmethod
    def buffer_distance_from_point(point, all_points):
        """
        Find the distance recorded using the point as the key

        :param shapely.Point point: Point interested in
        :param GeoDataFrame all_points: DataFrame containing 'buffer_distance' column

        :returns float: Distance recorded as buffer from point
        """
        point_details = all_points.loc[all_points["geometry"] == point]
        buffer = point_details["buffer_distance"].iloc[0]
        return buffer

    def nearest_other_points(self, row, other_data):
        """
        Given a row of a GeoDataFrame and a subset of a GeoDataFrame returns
        the points and corresponding distances for all points with twice
        the minimum distance from the row to the subset.

        :param DataSeries row: Row of a GeoDataFrame
        :param DataFrame other_data: Other rows of a GeoDataFrame

        :returns list: Sorted list of dictionaries containing points and distances
        """
        point = row["geometry"]
        self.logger.debug("nearest_other_points:" + str(row.index))
        other_points = shapely.geometry.MultiPoint(other_data["geometry"].tolist())
        distance = point.distance(other_points)*2
        points = [{"Point": p, "Distance": point.distance(p)} for p in other_points if point.distance(p) < distance]
        points.sort(key=lambda i: i["Distance"])
        self.logger.debug(points)
        return points

    def old_buffer_distance(self, point, data, id, id_col):
        """
        Legacy function to be removed
        """
        self.logger.error("old_buffer_distance is obselete function")
        self.logger.debug(f"Finding buffer distance of {point.wkt} in {id}")
        data_not_in_area = data.loc[data[id_col] != id]
        points_not_in_area = shapely.geometry.MultiPoint([p for p in data_not_in_area.geometry])

        data_in_area = data.loc[data[id_col] == id]
        points_in_area = shapely.geometry.MultiPoint([p for p in data_in_area.geometry])

        nearest_other_point = shapely.ops.nearest_points(points_not_in_area, point)[0]
        nearest_in_area_point = shapely.ops.nearest_points(points_in_area, nearest_other_point)[0]

        if nearest_in_area_point == point:
            buffer_distance = point.distance(nearest_other_point)/2
            self.logger.info(f"Buffer distance of {point.wkt} is {buffer_distance}")
        else:
            new_id_record = data.loc[data["geometry"] == nearest_other_point]
            new_id_record.reset_index(inplace=True)
            new_id = new_id_record.at[0, id_col]
            self.logger.info(f"To find buffer distance of {point.wkt} in {id} need to find it for {nearest_other_point.wkt} in {new_id}")
            buffer_distance = point.distance(nearest_other_point) - self.old_buffer_distance(nearest_other_point, data, new_id, id_col)

            points_not_in_area_or_nearest = shapely.geometry.MultiPoint([p for p in points_not_in_area if p != nearest_in_area_point])
            next_nearest_other_point = shapely.ops.nearest_points(points_not_in_area_or_nearest, point)[0]
            buffer_distance = min(buffer_distance, point.distance(next_nearest_other_point)/2)
            self.logger.info(f"Buffer distance of {point.wkt} is {buffer_distance}")

        return buffer_distance

    @staticmethod
    def years_of_return(records):
        years_of_data = [int(year) for year in records["Year"].unique()]
        return min(years_of_data), max(years_of_data)

    @staticmethod
    def has_increase(numeric_list):
        increments = [numeric_list[ii + 1] - numeric_list[ii] for ii in range(len(numeric_list) - 1)]
        max_increment = max(increments)
        return max_increment > 0

    def add_custom_data(self, csv_file_path, name, location_type="Postcodes", location_cols=None, markers_clustered=False, marker_data=None):
        """Function to add custom data as markers on map

        Note that the create_map function must have been called first, to
        populate self.map object.

        :param str csv_file_path: file path to open csv file
        :param str name: Name of layer that the markers will be added to
        :param str location_type: Either "Postcodes" or "Co-ordinates"
        :param str/dict location_cols: If "Co-ordinates" requires a dict {"crs": , "x": , "y": }
                                   If "Postcodes" the column name of the Postcode columm
        :param bool markers_clustered: Whether to cluster the markers or not
        :param list marker_data: list of strings for values in data that should be in popup
        """

        data = pd.read_csv(csv_file_path)

        if location_type == "Postcodes":
            # Merge with ONS Postcode Directory to obtain dataframe with lat/long
            data = pd.merge(data, self.ons_data.data, how='left', left_on=location_cols, right_index=True, sort=False)
            location_cols = {"crs": '4326', "x": "long", "y": "lat"}

        # Create geo data frame with points generated from lat/long or OS
        data = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data[location_cols["x"]], data[location_cols["y"]]))

        # Convert the 'Co-ordinate reference system' (crs) to WGS_84 (i.e. lat/long) if not already
        data.crs = {'init': f"epsg:{location_cols['crs']}"}
        data = data.to_crs({'init': 'epsg:4326'})

        self.map.add_layer(name, markers_clustered)

        # For each point plot marker, and include marker_data in the popup
        for index, row in data.iterrows():
            if marker_data:
                html = ""
                for data in marker_data:
                    html += f"<p align=\"center\">{row[data]}<p align=\"center\">"
                iframe = folium.IFrame(html=html, width=350, height=100)
                popup = folium.Popup(iframe, max_width=2650)
            else:
                popup = None
            if not np.isnan(row.geometry.x):
                self.map.add_marker(row.geometry.y, row.geometry.x, popup, 'green', name)
