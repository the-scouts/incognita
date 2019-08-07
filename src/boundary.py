import pandas as pd
import collections

from src.base import Base
from src.scout_data import ScoutData
from src.scout_census import ScoutCensus
import src.utility as utility

np = pd.np


class Boundary(Base):
    """

    :var dict Boundary.SECTION_AGES: Holds information about scout sections
    """

    SECTION_AGES = {
        'Beavers': [(6, 1), (7, 1)],
        'Cubs': [(8, 1), (9, 1), (10, 0.5)],
        'Scouts': [(10, 0.5), (11, 1), (12, 1), (13, 1)],
        'Explorers': [(14, 1), (15, 1), (16, 1), (17, 1)]
    }

    def __init__(self, geography_name, scout_data_object: ScoutData):
        super().__init__(settings=True)

        self.scout_data = scout_data_object
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

        boundaries_dict = self.ons_pd.BOUNDARIES

        if geography_name in boundaries_dict.keys():
            self.boundary_dict = boundaries_dict[geography_name]
            names_and_codes_file_path = self.boundary_dict["codes"].get("path")
            self.boundary_regions_data = pd.read_csv(
                self.ons_pd.NAMES_AND_CODES_FILE_LOCATION + names_and_codes_file_path,
                dtype={
                    self.boundary_dict["codes"]["key"]: self.boundary_dict["codes"]["key_type"],
                    self.boundary_dict["codes"]["name"]: "object"
                })
        elif geography_name in self.settings["Scout Mappings"].keys():
            self.boundary_dict = self.settings["Scout Mappings"][geography_name]
            names_and_codes_file_path = self.boundary_dict["codes"].get("path")
            self.boundary_regions_data = pd.read_csv(
                names_and_codes_file_path,
                dtype={
                    self.boundary_dict["codes"]["key"]: self.boundary_dict["codes"]["key_type"],
                    self.boundary_dict["codes"]["name"]: "object"
                })
        else:
            raise Exception(f"{geography_name} is an invalid boundary.\nValid boundaries include: {boundaries_dict.keys() + self.settings['Scout Mapping'].keys()}")

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
            raise Exception("boundary_dict has not been set, or there is no data in it")  # Has Boundary.set_boundary() been called?

        name = self.boundary_dict["name"]
        codes_key = self.boundary_dict["codes"]["key"]

        self.logger.info(f"Filtering {len(self.boundary_regions_data.index)} {name} boundaries by {field} being in {value_list}")
        # Filters ons data table if field column is in value_list. Returns ndarray of unique area codes
        boundary_subset = self.ons_pd.ons_field_mapping(field, value_list, name)
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

        district_ids_by_region = self.scout_data.data.loc[self.scout_data.data[region_type].isin(region_ids), [region_type, district_id_column, ]].dropna().drop_duplicates()
        district_ids = district_ids_by_region[district_id_column].dropna().drop_duplicates()

        region_ids_by_district = self.scout_data.data.loc[self.scout_data.data[district_id_column].isin(district_ids), [district_id_column, region_type]]
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

    def create_boundary_report(self, options=["Groups", "Section numbers", "6 to 17 numbers", "awards", "waiting list total"], historical=False, report_name=None):
        """Produces .csv file summarising by boundary provided.

        Requires self.boundary_data to be set, preferably by :meth:scout_data.set_boundary

        :param options: List of data to be included in report
        :param historical: Check to ensure that multiple years of data are intentional
        :param report_name:

        :type options: list
        :type historical: bool
        """
        # to remove IDE errors
        awards_mapping, year = None, None
        name = self.boundary_dict.get("name")  # e.g oslaua osward pcon
        sections_dict = ScoutCensus.column_labels['sections']

        if not name:
            raise Exception("boundary_dict has not been set. Try calling set_boundary")

        opt_groups = \
            True if "Groups" in options \
            else False
        opt_section_numbers = \
            True if "Section numbers" in options \
            else False
        opt_6_to_17_numbers = \
            True if "6 to 17 numbers" in options \
            else False
        opt_awards = \
            True if "awards" in options \
            else False
        opt_waiting_list_totals = \
            True if "waiting list total" in options \
            else False

        self.logger.info(f"Creating report by {name} with {', '.join(options)} from {len(self.scout_data.data.index)} records")

        min_year, max_year = utility.years_of_return(self.scout_data.data["Year"])
        years_in_data = range(min_year, max_year + 1)
        if len(years_in_data) > 1:
            if historical:
                self.logger.info(f"Historical analysis from {min_year} to {max_year}")
            else:
                self.logger.error(f"Historical option not selected, but multiple years of data selected ({min_year} - {max_year})")

        output_columns = ["Name", self.boundary_dict["name"]]

        if opt_groups:
            output_columns.append("Groups")

        for year in years_in_data:
            if opt_section_numbers:
                output_columns += [f"Beavers-{year}", f"Cubs-{year}", f"Scouts-{year}", f"Explorers-{year}"]
            if opt_6_to_17_numbers:
                output_columns.append(f"All-{year}")

        if opt_waiting_list_totals:
            output_columns += [f"Waiting List-{year}" for year in years_in_data]

        if opt_awards:
            output_columns.append("%-" + sections_dict["Beavers"]["top_award"])
            output_columns.append("QSA")
            output_columns.append("%-QSA")

            awards_mapping = self.district_mapping.get(name)
            if not awards_mapping:
                names = [self.ons_pd.BOUNDARIES[boundary]['name'] for boundary in self.ons_pd.BOUNDARIES]
                if name in names:
                    self.ons_to_district_mapping(name)
                    awards_mapping = self.district_mapping.get(name)
            else:
                self.logger.error("awards mapping successfully retrieved. can't delete if stmt")

        self.logger.debug(f"Report contains the following data:\n{output_columns}")

        output_data = pd.DataFrame(columns=output_columns)
        district_id_column = ScoutCensus.column_labels['id']["DISTRICT"]
        num_records = len(self.boundary_regions_data.index)

        for ii in range(num_records):
            self.logger.debug(f"{ii+1} out of {num_records}")
            boundary_data = {
                "Name": self.boundary_regions_data.iloc[ii, 1],
                name: self.boundary_regions_data.iloc[ii, 0],
            }
            code = boundary_data[name]

            records_in_boundary = self.scout_data.data.loc[self.scout_data.data[name] == code]
            self.logger.debug(f"Found {len(records_in_boundary.index)} records with {name} == {code}")

            if opt_groups:
                # Used to list the groups that operate within the boundary
                # Gets all groups in the records_in_boundary dataframe
                # Removes NaN values
                # Converts all values to strings to make sure the string operations work
                # Removes leading and trailing whitespace
                # Concatenates the Series to a string with a newline separator
                boundary_data["Groups"] = records_in_boundary[ScoutCensus.column_labels['name']["GROUP"]]\
                    .dropna() \
                    .astype(str)\
                    .str.strip()\
                    .str.cat(sep='\n')

            if opt_section_numbers or opt_6_to_17_numbers or opt_waiting_list_totals:
                self.logger.debug(f"Obtaining Section numbers and waiting list for {year}")
                for year in years_in_data:
                    year_records = records_in_boundary.loc[records_in_boundary[ScoutCensus.column_labels['YEAR']] == year]

                    boundary_data[f"All-{year}"] = 0
                    boundary_data[f"Waiting List-{year}"] = 0

                    for section in sections_dict.keys():
                        m_yp = year_records[sections_dict[section]["male"]].sum()
                        f_yp = year_records[sections_dict[section]["female"]].sum()

                        boundary_data[f"{section}-{year}"] = m_yp + f_yp
                        boundary_data[f"All-{year}"] += (m_yp + f_yp)

                        if sections_dict[section].get("waiting_list"):
                            boundary_data[f"Waiting List-{year}"] += year_records[sections_dict[section]["waiting_list"]].sum()

            if opt_awards:
                award_name = sections_dict["Beavers"]["top_award"]

                eligible = records_in_boundary[sections_dict["Beavers"]["top_award_eligible"]].sum()
                awards = records_in_boundary[award_name].sum()
                if eligible > 0:
                    boundary_data[f"%-{award_name}"] = (awards * 100) / eligible
                else:
                    boundary_data[f"%-{award_name}"] = np.NaN

                if name == "D_ID":
                    districts = {code: 1}
                else:
                    districts = awards_mapping.get(code, {})

                boundary_data["QSA"] = 0
                qsa_eligible = 0

                # calculates the nominal QSAs per ONS region specified.
                # Divides total # of awards by the number of Scout Districts that the ONS Region is in
                for district_id in districts.keys():  # district_id within ONS region
                    number_of_ons_regions_district_is_in = districts[district_id]
                    self.logger.debug(f"{district_id} in {number_of_ons_regions_district_is_in} ons boundaries")

                    district_records = self.scout_data.data.loc[self.scout_data.data[district_id_column] == district_id]  # Records for current district ID

                    # QSAs achieved in district, divided by the number of regions the district is in
                    boundary_data["QSA"] += district_records["Queens_Scout_Awards"].sum() / number_of_ons_regions_district_is_in

                    # number of young people eligible to achieve the QSA in district, divided by the number of regions the district is in
                    qsa_eligible += district_records["Eligible4QSA"].sum() / number_of_ons_regions_district_is_in

                if qsa_eligible > 0:
                    boundary_data["%-QSA"] = (boundary_data["QSA"] * 100) / qsa_eligible
                else:
                    boundary_data["%-QSA"] = np.NaN

            self.logger.debug(f"Adding data from {code}\n{boundary_data}")
            boundary_data_df = pd.DataFrame([boundary_data], columns=output_columns)
            output_data = pd.concat([output_data, boundary_data_df], axis=0, sort=False)

        if opt_awards:
            max_value = output_data["%-" + sections_dict["Beavers"]["top_award"]].quantile(0.95)
            output_data["%-" + sections_dict["Beavers"]["top_award"]].clip(upper=max_value, inplace=True)

        if name == "lsoa11":
            self.logger.debug(f"Output_data so far:\n{output_data}")
            unique_lsoas_with_imd = self.ons_pd.data[["lsoa11", "imd"]].drop_duplicates("lsoa11")
            self.logger.debug(f"Merging with\n{unique_lsoas_with_imd}")
            output_data = pd.merge(left=output_data, right=unique_lsoas_with_imd, how="left", on="lsoa11", validate="1:1")
            output_data = utility.country_add_imd_decile(output_data, "E92000001", self.ons_pd)

        output_data.reset_index(drop=True, inplace=True)
        self.boundary_report[self.boundary_dict["name"]] = output_data

        if report_name:
            self.save_report(output_data, report_name)

        return output_data

    def create_uptake_report(self, report_name=None):
        """Creates an report by the boundary that has been set, requires
        a boundary report to already have been run.
        Requires population data by age for the specified boundary.

        :var pd.DataFrame uptake_report:

        :returns: Uptake data of Scouts in the boundary
        :rtype: pd.DataFrame
        """
        boundary_dict = self.boundary_dict
        boundary = boundary_dict["name"]

        uptake_report: pd.DataFrame = self.boundary_report.get(boundary_dict["name"])
        section = None

        if uptake_report is None:
            raise AttributeError("Boundary report doesn't exist")

        age_profile_path = boundary_dict.get("age_profile").get("path")

        if age_profile_path:
            data_types = {str(key): "Int16" for key in range(5, 26)}
            age_profile_pd = pd.read_csv(self.settings["National Statistical folder"] + age_profile_path,
                                         dtype=data_types)
        else:
            raise Exception(f"Population by age data not present for this {boundary}")

        min_year, max_year = utility.years_of_return(self.scout_data.data["Year"])
        years_in_data = range(min_year, max_year + 1)

        # setup population columns
        pop_cols = [f"Pop_{section}" for section in Boundary.SECTION_AGES.keys()]
        pop_cols.append("Pop_All")

        # setup uptake columns
        uptake_cols = []
        for year in years_in_data:
            uptake_cols.extend([f"%-{section}-{year}" for section in Boundary.SECTION_AGES.keys()])
            uptake_cols.append(f"%-All-{year}")

        # adds all new columns with blank data (np.NaN)
        new_cols = uptake_report.columns.tolist() + pop_cols + uptake_cols
        uptake_report = uptake_report.reindex(columns=new_cols)

        for area_row in range(len(uptake_report.index)):
            boundary_row = uptake_report.iloc[area_row]
            area_code = boundary_row.at[boundary]
            area_pop = age_profile_pd.loc[age_profile_pd[boundary_dict["age_profile"]["key"]] == area_code]

            if not area_pop.empty:
                for section in Boundary.SECTION_AGES.keys():
                    section_total = 0
                    for age in Boundary.SECTION_AGES[section]:
                        section_total += area_pop.iloc[0][str(age[0])] * age[1]
                    boundary_row.at[f'Pop_{section}'] = section_total
                    for year in years_in_data:
                        col_name = f"%-{section}-{year}"
                        if section_total > 0:
                            boundary_row.at[col_name] = (boundary_row.at[f"{section}-{year}"] / section_total) * 100
                        else:
                            if boundary_row.at[f"{section}-{year}"] == 0:
                                # No Scouts and no eligible population in the geographic area
                                boundary_row.at[col_name] = np.NaN
                            else:
                                # There are Scouts but no eligible population in the geographic area
                                boundary_row.at[col_name] = 100

                section_total = area_pop.loc[[f"{age}" for age in range(6, 18)]].iloc[0].sum()
                boundary_row.at['Pop_All'] = section_total
                for year in years_in_data:
                    col_name = f"%-All-{year}"
                    if section_total > 0:
                        boundary_row.at[col_name] = (boundary_row.at[f"All-{year}"] / section_total) * 100
                    else:
                        if boundary_row.at[f'All-{year}'] == 0:
                            # No Scouts and no eligible population in the geographic area
                            boundary_row.at[col_name] = np.NaN
                        else:
                            # There are Scouts but no eligible population in the geographic area
                            boundary_row.at[col_name] = 100
            else:
                for section in Boundary.SECTION_AGES.keys():
                    boundary_row.at[f"%-{section}"] = np.NaN
                boundary_row.at[f'%-All-{section}'] = np.NaN

            uptake_report.iloc[area_row] = boundary_row

        for year in years_in_data:
            for section in Boundary.SECTION_AGES.keys():
                col_name = f"%-{section}-{year}"
                max_value = uptake_report[col_name].quantile(0.975)
                uptake_report[col_name].clip(upper=max_value, inplace=True)
            max_value = uptake_report[f"%-All-{year}"].quantile(0.975)
            uptake_report[f"%-All-{year}"].clip(upper=max_value, inplace=True)

        if report_name:
            self.save_report(uptake_report, report_name)

        return uptake_report

    def filter_set_boundaries_in_scout_area(self, column, value_list):
        records_in_scout_area = self.scout_data.data.loc[self.scout_data.data[column].isin(value_list)]
        boundaries_in_scout_area = records_in_scout_area[self.boundary_dict["name"]].unique()
        self.boundary_regions_data = self.boundary_regions_data.loc[self.boundary_regions_data[self.boundary_dict["codes"]["key"]].isin(boundaries_in_scout_area)]

    def filter_records_by_boundary(self):
        """Selects the records that are with the boundary specified"""
        self.scout_data.data = utility.filter_records(self.scout_data.data, self.boundary_dict["name"], self.boundary_regions_data[self.boundary_dict["codes"]["key"]], self.logger)

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
        self.logger.info(f"Finding the ons areas that exist with {column} in {value_list}")

        records = self.scout_data.data.loc[self.scout_data.data[column].isin(value_list)]
        self.logger.debug(f"Found {len(records.index)} records that match {column} in {value_list}")

        ons_codes = records[ons_code].drop_duplicates().dropna()
        ons_codes = ons_codes[ons_codes != ScoutCensus.DEFAULT_VALUE]
        self.logger.debug(f"Found raw {len(ons_codes)} {ons_code}s that match {column} in {value_list}")

        ons_codes = [code for code in ons_codes if (isinstance(code, str) or (isinstance(code, np.int32)))]
        self.logger.debug(f"Found clean {len(ons_codes)} {ons_code}s that match {column} in {value_list}")

        return ons_codes

    def save_report(self, report_data, report_name):
        utility.save_report(report_data, self.settings["Output folder"], report_name, logger=self.logger)
