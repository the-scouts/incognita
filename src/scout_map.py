import pandas as pd
import numpy as np
from src.map_plotter import ChoroplethMapPlotter
from src.scout_census import ScoutCensus
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
        self.census_data = ScoutCensus(census_csv_path)

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
        """Merges ScoutCensus object with ONSPostcodeDirectory object and outputs to csv

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
        merge.clean_and_verify_postcode(self.census_data.data, ScoutCensus.column_labels['POSTCODE'])

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
            ScoutCensus.column_labels['VALID_POSTCODE'],
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
            for section in ScoutCensus.column_labels['sections'].keys():
                self.logger.debug(f"Analysis of {section} member exclusions")
                section_type = ScoutCensus.column_labels['sections'][section]["type"]
                section_dict = ScoutCensus.column_labels['sections'][section]

                excluded_sections = excluded_data.loc[excluded_data[ScoutCensus.column_labels['UNIT_TYPE']] == section_type]
                self.logger.debug(f"Excluded sections\n{excluded_sections}")
                self.logger.debug(f"Finding number of excluded {section} by summing {section_dict['male']} and {section_dict['female']}")
                excluded_members = excluded_sections[section_dict["male"]].sum() + excluded_sections[section_dict["female"]].sum()
                self.logger.debug(f"{excluded_members} {section} excluded")

                sections = self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['UNIT_TYPE']] == section_type]
                counted_members = sections[section_dict["male"]].sum() + sections[section_dict["female"]].sum()

                original_members = counted_members + excluded_members

                if original_members > 0:
                    self.logger.info(f"{excluded_members} {section} members were removed ({excluded_members / original_members * 100}%) of total")
                else:
                    self.logger.info(f"There are no {section} members present in data")

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

    @staticmethod
    def section_from_type(type):
        for section in ScoutCensus.column_labels['sections'].keys():
            if type == ScoutCensus.column_labels['sections'][section]["type"]:
                return section

    def group_history_summary(self, years):
        self.logger.info("Beginning group_history_summary")
        return self.history_summary(years, "Group ID", ScoutCensus.column_labels['id']["GROUP"])

    def section_history_summary(self, years):
        # Works effectively for years after 2017
        self.logger.info("Beginning section_history_summary")
        return self.history_summary(years, "compass ID", "compass")

    def history_summary(self, years, id_name, census_col):
        # Must have imd scores and deciles already in census_postcode_data.
        section_numbers = []
        for year in years:
            for section in ScoutCensus.column_labels['sections'].keys():
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
            group_data["Type"] = group_records[ScoutCensus.column_labels['UNIT_TYPE']].unique()[0]
            group_data["Group"] = group_records[ScoutCensus.column_labels['name']["GROUP"]].unique()[0]
            # As district, region and county must be the same for all sections
            # in a Group - just get the first one.
            group_data["District"] = group_records[ScoutCensus.column_labels['name']["DISTRICT"]].unique()[0]
            group_data["County"] = group_records["C_name"].unique()[0]
            group_data["Region"] = group_records["R_name"].unique()[0]
            group_data["Scout Country"] = group_records["X_name"].unique()[0]

            # For each year, calculate and add number of beavers, cubs, scouts.
            # Explorers deliberately omitted.
            for year in years:
                group_records_year = group_records.loc[group_records["Year"] == year]
                for section in ScoutCensus.column_labels['sections'].keys():
                    if section != "Explorers":
                        group_data[section + "-" + year] = group_records_year[ScoutCensus.column_labels['sections'][section]["male"]].sum() + group_records_year[ScoutCensus.column_labels['sections'][section]["female"]].sum()
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

            group_data["Postcode"] = min_imd_records[ScoutCensus.column_labels['POSTCODE']].unique()[0]
            country = self.ons_data.COUNTRY_CODES.get(min_imd_records["ctry"].unique()[0])
            if country:
                group_data["IMD Country"] = country
            else:
                group_data["IMD Country"] = ScoutCensus.DEFAULT_VALUE
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
        group_ids = self.census_data.data[ScoutCensus.column_labels['id']["GROUP"]].unique()
        group_ids = [str(x).strip() for x in group_ids]
        if "nan" in group_ids:
            group_ids.remove("nan")

        for group_id in group_ids:
            group_records = self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['id']["GROUP"]] == group_id]

            for section in self.census_data.get_section_names('Group'):
                nu_sections = []
                for year in years:
                    group_records_year = group_records.loc[group_records["Year"] == year]
                    nu_sections.append(group_records_year[ScoutCensus.column_labels['sections'][section]["unit_label"]].sum())
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
        district_ids = self.census_data.data[ScoutCensus.column_labels['id']["DISTRICT"]].unique()
        district_ids = [str(x).strip() for x in district_ids]
        if "nan" in district_ids:
            district_ids.remove("nan")

        for district_id in district_ids:
            district_records = self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['id']["DISTRICT"]] == district_id]
            nu_sections = []
            for year in years:
                district_records_year = district_records.loc[district_records["Year"] == year]
                nu_sections.append(district_records_year[ScoutCensus.column_labels['sections']["Explorers"]["unit_label"]].sum())

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
                records = self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['id']["GROUP"]] == section_id]
                section_data["Group_ID"] = records[ScoutCensus.column_labels['id']["GROUP"]].unique()[0]
                section_data["Group"] = records[ScoutCensus.column_labels['name']["GROUP"]].unique()[0]
            elif section in self.census_data.get_section_names('District'):
                records = self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['id']["DISTRICT"]] == section_id]
                section_data["Group_ID"] = ""
                section_data["Group"] = ""
            else:
                raise Exception(f"{section} neither belongs to a Group or District. id = {new_sections_id}")

            for year in open_years:
                year_records = records.loc[records["Year"] == year]
                if int(year) >= 2018:
                    compass_id = section_data.get("Object_ID")
                    section_year_records = year_records.loc[records[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections'][section]["type"]]

                    if compass_id:
                        section_record = section_year_records.loc[section_year_records["Object_ID"] == compass_id]
                        section_data[year + "_Members"] = section_record[ScoutCensus.column_labels['sections'][section]["male"]].sum() + section_record[ScoutCensus.column_labels['sections'][section]["female"]].sum()
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
                            section_data[year + "_Members"] = section_record[ScoutCensus.column_labels['sections'][section]["male"]].sum() + section_record[ScoutCensus.column_labels['sections'][section]["female"]].sum()
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
                            male_members = section_record[ScoutCensus.column_labels['sections'][section]["male"]].sum()
                            female_members = section_record[ScoutCensus.column_labels['sections'][section]["female"]].sum()
                            self.logger.debug(f"{section} in {section_id} in {year} found {male_members + female_members} members")
                            section_data[year + "_Members"] = male_members + female_members
                else:
                    year_before_section_opened = str(int(open_years[0])-1)
                    year_before_records = records.loc[records["Year"] == year_before_section_opened]

                    number_of_new_sections = new_sections_id["nu_sections"][open_years[0]] - new_sections_id["nu_sections"][year_before_section_opened]

                    old_male_members = year_before_records[ScoutCensus.column_labels['sections'][section]["male"]].sum()
                    old_female_members = year_before_records[ScoutCensus.column_labels['sections'][section]["female"]].sum()
                    old_members = old_male_members + old_female_members

                    new_male_members = year_records[ScoutCensus.column_labels['sections'][section]["male"]].sum()
                    new_female_members = year_records[ScoutCensus.column_labels['sections'][section]["female"]].sum()
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
                        section_records = records.loc[records[ScoutCensus.column_labels['UNIT_TYPE']] == self.census_data.UNIT_LEVEL_GROUP]
                    elif section in self.census_data.get_section_names('District'):
                        section_records = records.loc[records[ScoutCensus.column_labels['UNIT_TYPE']] == self.census_data.UNIT_LEVEL_DISTRICT]
                elif int(open_years[-1]) == 2017:
                    section_records = records.loc[records[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections'][section]["type"]]
                else:
                    raise Exception(f"Unable to find section records for {new_section_ids}")

            section_data["Section"] = section
            section_data["District_ID"] = section_records[ScoutCensus.column_labels['id']["DISTRICT"]].unique()[0]
            section_data["District"] = section_records[ScoutCensus.column_labels['name']["DISTRICT"]].unique()[0]
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
                    group_sections = records.loc[records[ScoutCensus.column_labels['id']["GROUP"]] == section_data["Group_ID"]]
                    self.logger.debug(f"There are {group_sections.shape[0]} group records")
                    section_rec = group_sections.loc[group_sections[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections'][section]["type"]]
                    self.logger.debug(f"There are {section_rec.shape[0]} group records in {section}")
                    most_recent_sec = section_rec.loc[section_rec["Year"] == most_recent_year]
                    self.logger.debug(f"There are {most_recent_sec.shape[0]} group records in {section} in {most_recent_year}")
                    most_recent = most_recent_sec.iloc[0]
                elif section in self.census_data.get_section_names('District'):
                    district_sections = records.loc[records[ScoutCensus.column_labels['id']["DISTRICT"]] == section_data["District_ID"]]
                    section_rec = district_sections.loc[district_sections[ScoutCensus.column_labels['UNIT_TYPE']] == section]
                    most_recent = section_rec.loc[section_rec["Year"] == most_recent_year].iloc[0]
            else:
                self.logger.warning("Multiple sections found, assigning a section")
                most_recent = most_recent.iloc[0]

            postcode_valid = most_recent.at["postcode_is_valid"]
            # self.logger.debug(f"Identified:\n{most_recent} determined postcode valid:\n{postcode_valid}\n{postcode_valid == 1}\n{int(postcode_valid) == 1}")
            # add postcode
            if postcode_valid == "1":
                self.logger.debug(f"Adding postcode {most_recent.at[ScoutCensus.column_labels['POSTCODE']]}")
                section_data["Postcode"] = most_recent.at[ScoutCensus.column_labels['POSTCODE']]
                country = self.ons_data.COUNTRY_CODES.get(most_recent.at["ctry"])
                if country:
                    section_data["IMD Country"] = country
                else:
                    section_data["IMD Country"] = ScoutCensus.DEFAULT_VALUE
                section_data["IMD Decile"] = most_recent.at["imd_decile"]
                section_data["IMD Rank"] = most_recent.at["imd"]
            else:
                section_data["Postcode"] = ScoutCensus.DEFAULT_VALUE
                section_data["IMD Country"] = ScoutCensus.DEFAULT_VALUE
                section_data["IMD Decile"] = ScoutCensus.DEFAULT_VALUE
                section_data["IMD Rank"] = ScoutCensus.DEFAULT_VALUE

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
        groups = self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['UNIT_TYPE']] == self.census_data.UNIT_LEVEL_GROUP]
        input_cols = list(group_details.columns.values)
        output_columns = input_cols + [ScoutCensus.column_labels['id']["GROUP"]] + census_cols
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
                matching_group_ids = group_record[ScoutCensus.column_labels['id']["GROUP"]].unique()
                self.logger.debug(f"Group matched: {matching_group_ids}")
                if len(matching_group_ids) == 1:
                    self.logger.info(f"Matched group")
                    group_data[ScoutCensus.column_labels['id']["GROUP"]] = matching_group_ids[0]
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

    @staticmethod
    def years_of_return(records):
        years_of_data = [int(year) for year in records["Year"].unique()]
        return min(years_of_data), max(years_of_data)

    @staticmethod
    def has_increase(numeric_list):
        increments = [numeric_list[ii + 1] - numeric_list[ii] for ii in range(len(numeric_list) - 1)]
        max_increment = max(increments)
        return max_increment > 0
