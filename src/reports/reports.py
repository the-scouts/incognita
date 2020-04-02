import pandas as pd
import collections

from src.data.scout_data import ScoutData
from src.geographies.geography import Geography
from src.base import Base, time_function
from src.data.scout_census import ScoutCensus
import src.utility as utility


class Reports(Base):
    @property
    def data(self) -> pd.DataFrame:
        return self.boundary_report[self.geography.type]

    @property
    def shapefile_name(self) -> str:
        return self.geography.shapefile_name

    @property
    def shapefile_key(self) -> str:
        return self.geography.shapefile_key

    @property
    def shapefile_path(self) -> str:
        return self.geography.shapefile_path

    @property
    def geography_type(self) -> str:
        return self.geography.type

    def __init__(self, geography_name: str, scout_data_object: ScoutData, ons_pd_object=None):
        super().__init__(settings=True)

        self.ons_pd = scout_data_object.ons_pd if ons_pd_object is None else ons_pd_object  # Only needed for BOUNDARIES dict
        self.scout_data = scout_data_object  # only uses are for self.scout_data.data
        self.geography = Geography(geography_name, self.ons_pd)

        self.boundary_report = {}

    SECTION_AGES = {
        "Beavers": {"ages": ["6", "7"]},
        "Cubs": {"ages": ["8", "9"], "halves": ["10"]},
        "Scouts": {"halves": ["10"], "ages": ["11", "12", "13"]},
        "Explorers": {"ages": ["14", "15", "16", "17"]},
    }

    @time_function
    def filter_boundaries(self, field: str, value_list: list, boundary: str = "", distance=3000, near=False):

        # Check if field (i.e. scout_data column) is a census column or ONS column
        if field in self.ons_pd.fields:
            self.geography.filter_boundaries_regions_data(field, value_list, self.ons_pd)
        elif field in self.scout_data.columns:
            # Chose which filter to use for scout areas
            if near:
                self.geography.filter_boundaries_near_scout_area(self.scout_data, boundary, field, value_list, distance)
            else:
                self.geography.filter_boundaries_by_scout_area(self.scout_data, self.ons_pd, boundary, field, value_list)
        else:
            raise ValueError(f"Field value {field} not valid. Valid values are {[*self.ons_pd.fields, *self.scout_data.columns]}")

    def _ons_to_district_mapping(self, ons_code: str) -> dict:
        """Create json file, containing which scout districts are within an each ONS area, and how many ONS areas those districts are in.

        :param str ons_code: A field in the modified census report corresponding to an administrative region (lsoa11, msoa11, oslaua, osward, pcon, oscty, ctry, rgn)

        :returns None: Nothing
        """

        self.logger.debug("Creating mapping from ons boundary to scout district")

        region_type = ons_code  # Census column heading for the region geography type
        district_id_column = ScoutCensus.column_labels["id"]["DISTRICT"]

        region_ids = self.geography.geography_region_ids_mapping[self.geography.codes_map_key].dropna().drop_duplicates()

        district_ids_by_region = self.scout_data.data.loc[self.scout_data.data[region_type].isin(region_ids), [region_type, district_id_column]].dropna().drop_duplicates()
        district_ids = district_ids_by_region[district_id_column].dropna().drop_duplicates()

        region_ids_by_district = self.scout_data.data.loc[self.scout_data.data[district_id_column].isin(district_ids), [district_id_column, region_type]]
        region_ids_by_district = region_ids_by_district.loc[~(region_ids_by_district[region_type] == ScoutCensus.DEFAULT_VALUE)].dropna().drop_duplicates()

        count_regions_in_district = (
            region_ids_by_district.groupby(district_id_column).count().rename(columns={region_type: "count"})
        )  # count of how many regions the district occupies
        count_by_district_by_region = pd.merge(left=district_ids_by_region, right=count_regions_in_district, on=district_id_column)

        count_by_district_by_region = count_by_district_by_region.set_index([region_type, district_id_column])

        nested_dict = collections.defaultdict(dict)
        for keys, value in count_by_district_by_region["count"].iteritems():
            nested_dict[keys[0]][keys[1]] = value

        self.logger.debug("Finished mapping from ons boundary to district")
        return dict(nested_dict)  # Return the mapping

    @time_function
    def create_boundary_report(self, options=None, historical=False, report_name=None):
        """Produces .csv file summarising by boundary provided.

        Requires self.boundary_data to be set, preferably by :meth:scout_data._set_boundary

        :param list or None options: List of data to be included in report
        :param bool historical: Check to ensure that multiple years of data are intentional
        :param str report_name:
        """

        # Set default option set for `options`
        if options is None:
            options = ["Number of Sections", "Number of Groups", "Groups", "Section numbers", "6 to 17 numbers", "awards", "waiting list total"]

        # fmt: off
        opt_number_of_sections = \
            True if "Number of Sections" in options else False
        opt_number_of_groups = \
            True if "Number of Groups" in options else False
        opt_groups = \
            True if "Groups" in options else False
        opt_section_numbers = \
            True if "Section numbers" in options else False
        opt_6_to_17_numbers = \
            True if "6 to 17 numbers" in options else False
        opt_awards = \
            True if "awards" in options else False
        opt_waiting_list_totals = \
            True if "waiting list total" in options else False
        # fmt: on

        geog_name = self.geography.type  # e.g oslaua osward pcon lsoa11

        if not geog_name:
            raise Exception("Geography type has not been set. Try calling _set_boundary")
        else:
            self.logger.info(f"Creating report by {geog_name} with {', '.join(options)} from {len(self.scout_data.data.index)} records")

        years = self.scout_data.data["Year"].drop_duplicates().dropna().sort_values().to_list()
        if len(years) > 1:
            if historical:
                self.logger.info(f"Historical analysis from {years[0]} to {years[-1]}")
            else:
                self.logger.error(f"Historical option not selected, but multiple years of data selected ({years[0]} - {years[-1]})")

        sections_dict = ScoutCensus.column_labels["sections"]
        district_id_column = ScoutCensus.column_labels["id"]["DISTRICT"]
        award_name = sections_dict["Beavers"]["top_award"]
        award_eligible = sections_dict["Beavers"]["top_award_eligible"]
        section_cols = {section: [sections_dict[section]["male"], sections_dict[section]["female"]] for section in sections_dict.keys() if section != "Network"}

        def groups_groupby(group_series: pd.Series):
            # Used to list the groups that operate within the boundary
            # Gets all groups in the records_in_boundary dataframe
            # Removes NaN values
            # Converts all values to strings to make sure the string operations work
            # Removes leading and trailing whitespace
            # Concatenates the Series to a string with a newline separator
            # Calculates the number of groups
            group_list: pd.Series = group_series.dropna().drop_duplicates().str.strip()
            return group_list.str.cat(sep="\n"), group_list.size

        def young_people_numbers_groupby(group_df: pd.DataFrame):
            output = {}
            dicts: pd.Series = group_df.groupby(["Year"], sort=True).apply(year_groupby).to_list()
            for row in dicts:
                output = {**output, **row}
            return output

        def year_groupby(group_df: pd.DataFrame):
            census_year = group_df.name
            output = {}
            all_young_people = 0
            waiting_list = 0

            for section, cols in section_cols.items():
                total_young_people = group_df[cols].to_numpy().sum()
                all_young_people += total_young_people
                if opt_section_numbers:
                    output[f"{section}-{census_year}"] = total_young_people
                if opt_number_of_sections:
                    # TODO correct for pluralisation (e.g. Colony -> Colonys not Colonies)
                    output[f"{sections_dict[section]['type']}s-{census_year}"] = group_df[sections_dict[section]["unit_label"]].sum()
                if sections_dict[section].get("waiting_list"):
                    waiting_list += group_df[sections_dict[section]["waiting_list"]].sum()

            if opt_6_to_17_numbers:
                output[f"All-{census_year}"] = all_young_people
            if opt_waiting_list_totals:
                output[f"Waiting List-{census_year}"] = waiting_list
            return output

        def awards_groupby(group_df: pd.DataFrame, awards_data: pd.DataFrame):
            summed = group_df[[award_name, award_eligible,]].sum()
            output = summed.to_dict()
            if summed[award_eligible] > 0:
                output[f"%-{award_name}"] = (summed[award_name] * 100) / summed[award_eligible]

            # calculates the nominal QSAs per ONS region specified.
            # Divides total # of awards by the number of Scout Districts that the ONS Region is in
            code = group_df.name
            district_ids = awards_mapping.get(code, {}) if not geog_name == "D_ID" else {code: 1}
            awards_regions_data = awards_data.loc[[id for id in district_ids.keys()]].sum()

            output["QSA"] = awards_regions_data["QSA"]
            if awards_regions_data["qsa_eligible"] > 0:
                output["%-QSA"] = 100 * awards_regions_data["QSA"] / awards_regions_data["qsa_eligible"]

            return output

        def awards_per_region(district_records, district_nums):
            district_id = district_records.name
            num_ons_regions_occupied_by_district = district_nums[district_id]

            self.logger.debug(f"{district_id} in {num_ons_regions_occupied_by_district} ons boundaries")

            return {
                # QSAs achieved in district, divided by the number of regions the district is in
                "QSA": district_records["Queens_Scout_Awards"].sum() / num_ons_regions_occupied_by_district,
                # number of young people eligible to achieve the QSA in district, divided by the number of regions the district is in
                "qsa_eligible": district_records["Eligible4QSA"].sum() / num_ons_regions_occupied_by_district,
            }

        grouped_data = self.scout_data.data.groupby([geog_name], sort=False)
        dataframes = []

        if opt_groups or opt_number_of_groups:
            self.logger.debug(f"Adding group data")
            group_table: pd.Series = grouped_data[ScoutCensus.column_labels["name"]["GROUP"]].apply(groups_groupby)
            dataframes.append(pd.DataFrame(group_table.values.tolist(), columns=['Groups', 'Number of Groups']))

        if opt_section_numbers or opt_6_to_17_numbers or opt_waiting_list_totals or opt_number_of_sections:
            self.logger.debug(f"Adding young people numbers")
            sections_table = grouped_data.apply(young_people_numbers_groupby)
            dataframes.append(pd.DataFrame(sections_table.values.tolist(), index=sections_table.index))

        if opt_awards:
            # Must be self.ons_pd as BOUNDARIES dictionary changes for subclasses of ONSPostcodeDirectory
            geog_names = [self.ons_pd.BOUNDARIES[boundary]["name"] for boundary in self.ons_pd.BOUNDARIES]
            if geog_name not in geog_names:
                raise ValueError(f"{geog_name} is not a valid geography name. Valid values are {geog_names}")

            self.logger.debug(f"Creating awards mapping")
            awards_mapping = self._ons_to_district_mapping(geog_name)
            district_numbers = {district_id: num for district_dict in awards_mapping.values() for district_id, num in district_dict.items()}
            awards_per_district_per_regions = self.scout_data.data.groupby(district_id_column).apply(awards_per_region, district_numbers)
            awards_per_district_per_regions = pd.DataFrame(awards_per_district_per_regions.values.tolist(), index=awards_per_district_per_regions.index)

            self.logger.debug(f"Adding awards data")
            awards_table: pd.DataFrame = grouped_data.apply(awards_groupby, awards_per_district_per_regions)
            awards_table: pd.DataFrame = pd.DataFrame(awards_table.values.tolist(), index=awards_table.index)
            top_award = awards_table[f"%-{sections_dict['Beavers']['top_award']}"]
            max_value = top_award.quantile(0.95)
            awards_table[f"%-{sections_dict['Beavers']['top_award']}"] = top_award.clip(upper=max_value)
            dataframes.append(awards_table)

        if geog_name == "lsoa11":
            self.logger.debug(f"Adding IMD deciles")
            dataframes.append(grouped_data[["imd_decile"]].first())

        renamed_cols_dict = {self.geography.codes_map_name: "Name", self.geography.codes_map_key: geog_name}

        # areas_data holds area names and codes for each area
        # Area names column is Name and area codes column is the geography type
        areas_data: pd.DataFrame = (self.geography.geography_region_ids_mapping.copy().rename(columns=renamed_cols_dict).reset_index(drop=True))

        merged_dataframes = pd.concat(dataframes, axis=1)
        output_data = areas_data.merge(merged_dataframes, how="left", left_on=geog_name, right_index=True, sort=False)
        self.boundary_report[geog_name] = output_data

        if report_name:
            self._save_report(output_data, report_name)

        return output_data

    @time_function
    def create_uptake_report(self, report_name=None):
        """Creates a report of scouting uptake in geographic areas

        Creates an report by the boundary that has been set, requires a boundary report to already have been run.
        Requires population data by age for the specified boundary.

        :param str report_name: Name to save the report as

        :returns pd.DataFrame: Uptake data of Scouts in the boundary
        """
        geog_name: str = self.geography.type
        try:
            age_profile_path: str = self.geography.age_profile_path
            age_profile_key: str = self.geography.age_profile_key
        except KeyError:
            raise AttributeError(f"Population by age data not present for this {geog_name}")

        try:
            boundary_report: pd.DataFrame = self.boundary_report[geog_name]
        except KeyError:
            raise AttributeError("Geography report doesn't exist")

        data_types = {str(key): "Int16" for key in range(5, 26)}
        try:
            age_profile_pd = pd.read_csv(self.settings["National Statistical folder"] + age_profile_path, dtype=data_types)
        except TypeError:
            self.logger.error("Age profiles must be integers in each age category")
            raise

        # population data
        for section, ages in Reports.SECTION_AGES.items():
            age_profile_pd[f"Pop_{section}"] = age_profile_pd[ages["ages"]].sum(axis=1)
            age_profile_pd[f"Pop_{section}"] += age_profile_pd[ages["halves"]].sum(axis=1) // 2 if ages.get("halves") else 0
        age_profile_pd["Pop_All"] = age_profile_pd[[f"{age}" for age in range(6, 17 + 1)]].sum(axis=1)

        # merge population data
        cols = [f"Pop_{section}" for section in Reports.SECTION_AGES.keys()] + ["Pop_All"] + [age_profile_key]
        uptake_report = boundary_report.merge(age_profile_pd[cols], how="left", left_on=geog_name, right_on=age_profile_key, sort=False)
        del uptake_report[age_profile_key]

        years = self.scout_data.data["Year"].drop_duplicates().dropna().sort_values()

        # add uptake data
        for year in years:
            for section in Reports.SECTION_AGES.keys():
                uptake_section = uptake_report[f"{section}-{year}"] / uptake_report[f"Pop_{section}"]
                max_value = uptake_section.quantile(0.975)
                uptake_report[f"%-{section}-{year}"] = uptake_section.clip(upper=max_value)
            uptake_all = uptake_report[f"All-{year}"] / uptake_report[f"Pop_All"]
            max_value = uptake_all.quantile(0.975)
            uptake_report[f"%-All-{year}"] = uptake_all.clip(upper=max_value)
            # TODO explain 97.5th percentile clip
        # TODO check edge cases - 0 population and 0 or more scouts

        if report_name:
            self._save_report(uptake_report, report_name)

        return uptake_report

    def _save_report(self, report_data, report_name):
        utility.save_report(report_data, self.settings["Output folder"], report_name, logger=self.logger)
