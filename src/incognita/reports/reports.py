from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import pandas as pd

from incognita.data import scout_census
from incognita.data.scout_data import ScoutData
from incognita.geographies.geography import Geography
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import utility
from incognita.utility.utility import time_function

if TYPE_CHECKING:
    from incognita.data.ons_pd import ONSPostcodeDirectory


class Reports:
    @property
    def data(self) -> pd.DataFrame:
        return self.boundary_report

    def __init__(self, geography_name: str, scout_data: ScoutData):
        self.ons_pd: ONSPostcodeDirectory = scout_data.ons_pd  # Only needed for BOUNDARIES dict
        self.scout_data = scout_data  # only uses are for self.scout_data.data
        self.geography = Geography(geography_name, self.ons_pd)

        self.boundary_report = None

        self.ons_pd_data: Optional[pd.DataFrame] = None

    SECTION_AGES = {
        "Beavers": {"ages": ["6", "7"]},
        "Cubs": {"ages": ["8", "9"], "halves": ["10"]},
        "Scouts": {"halves": ["10"], "ages": ["11", "12", "13"]},
        "Explorers": {"ages": ["14", "15", "16", "17"]},
    }

    @time_function
    def add_shapefile_data(self) -> None:

        logger.info("Adding shapefile data")
        # self.scout_data = copy.copy(self.scout_data)
        # self.scout_data.census_data = self.scout_data.census_data.copy()

        shapefile_key = self.geography.metadata.shapefile.key
        self.scout_data.add_shape_data(shapefile_key, path=self.geography.metadata.shapefile.path)
        self.scout_data.census_data = self.scout_data.census_data.rename(columns={shapefile_key: self.geography.metadata.key})

    @time_function
    def filter_boundaries(self, field: str, value_list: set[str], boundary: str = "", distance: int = 0) -> pd.DataFrame:
        """Keep all geographic boundaries where the value of `field` is in the given value list.

        The geographic boundary is specified by `boundary`, or if not given,
        `field` is assumed to be a geographic boundary.

        Effectively, this remaps the values in value_list to a given
        geography and keeps them, with field as the origin and boundary as the
        destination keys.

        """
        # Check if field (i.e. scout_data column) is a census column or ONS column
        valid_filter_columns = self.ons_pd.fields | self.scout_data.filterable_columns
        if field not in valid_filter_columns:
            raise ValueError(f"Field value {field} not valid. Valid values are {valid_filter_columns}")
        if field in self.ons_pd.fields:
            return self.geography.filter_ons_boundaries(field, value_list)
        if distance:
            return self.geography.filter_boundaries_near_scout_area(self.scout_data, boundary, field, value_list, distance)
        return self.geography.filter_boundaries_by_scout_area(self.scout_data, boundary, field, value_list)

    def _ons_to_district_mapping(self, ons_code: str) -> dict:
        """Create json file, containing which scout districts are within an each ONS area, and how many ONS areas those districts are in.

        Args:
            ons_code: A field in the modified census report corresponding to an administrative region (lsoa11, msoa11, oslaua, osward, pcon, oscty, ctry, rgn)

        """

        logger.debug("Creating mapping from ons boundary to scout district")

        region_type = ons_code  # Census column heading for the region geography type
        district_id_column = scout_census.column_labels.id.DISTRICT
        census_data = self.scout_data.census_data

        region_ids = self.geography.boundary_codes["codes"].dropna().drop_duplicates()

        district_ids_by_region = census_data.loc[census_data[region_type].isin(region_ids), [region_type, district_id_column]].dropna().drop_duplicates()
        district_ids = district_ids_by_region[district_id_column].dropna().drop_duplicates()

        region_ids_by_district = census_data.loc[census_data[district_id_column].isin(district_ids), [district_id_column, region_type]]
        region_ids_by_district = region_ids_by_district.loc[~(region_ids_by_district[region_type] == scout_census.DEFAULT_VALUE)].dropna().drop_duplicates()

        # count of how many regions the district occupies:
        count_regions_in_district = region_ids_by_district.groupby(district_id_column).count().rename(columns={region_type: "count"})

        count_by_district_by_region = pd.merge(left=district_ids_by_region, right=count_regions_in_district, on=district_id_column)

        count_by_district_by_region = count_by_district_by_region.set_index([region_type, district_id_column])

        count_col: pd.Series = count_by_district_by_region["count"]
        nested_dict = {}
        for (region_id, district_id), value in count_col.iteritems():
            nested_dict.setdefault(region_id, {})[district_id] = value

        logger.debug("Finished mapping from ons boundary to district")
        return dict(nested_dict)  # Return the mapping

    @time_function
    def create_boundary_report(self, options: set[str] = None, historical: bool = False, report_name: str = None) -> pd.DataFrame:
        """Produces .csv file summarising by boundary provided.

        Requires self.boundary_data to be set, preferably by :meth:scout_data._set_boundary

        Args:
            options: List of data to be included in report
            historical: Check to ensure that multiple years of data are intentional
            report_name:

        """

        # Set default option set for `options`
        if options is None:
            options = {"Number of Sections", "Number of Groups", "Groups", "Section numbers", "6 to 17 numbers", "awards", "waiting list total"}

        opt_number_of_sections = "Number of Sections" in options
        opt_number_of_groups = "Number of Groups" in options
        opt_groups = "Groups" in options
        opt_section_numbers = "Section numbers" in options
        opt_6_to_17_numbers = "6 to 17 numbers" in options
        opt_awards = "awards" in options
        opt_waiting_list_totals = "waiting list total" in options
        opt_adult_numbers = "Adult numbers" in options

        geog_name = self.geography.metadata.key  # e.g oslaua osward pcon lsoa11
        logger.info(f"Creating report by {geog_name} with {', '.join(options)} from {len(self.scout_data.census_data.index)} records")

        years = self.scout_data.census_data["Year"].drop_duplicates().dropna().sort_values().to_list()
        if len(years) > 1:
            if historical:
                logger.info(f"Historical analysis from {years[0]} to {years[-1]}")
            else:
                logger.error(f"Historical option not selected, but multiple years of data selected ({years[0]} - {years[-1]})")

        sections_model = scout_census.column_labels.sections
        district_id_column = scout_census.column_labels.id.DISTRICT
        award_name = sections_model.Beavers.top_award
        award_eligible = sections_model.Beavers.top_award_eligible

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
        self.scout_data.census_data[[geog_name]] = self.scout_data.census_data[[geog_name]].fillna("DUMMY")

        total_cols = [section_model.total for section_name, section_model in sections_model if section_name != "Network"]
        waiting_cols = [section_model.waiting_list for section_name, section_model in sections_model if section_name != "Network"]
        self.scout_data.census_data["All"] = self.scout_data.census_data[total_cols].sum(axis=1).astype("Int32")
        self.scout_data.census_data["Waiting List"] = self.scout_data.census_data[waiting_cols].sum(axis=1).astype("Int32")
        self.scout_data.census_data["Adults"] = self.scout_data.census_data[["Leaders", "AssistantLeaders", "SectAssistants", "OtherAdults"]].sum(axis=1).astype("Int32")

        # Check that our pivot keeps the total membership constant
        yp_cols = ["Beavers_total", "Cubs_total", "Scouts_total", "Explorers_total"]
        grouped_data = self.scout_data.census_data.groupby([geog_name], sort=False)
        assert int(self.scout_data.census_data[yp_cols].sum().sum()) == int(grouped_data[yp_cols].sum().sum().sum())
        dataframes = []

        if opt_groups or opt_number_of_groups:
            # Used to list the groups that operate within the boundary.
            # Gets all groups in the census_data dataframe and calculates the
            # number of groups.
            logger.debug(f"Adding group data")
            groups = self.scout_data.census_data[[geog_name, scout_census.column_labels.name.GROUP]].copy()
            groups[scout_census.column_labels.name.GROUP] = groups[scout_census.column_labels.name.GROUP].str.strip()
            g = groups.drop_duplicates().dropna().groupby([geog_name], sort=False)[scout_census.column_labels.name.GROUP]
            dataframes.append(pd.DataFrame({"Groups": g.unique().apply("\n".join), "Number of Groups": g.nunique(dropna=True)}))

        if opt_section_numbers or opt_6_to_17_numbers or opt_waiting_list_totals or opt_number_of_sections:
            logger.debug(f"Adding young people numbers")
            metric_cols = []
            rename = {}
            if opt_section_numbers:
                metric_cols += [section_model.total for section_name, section_model in sections_model if section_name != "Network"]
            if opt_number_of_sections:
                # TODO correct for pluralisation (e.g. Colony -> Colonys not Colonies)
                metric_cols += [section_model.unit_label for section_name, section_model in sections_model if section_name != "Network"]
                rename |= {section_model.unit_label: f"{section_model.type}s" for section_name, section_model in sections_model if section_name != "Network"}
            if opt_6_to_17_numbers:
                metric_cols += ["All"]
            if opt_waiting_list_totals:
                metric_cols += ["Waiting List"]
            if opt_adult_numbers:
                metric_cols += ["Adults"]
            agg = self.scout_data.census_data.groupby([geog_name, "Year"], sort=True)[metric_cols].sum()
            agg = agg.unstack().sort_index()
            agg.columns = [f"{rename.get(key, key)}-{census_year}".replace("_total", "") for key, census_year in agg.columns]
            dataframes.append(agg)

        if opt_awards:
            # Must be self.ons_pd as BOUNDARIES dictionary changes for subclasses of ONSPostcodeDirectory
            geog_names = {boundary_model.key for boundary_model in self.ons_pd.BOUNDARIES.values()}
            if geog_name not in geog_names:
                raise ValueError(f"{geog_name} is not a valid geography name. Valid values are {geog_names}")

            logger.debug(f"Creating awards mapping")
            awards_mapping = self._ons_to_district_mapping(geog_name)
            district_numbers = {district_id: num for district_dict in awards_mapping.values() for district_id, num in district_dict.items()}
            awards_per_district_per_regions = self.scout_data.census_data.groupby(district_id_column).apply(_awards_per_region, district_numbers)
            awards_per_district_per_regions = pd.DataFrame(awards_per_district_per_regions.values.tolist(), index=awards_per_district_per_regions.index)

            logger.debug(f"Adding awards data")
            awards_table: pd.DataFrame = grouped_data.apply(_awards_groupby, awards_per_district_per_regions)
            awards_table: pd.DataFrame = pd.DataFrame(awards_table.values.tolist(), index=awards_table.index)
            top_award = awards_table[f"%-{sections_model.Beavers.top_award}"]
            max_value = top_award.quantile(0.95)
            awards_table[f"%-{sections_model.Beavers.top_award}"] = top_award.clip(upper=max_value)
            dataframes.append(awards_table)

        # TODO find a way to keep DUMMY geography coding
        output_data: pd.DataFrame = self.geography.boundary_codes.reset_index(drop=True).copy()
        output_data = output_data.merge(pd.concat(dataframes, axis=1), how="left", left_on="codes", right_index=True, sort=False)

        if geog_name == "lsoa11":
            logger.debug(f"Loading ONS postcode data.")
            if self.ons_pd_data is None:
                self.ons_pd_data = pd.read_feather(config.SETTINGS.ons_pd.reduced)

            logger.debug(f"Adding IMD deciles")
            output_data = output_data.merge(self.ons_pd_data[["lsoa11", "imd_decile"]], how="left", left_on="codes", right_on="lsoa11")

        self.boundary_report = output_data

        if report_name:
            utility.save_report(output_data, report_name)

        return output_data

    @time_function
    def create_uptake_report(self, report_name: str = None) -> pd.DataFrame:
        """Creates a report of scouting uptake in geographic areas

        Creates an report by the boundary that has been set, requires a boundary report to already have been run.
        Requires population data by age for the specified boundary.

        Args:
            report_name: Name to save the report as

        Returns:
            Uptake data of Scouts in the boundary

        """
        geog_name = self.geography.metadata.key
        try:
            age_profile_path = config.SETTINGS.folders.national_statistical / self.geography.metadata.age_profile.path
            age_profile_key = self.geography.metadata.age_profile.key
        except KeyError:
            raise AttributeError(f"Population by age data not present for this {geog_name}")

        if self.boundary_report is None:
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
        pivot_key = self.geography.metadata.age_profile.pivot_key
        if pivot_key and pivot_key != geog_name:
            logger.debug(f"Loading ONS postcode data.")
            if self.ons_pd_data is None:
                self.ons_pd_data = pd.read_feather(config.SETTINGS.ons_pd.reduced)

            ons_data_subset = self.ons_pd_data[[geog_name, pivot_key]]
            merged_age_profile = reduced_age_profile_pd.merge(ons_data_subset, how="left", left_on=age_profile_key, right_on=pivot_key).drop(pivot_key, axis=1)
            merged_age_profile_no_na = merged_age_profile.dropna(subset=[geog_name])
            pivoted_age_profile = merged_age_profile_no_na.groupby(geog_name).sum().astype("UInt32")

            # Check we did not accidentally expand the population!
            # assert merged_age_profile["Pop_All"].sum() == reduced_age_profile_pd["Pop_All"].sum()  # this will fail
            assert pivoted_age_profile["Pop_All"].sum() == merged_age_profile_no_na["Pop_All"].sum()
            uptake_report = self.boundary_report.merge(pivoted_age_profile, how="left", left_on="codes", right_index=True, sort=False)
        else:
            uptake_report = self.boundary_report.merge(reduced_age_profile_pd, how="left", left_on="codes", right_on=age_profile_key, sort=False)
            del uptake_report[age_profile_key]

        years = self.scout_data.census_data["Year"].drop_duplicates().dropna().sort_values()

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
            utility.save_report(uptake_report, report_name)

        self.boundary_report = uptake_report
        return uptake_report
