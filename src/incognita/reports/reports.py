from __future__ import annotations

import collections
from typing import TYPE_CHECKING

import pandas as pd

from incognita import utility
from incognita.data.scout_census import ScoutCensus
from incognita.data.scout_data import ScoutData
from incognita.geographies.geography import Geography
from incognita.logger import logger
from incognita.utility import time_function

if TYPE_CHECKING:
    from pathlib import Path

    from incognita.data.ons_pd import ONSPostcodeDirectory


class Reports:
    @property
    def data(self) -> pd.DataFrame:
        return self.boundary_report

    @property
    def shapefile_name(self) -> str:
        return self.geography.shapefile_name

    @property
    def shapefile_key(self) -> str:
        return self.geography.shapefile_key

    @property
    def shapefile_path(self) -> Path:
        return self.geography.shapefile_path

    @property
    def geography_type(self) -> str:
        return self.geography.type

    def __init__(self, geography_name: str, scout_data_object: ScoutData, ons_pd_object: ONSPostcodeDirectory = None):
        self.ons_pd = scout_data_object.ons_pd if ons_pd_object is None else ons_pd_object  # Only needed for BOUNDARIES dict
        self.scout_data = scout_data_object  # only uses are for self.scout_data.data
        self.geography = Geography(geography_name, self.ons_pd)

        self.boundary_report = None

    SECTION_AGES = {
        "Beavers": {"ages": ["6", "7"]},
        "Cubs": {"ages": ["8", "9"], "halves": ["10"]},
        "Scouts": {"halves": ["10"], "ages": ["11", "12", "13"]},
        "Explorers": {"ages": ["14", "15", "16", "17"]},
    }

    @time_function
    def add_shapefile_data(self):
        import copy

        logger.info("Adding shapefile data")
        # self.scout_data = copy.copy(self.scout_data)
        # self.scout_data.data = self.scout_data.data.copy()

        self.scout_data.add_shape_data(self.shapefile_key, path=self.shapefile_path)
        self.scout_data.data = self.scout_data.data.rename(columns={self.shapefile_key: self.geography_type})

    @time_function
    def filter_boundaries(self, field: str, value_list: list, boundary: str = "", distance: int = 3000, near: bool = False):

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

        logger.debug("Creating mapping from ons boundary to scout district")

        region_type = ons_code  # Census column heading for the region geography type
        district_id_column = ScoutCensus.column_labels["id"]["DISTRICT"]

        region_ids = self.geography.geography_region_ids_mapping[self.geography.codes_map_key].dropna().drop_duplicates()

        district_ids_by_region = self.scout_data.data.loc[self.scout_data.data[region_type].isin(region_ids), [region_type, district_id_column]].dropna().drop_duplicates()
        district_ids = district_ids_by_region[district_id_column].dropna().drop_duplicates()

        region_ids_by_district = self.scout_data.data.loc[self.scout_data.data[district_id_column].isin(district_ids), [district_id_column, region_type]]
        region_ids_by_district = region_ids_by_district.loc[~(region_ids_by_district[region_type] == ScoutCensus.DEFAULT_VALUE)].dropna().drop_duplicates()

        # count of how many regions the district occupies:
        count_regions_in_district = region_ids_by_district.groupby(district_id_column).count().rename(columns={region_type: "count"})

        count_by_district_by_region = pd.merge(left=district_ids_by_region, right=count_regions_in_district, on=district_id_column)

        count_by_district_by_region = count_by_district_by_region.set_index([region_type, district_id_column])

        count_col: pd.Series = count_by_district_by_region["count"]
        nested_dict = collections.defaultdict(dict)
        for keys, value in count_col.iteritems():
            nested_dict[keys[0]][keys[1]] = value

        logger.debug("Finished mapping from ons boundary to district")
        return dict(nested_dict)  # Return the mapping

    @time_function
    def create_boundary_report(self, options: list = None, historical: bool = False, report_name: str = None) -> pd.DataFrame:
        """Produces .csv file summarising by boundary provided.

        Requires self.boundary_data to be set, preferably by :meth:scout_data._set_boundary

        :param list options: List of data to be included in report
        :param bool historical: Check to ensure that multiple years of data are intentional
        :param str report_name:
        """

        # Set default option set for `options`
        if options is None:
            options = {"Number of Sections", "Number of Groups", "Groups", "Section numbers", "6 to 17 numbers", "awards", "waiting list total"}
        else:
            options = set(options)

        # fmt: off
        opt_number_of_sections = "Number of Sections" in options
        opt_number_of_groups = "Number of Groups" in options
        opt_groups = "Groups" in options
        opt_section_numbers = "Section numbers" in options
        opt_6_to_17_numbers = "6 to 17 numbers" in options
        opt_awards = "awards" in options
        opt_waiting_list_totals = "waiting list total" in options
        opt_adult_numbers = "Adult numbers" in options
        # fmt: on

        geog_name = self.geography_type  # e.g oslaua osward pcon lsoa11

        if not geog_name:
            raise Exception("Geography type has not been set. Try calling _set_boundary")
        else:
            logger.info(f"Creating report by {geog_name} with {', '.join(options)} from {len(self.scout_data.data.index)} records")

        years = self.scout_data.data["Year"].drop_duplicates().dropna().sort_values().to_list()
        if len(years) > 1:
            if historical:
                logger.info(f"Historical analysis from {years[0]} to {years[-1]}")
            else:
                logger.error(f"Historical option not selected, but multiple years of data selected ({years[0]} - {years[-1]})")

        sections_dict = ScoutCensus.column_labels["sections"]
        district_id_column = ScoutCensus.column_labels["id"]["DISTRICT"]
        award_name = sections_dict["Beavers"]["top_award"]
        award_eligible = sections_dict["Beavers"]["top_award_eligible"]
        section_cols = [sect for sect in sections_dict.keys() if sect != "Network"]

        def _groups_groupby(group_series: pd.Series) -> (str, int):
            # Used to list the groups that operate within the boundary
            # Gets all groups in the records_in_boundary dataframe
            # Removes NaN values
            # Converts all values to strings to make sure the string operations work
            # Removes leading and trailing whitespace
            # Concatenates the Series to a string with a newline separator
            # Calculates the number of groups
            group_list: pd.Series = group_series.dropna().drop_duplicates().str.strip()
            return group_list.str.cat(sep="\n"), group_list.size

        def _young_people_numbers_groupby(group_df: pd.DataFrame) -> dict:
            output = {}
            dicts: pd.Series = group_df.groupby(["Year"], sort=True).apply(_year_groupby).to_list()
            for row in dicts:
                output |= row
            return output

        def _year_groupby(group_df: pd.DataFrame) -> dict:
            census_year = group_df.name
            output = {}
            all_young_people = 0
            waiting_list = 0

            for section in section_cols:
                total_young_people = group_df[sections_dict[section]["total"]].sum()
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
            if opt_adult_numbers:
                output[f"Adults-{census_year}"] = group_df[["Leaders", "AssistantLeaders", "SectAssistants", "OtherAdults"]].sum().sum()
            return output

        def _awards_groupby(group_df: pd.DataFrame, awards_data: pd.DataFrame) -> dict:
            summed = group_df[[award_name, award_eligible]].sum()
            output = summed.to_dict()
            if summed[award_eligible] > 0:
                output[f"%-{award_name}"] = (summed[award_name] * 100) / summed[award_eligible]

            # calculates the nominal QSAs per ONS region specified.
            # Divides total # of awards by the number of Scout Districts that the ONS Region is in
            code = group_df.name
            district_ids = awards_mapping.get(code, {}) if not geog_name == "D_ID" else {code: 1}
            awards_regions_data = awards_data.loc[[d_id for d_id in district_ids.keys()]].sum()

            output["QSA"] = awards_regions_data["QSA"]
            if awards_regions_data["qsa_eligible"] > 0:
                output["%-QSA"] = 100 * awards_regions_data["QSA"] / awards_regions_data["qsa_eligible"]

            return output

        def _awards_per_region(district_records, district_nums) -> dict:
            district_id = district_records.name
            num_ons_regions_occupied_by_district = district_nums[district_id]

            logger.debug(f"{district_id} in {num_ons_regions_occupied_by_district} ons boundaries")

            return {
                # QSAs achieved in district, divided by the number of regions the district is in
                "QSA": district_records["Queens_Scout_Awards"].sum() / num_ons_regions_occupied_by_district,
                # number of young people eligible to achieve the QSA in district, divided by the number of regions the district is in
                "qsa_eligible": district_records["Eligible4QSA"].sum() / num_ons_regions_occupied_by_district,
            }

        # TODO pandas > 1.1 move to new dropna=False groupby
        self.scout_data.data[[geog_name]] = self.scout_data.data[[geog_name]].fillna("DUMMY")

        # Check that our pivot keeps the total membership constant
        yp_cols = ["Beavers_total", "Cubs_total", "Scouts_total", "Explorers_total"]
        grouped_data = self.scout_data.data.groupby([geog_name], sort=False)
        assert int(self.scout_data.data[yp_cols].sum().sum()) == int(grouped_data[yp_cols].sum().sum().sum())
        dataframes = []

        if opt_groups or opt_number_of_groups:
            logger.debug(f"Adding group data")
            group_table: pd.Series = grouped_data[ScoutCensus.column_labels["name"]["GROUP"]].apply(_groups_groupby)
            dataframes.append(pd.DataFrame(group_table.values.tolist(), columns=["Groups", "Number of Groups"]))

        if opt_section_numbers or opt_6_to_17_numbers or opt_waiting_list_totals or opt_number_of_sections:
            logger.debug(f"Adding young people numbers")
            sections_table = grouped_data.apply(_young_people_numbers_groupby)
            dataframes.append(pd.DataFrame(sections_table.values.tolist(), index=sections_table.index))

        if opt_awards:
            # Must be self.ons_pd as BOUNDARIES dictionary changes for subclasses of ONSPostcodeDirectory
            geog_names = [self.ons_pd.BOUNDARIES[boundary]["name"] for boundary in self.ons_pd.BOUNDARIES]
            if geog_name not in geog_names:
                raise ValueError(f"{geog_name} is not a valid geography name. Valid values are {geog_names}")

            logger.debug(f"Creating awards mapping")
            awards_mapping = self._ons_to_district_mapping(geog_name)
            district_numbers = {district_id: num for district_dict in awards_mapping.values() for district_id, num in district_dict.items()}
            awards_per_district_per_regions = self.scout_data.data.groupby(district_id_column).apply(_awards_per_region, district_numbers)
            awards_per_district_per_regions = pd.DataFrame(awards_per_district_per_regions.values.tolist(), index=awards_per_district_per_regions.index)

            logger.debug(f"Adding awards data")
            awards_table: pd.DataFrame = grouped_data.apply(_awards_groupby, awards_per_district_per_regions)
            awards_table: pd.DataFrame = pd.DataFrame(awards_table.values.tolist(), index=awards_table.index)
            top_award = awards_table[f"%-{sections_dict['Beavers']['top_award']}"]
            max_value = top_award.quantile(0.95)
            awards_table[f"%-{sections_dict['Beavers']['top_award']}"] = top_award.clip(upper=max_value)
            dataframes.append(awards_table)

        renamed_cols_dict = {self.geography.codes_map_name: "Name", self.geography.codes_map_key: geog_name}

        # areas_data holds area names and codes for each area
        # Area names column is Name and area codes column is the geography type
        areas_data: pd.DataFrame = self.geography.geography_region_ids_mapping.copy().rename(columns=renamed_cols_dict).reset_index(drop=True)

        # TODO find a way to keep DUMMY geography coding
        merged_dataframes = pd.concat(dataframes, axis=1)
        output_data = areas_data.merge(merged_dataframes, how="left", left_on=geog_name, right_index=True, sort=False)

        if geog_name == "lsoa11":
            logger.debug(f"Adding IMD deciles")
            output_data = output_data.merge(self.ons_pd.data[["lsoa11", "imd_decile"]], how="left", on="lsoa11")

        self.boundary_report = output_data

        if report_name:
            self._save_report(output_data, report_name)

        return output_data

    @time_function
    def create_uptake_report(self, report_name: str = None) -> pd.DataFrame:
        """Creates a report of scouting uptake in geographic areas

        Creates an report by the boundary that has been set, requires a boundary report to already have been run.
        Requires population data by age for the specified boundary.

        :param str report_name: Name to save the report as

        :returns pd.DataFrame: Uptake data of Scouts in the boundary
        """
        geog_name = self.geography_type
        try:
            age_profile_path = self.geography.age_profile_path
            age_profile_key = self.geography.age_profile_key
        except KeyError:
            raise AttributeError(f"Population by age data not present for this {geog_name}")

        try:
            boundary_report: pd.DataFrame = self.boundary_report
        except KeyError:
            raise AttributeError("Geography report doesn't exist")

        data_types = {str(key): "Int16" for key in range(5, 26)}
        try:
            age_profile_pd = pd.read_csv(age_profile_path, dtype=data_types)
        except TypeError:
            logger.error("Age profiles must be integers in each age category")
            raise

        # population data
        for section, ages in Reports.SECTION_AGES.items():
            section_population = age_profile_pd[ages["ages"]].sum(axis=1)
            section_population += age_profile_pd[ages["halves"]].sum(axis=1) // 2 if ages.get("halves") else 0
            age_profile_pd[f"Pop_{section}"] = section_population.astype("UInt32")
        age_profile_pd["Pop_All"] = age_profile_pd[[f"{age}" for age in range(6, 17 + 1)]].sum(axis=1).astype("UInt32")

        # merge population data
        cols = [age_profile_key] + [f"Pop_{section}" for section in Reports.SECTION_AGES.keys()] + ["Pop_All"]
        reduced_age_profile_pd = age_profile_pd[cols]

        # Pivot age profile to current geography type if needed
        if self.geography.age_profile_pivot and self.geography.age_profile_pivot != geog_name:
            pivot_key = self.geography.age_profile_pivot

            ons_data_subset = self.ons_pd.data[[geog_name, pivot_key]]
            merged_age_profile = reduced_age_profile_pd.merge(ons_data_subset, how="left", left_on=age_profile_key, right_on=pivot_key).drop(pivot_key, axis=1)
            merged_age_profile_no_na = merged_age_profile.dropna(subset=[geog_name])
            pivoted_age_profile = merged_age_profile_no_na.groupby(geog_name).sum().astype("UInt32")

            # Check we did not accidentally expand the population!
            # assert merged_age_profile["Pop_All"].sum() == reduced_age_profile_pd["Pop_All"].sum()  # this will fail
            assert pivoted_age_profile["Pop_All"].sum() == merged_age_profile_no_na["Pop_All"].sum()
            uptake_report = boundary_report.merge(pivoted_age_profile, how="left", left_on=geog_name, right_index=True, sort=False)
        else:
            uptake_report = boundary_report.merge(reduced_age_profile_pd, how="left", left_on=geog_name, right_on=age_profile_key, sort=False)
            del uptake_report[age_profile_key]

        years = self.scout_data.data["Year"].drop_duplicates().dropna().sort_values()

        # add uptake data
        for year in years:
            # clip here as unexpectedly large values throw off the scale bars.
            # TODO normalise unexpectedly large values so that we don't need to clip
            for section in Reports.SECTION_AGES.keys():
                uptake_section = 100 * uptake_report[f"{section}-{year}"] / uptake_report[f"Pop_{section}"]
                max_value = uptake_section.quantile(0.975)
                uptake_report[f"%-{section}-{year}"] = uptake_section.clip(upper=max_value)
            uptake_all = 100 * uptake_report[f"All-{year}"] / uptake_report[f"Pop_All"]
            max_value = uptake_all.quantile(0.975)
            uptake_report[f"%-All-{year}"] = uptake_all.clip(upper=max_value)
            # TODO explain 97.5th percentile clip
        # TODO check edge cases - 0 population and 0 or more scouts

        if report_name:
            self._save_report(uptake_report, report_name)

        self.boundary_report = uptake_report
        return uptake_report

    def _save_report(self, report_data: pd.DataFrame, report_name: str):
        utility.save_report(report_data, report_name)
