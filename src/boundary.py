import pandas as pd
import collections

from src.base import Base
from src.scout_map import ScoutMap
from src.scout_census import ScoutCensus

np = pd.np


class Boundary(Base):
    """

    :var dict ScoutMap.SECTION_AGES: Holds information about scout sections
    """

    SECTION_AGES = {
        'Beavers': [(6, 1), (7, 1)],
        'Cubs': [(8, 1), (9, 1), (10, 0.5)],
        'Scouts': [(10, 0.5), (11, 1), (12, 1), (13, 1)],
        'Explorers': [(14, 1), (15, 1), (16, 1), (17, 1)]
    }

    def __init__(self, geography_name, scout_data_object: ScoutMap):
        super().__init__(settings=True)

        self.census_data = scout_data_object.census_data
        self.ons_pd = scout_data_object.ons_pd

        self.boundary_dict = None
        self.boundary_regions_data = None
        self.boundary_report = {}

        self.district_mapping = {}

        self.set_boundary(geography_name)

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
        district_id_column = ScoutCensus.column_labels['id']["DISTRICT"]

        region_ids = self.boundary_regions_data[codes_key].dropna().drop_duplicates()

        district_ids_by_region = self.census_data.data.loc[self.census_data.data[region_type].isin(region_ids), [region_type, district_id_column,]].dropna().drop_duplicates()
        district_ids = district_ids_by_region[district_id_column].dropna().drop_duplicates()

        region_ids_by_district = self.census_data.data.loc[self.census_data.data[district_id_column].isin(district_ids), [district_id_column, region_type]]
        region_ids_by_district = region_ids_by_district.loc[~(region_ids_by_district[region_type] == ScoutCensus.DEFAULT_VALUE)].dropna().drop_duplicates()

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

        #years_in_data = self.census_data.data[ScoutCensus.column_labels['YEAR']].unique().tolist()
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
            output_columns.append("%-" + ScoutCensus.column_labels['sections']["Beavers"]["top_award"])
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

        district_id_column = ScoutCensus.column_labels['id']["DISTRICT"]
        for ii in range(len(self.boundary_regions_data.index)):
            self.logger.debug(f"{ii+1} out of {len(self.boundary_regions_data.index)}")
            boundary_data = {
                "Name": self.boundary_regions_data.iloc[ii, 1],
                name: self.boundary_regions_data.iloc[ii, 0]}
            code = boundary_data[name]  # == self.boundary_regions_data.iloc[ii, 0]

            records_in_boundary = self.census_data.data.loc[self.census_data.data[name] == code]
            self.logger.debug(f"Found {len(records_in_boundary.index)} records with {name} == {code}")

            # list_of_groups = records_in_boundary[ScoutCensus.column_labels['id']["GROUP"]].unique()
            # list_of_districts = records_in_boundary[ScoutCensus.column_labels['id']["DISTRICT"]].unique()

            if "Groups" in options:
                # Used to list the groups that operate within the boundary
                group_names_in_boundary = [str(x).strip() for x in records_in_boundary[ScoutCensus.column_labels['name']["GROUP"]].unique()]
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
                    year_records = records_in_boundary.loc[records_in_boundary[ScoutCensus.column_labels['YEAR']] == year]
                    # beaver_sections = year_records.loc[year_records[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections']["Beavers"]]
                    # cub_sections = year_records.loc[year_records[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections']["Cubs"]]
                    # scout_sections = year_records.loc[year_records[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections']["Scouts"]]
                    # explorer_sections = year_records.loc[year_records[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections']["Explorers"]]
                    #
                    # group_records = year_records.loc[year_records[ScoutCensus.column_labels['UNIT_TYPE']] == self.census_data.CENSUS_TYPE_GROUP]
                    # explorer_waiting = year_records.loc[year_records[ScoutCensus.column_labels['UNIT_TYPE']] == self.census_data.CENSUS_TYPE_DISTRICT]
                    boundary_data[f"Waiting List-{year}"] = 0
                    for section in [section for section in ScoutCensus.column_labels['sections'].keys() if ScoutCensus.column_labels['sections'][section].get("waiting_list")]:
                        boundary_data[f"Waiting List-{year}"] += year_records[ScoutCensus.column_labels['sections'][section]["waiting_list"]].sum()

                    boundary_data[f"All-{year}"] = 0
                    for section in ScoutCensus.column_labels['sections'].keys():
                        # sections = year_records.loc[year_records[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections'][section]["type"]]
                        boundary_data[f"{section}-{year}"] = year_records[ScoutCensus.column_labels['sections'][section]["male"]].sum() + year_records[ScoutCensus.column_labels['sections'][section]["female"]].sum()
                        boundary_data[f"All-{year}"] += boundary_data[f"{section}-{year}"]

            if "awards" in options:
                eligible = records_in_boundary[ScoutCensus.column_labels['sections']["Beavers"]["top_award_eligible"]].sum()
                awards = records_in_boundary[ScoutCensus.column_labels['sections']["Beavers"]["top_award"]].sum()
                if eligible > 0:
                    boundary_data["%-" + ScoutCensus.column_labels['sections']["Beavers"]["top_award"]] = (awards * 100) / eligible
                else:
                    boundary_data["%-" + ScoutCensus.column_labels['sections']["Beavers"]["top_award"]] = np.NaN

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
            max_value = output_data["%-" + ScoutCensus.column_labels['sections']["Beavers"]["top_award"]].quantile(0.95)
            output_data["%-" + ScoutCensus.column_labels['sections']["Beavers"]["top_award"]].clip(upper=max_value, inplace=True)

        if name == "lsoa11":
            self.logger.debug(f"Output_data so far:\n{output_data}")
            data_to_merge = self.ons_data.data[["lsoa11", "imd"]].drop_duplicates("lsoa11")
            self.logger.debug(f"Merging with\n{data_to_merge}")
            output_data = pd.merge(left=output_data, right=data_to_merge , how="left", on="lsoa11", validate="1:1")
            output_data = self.country_add_IMD_decile(output_data, "E92000001")

        output_data.reset_index(drop=True, inplace=True)
        self.boundary_report[self.boundary_dict["name"]] = output_data
        return output_data

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

    def filter_set_boundaries_in_scout_area(self, column, value_list):
        records_in_scout_area = self.census_data.data.loc[self.census_data.data[column].isin(value_list)]
        boundaries_in_scout_area = records_in_scout_area[self.boundary_dict["name"]].unique()
        self.boundary_regions_data = self.boundary_regions_data.loc[self.boundary_regions_data[self.boundary_dict["codes"]["key"]].isin(boundaries_in_scout_area)]

    def filter_records_by_boundary(self):
        """Selects the records that are with the boundary specified"""
        self.filter_records(self.boundary_dict["name"], self.boundary_regions_data[self.boundary_dict["codes"]["key"]])

    def filter_boundaries_by_scout_area(self, boundary, column, value_list):
        """Filters the boundaries, to include only those boundaries which have
        Sections that satisfy the requirement that the column is in the value_list.

        :param str boundary: ONS boundary to filter on
        :param str column: Scout boundary (e.g. C_ID)
        :param list value_list: List of values in the Scout boundary
        """
        ons_value_list = self.ons_from_scout_area(boundary, column, value_list)
        self.filter_boundaries(boundary, ons_value_list)

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
        if ScoutCensus.DEFAULT_VALUE in ons_codes:
            ons_codes.remove(ScoutCensus.DEFAULT_VALUE)
        ons_codes = [code for code in ons_codes if (isinstance(code, str) or (isinstance(code, np.int32) and not np.isnan(code)))]
        self.logger.debug(f"Found clean {len(ons_codes)} {ons_code}s that match {column} in {value_list}")
        return ons_codes