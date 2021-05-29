from __future__ import annotations

import pandas as pd

from incognita.data import scout_census
from incognita.data.ons_pd import ONS_POSTCODE_DIRECTORY_MAY_20 as ONS_PD
from incognita.logger import logger
from incognita.utility import report_io


class HistorySummary:
    def __init__(self, census_data: pd.DataFrame):
        self.census_data = census_data

    def group_history_summary(self, years: list, report_name: str = None) -> pd.DataFrame:
        logger.info("Beginning group_history_summary")
        report = self._history_summary(years, "Group ID", scout_census.column_labels.id.GROUP, unit_type="Group")
        if report_name:
            report_io.save_report(report, report_name)
        return report

    def section_history_summary(self, years: list, report_name: str = None) -> pd.DataFrame:
        # Works effectively for years after 2017
        logger.info("Beginning section_history_summary")
        report = self._history_summary(years, "compass ID", "compass")
        if report_name:
            report_io.save_report(report, report_name)
        return report

    def _history_summary(self, years: list, id_name: str, census_col: str, unit_type: str = None) -> pd.DataFrame:
        sections_model = scout_census.column_labels.sections

        # Must have imd scores and deciles already in census_postcode_data.
        logger.info(f"Grouping data by {census_col}")
        data = self.census_data
        grouped_data = data.groupby([census_col], sort=False)

        # create dataframe of all constant values, which happen to all be scout org hierachy related
        logger.info(f"Creating table of Scout organisational data")
        scout_org_cols = [
            census_col,
            scout_census.column_labels.UNIT_TYPE,
            scout_census.column_labels.name.GROUP,
            scout_census.column_labels.name.DISTRICT,
            scout_census.column_labels.name.COUNTY,
            scout_census.column_labels.name.REGION,
            scout_census.column_labels.name.COUNTRY,
        ]
        scout_org_data = grouped_data[scout_org_cols].first()

        # if unit_types is set the series should be overwritten with that value
        # this is for manually overwriting the unit type
        if unit_type:
            scout_org_data[scout_census.column_labels.UNIT_TYPE] = unit_type

        logger.info(f"Finding opening and closing years")
        # Takes the year column from the grouped_data object resulting in a SeriesGroupBy
        # Applies the years_of_return method to get max and min years for each series in the object
        # Applies to a Series, unpacking the returned tuples to individual series
        # Casts to an object dtype as later we introduce text.
        years_return = grouped_data["Year"].agg(lambda series: (series.min(), series.max())).apply(pd.Series).astype(object)

        # If open in the first year of data or last year of data, add an explanatory note that the limits are not certain
        years_return[0] = years_return[0].mask(years_return[0] == years[0], f"{years[0]} or before")
        years_return[1] = years_return[1].mask(years_return[1] == years[-1], f"Open in {years[-1]}")
        years_return.columns = ["min_year", "max_year"]

        # for each dataframe in the groupby object, find the lowest IMD rank from the latest year, and return
        # values associated with that rank. This requires IMD decile to have been added beforehand
        imd_cols = ["clean_postcode", "ctry", "imd", "imd_decile"]

        def _imd_groupby(df: pd.DataFrame):
            # To find the postcode and IMD for a range of Sections and Group records across several years.
            # Find the most recent year, and then choose the Postcode with the lowest IMD Rank.
            most_recent_year = df["Year"].max()
            df["imd"] = df["imd"].where(df["imd"] > 0)  # Only keep values where IMD rank is greater than 0
            most_recent_records = df[df["Year"] == most_recent_year]  # The latest year of records
            min_imd_records = most_recent_records.nsmallest(1, "imd")  # get smallest imd rank
            return min_imd_records[imd_cols]

        # per year open, record the total young people per section and the number of adults
        # uses a nested groupby for efficiency
        sections_list = [section_name for section_name, section_model in sections_model if section_name not in {"Explorers", "Network"}]
        adult_cols = ["Leaders", "SectAssistants", "OtherAdults"]  # TODO re add

        def _year_groupby(df):
            dicts: pd.Series = df.groupby(["Year"], sort=True).apply(_section_groupby).to_list()
            output = {}
            for row in dicts:
                output |= row
            return output

        def _section_groupby(df):
            census_year = df.name
            output = {}
            for section in sections_list:
                output[f"{section}-{census_year}"] = df[getattr(scout_census.column_labels.sections, section).total].sum()
            output[f"Adults-{census_year}"] = df[adult_cols].to_numpy().sum()
            return output

        # For each year, calculate and add number of beavers, cubs, scouts.  Explorers, Network deliberately omitted.
        # Expand series of dictionaries to a dataframe with the same index
        logger.info(f"Creating table of members by section and adults by year")
        member_numbers_table = grouped_data.apply(_year_groupby)
        member_numbers_table = pd.DataFrame(member_numbers_table.to_list(), index=member_numbers_table.index)

        # apply the imd function and map country codes to country names
        logger.info(f"Creating table of IMD data and postcodes")
        imd_table = grouped_data.apply(_imd_groupby).droplevel(1)
        imd_table["IMD Country"] = imd_table["ctry"].map(ONS_PD.COUNTRY_CODES)

        # fmt: off
        column_renaming = {
            census_col: id_name, "type": "Type",
            "G_name": "Group", "D_name": "District", "C_name": "County", "R_name": "Region", "X_name": "Scout Country",
            "clean_postcode": "Postcode", "imd": "IMD Rank", "imd_decile": "IMD Decile",
            "min_year": "First Year", "max_year": "Last Year",
        }
        # fmt: on

        logger.info(f"Merging tables and conforming columns")
        history_summary_data = scout_org_data.join([imd_table, years_return, member_numbers_table]).rename(columns=column_renaming).reset_index(drop=True)

        # create output columns list and add generated section names
        output_columns = [id_name, "Type", "Group", "District", "County", "Region", "Scout Country", "Postcode", "IMD Country", "IMD Rank", "IMD Decile", "First Year", "Last Year"]
        for year in years:
            output_columns.extend([f"{section_name}-{year}" for section_name, section_model in sections_model if section_name != "Explorers"])
            output_columns.append(f"Adults-{year}")

        return pd.DataFrame(history_summary_data, columns=output_columns)

    def new_section_history_summary(self, years: list, report_name: str = None) -> pd.DataFrame:
        sections_model = scout_census.column_labels.sections

        # Given data on all sections, provides summary of all new sections, and
        # copes with the pre-2017 section reporting structure
        logger.info(f"Beginning new_section_history_summary for {years}")
        new_section_ids: list[dict] = []

        logger.info(f"Getting group ID list in column {scout_census.column_labels.id.GROUP}")
        # Iterate through Groups looking for new Sections
        group_ids = self.census_data[scout_census.column_labels.id.GROUP].dropna().drop_duplicates().to_list()

        logger.info(f"Found {len(group_ids)} Groups")

        # for each section in each group in the census
        # construct dict of {year: number of sections of that type open in that year}
        # construct list of number of sections of that type open in that year
        # construct list of changes in number of sections per year
        # if there is an increase year on year
        # for each year from the second year calculate the change in the number of sections
        # whatever happens with change
        # do the same for district sections (explorers)
        #
        #
        # .

        census_data = self.census_data.fillna({scout_census.column_labels.id.GROUP: 0, scout_census.column_labels.id.DISTRICT: 0})

        for group_id in group_ids:
            logger.info(f"Investigating {group_id}")
            group_records = census_data.loc[census_data[scout_census.column_labels.id.GROUP] == group_id]

            for section in scout_census.SECTIONS_GROUP:
                logger.info(f"Finding {section} sections")
                units_by_year = {}
                for year in years:
                    section_numbers_year = group_records.loc[group_records["Year"] == year, getattr(scout_census.column_labels.sections, section).unit_label].sum()
                    units_by_year[year] = section_numbers_year

                increments = [units_by_year[year + 1] - units_by_year[year] for year in units_by_year.keys() if (year + 1) in units_by_year]
                if max(increments) > 0:
                    logger.debug(f"Identified year profile of sections: {units_by_year}")
                    opened_sections = []
                    closed_sections = []
                    for year in years[1:]:
                        change = units_by_year[year] - units_by_year[year - 1]
                        if change > 0:
                            # Extent life of current sections
                            for open_sections in opened_sections:
                                open_sections["years"].append(year)
                            # Create new section record
                            for ii in range(change):
                                logger.debug(f"New {section} section found for {group_id} in {year}")
                                opened_sections.append({"id": group_id, "section": section, "years": [year], "nu_sections": units_by_year})
                        elif change == 0:
                            # Lengthens all sections by a year
                            for open_sections in opened_sections:
                                open_sections["years"].append(year)
                        elif change < 0:
                            for ii in range(-change):
                                # Close sections in newest first
                                if len(opened_sections) > 0:
                                    logger.debug(f"{section} closed for {group_id} in {year}")
                                    closed_sections.append(opened_sections.pop(-1))
                            # Lengthens remaining open sections by a year
                            for open_sections in opened_sections:
                                open_sections["years"].append(year)

                    logger.debug(f"For {group_id} adding\n{opened_sections + closed_sections}")
                    new_section_ids += opened_sections
                    new_section_ids += closed_sections
                else:
                    logger.info(f"No new {section} sections in {group_id}")

        logger.info("Finding new Explorer Sections")
        # Iterate through District looking for new Sections

        district_ids = self.census_data[scout_census.column_labels.id.DISTRICT].drop_duplicates().dropna().to_list()

        for district_id in district_ids:
            logger.info(f"Investigating {district_id}")
            district_records = census_data.loc[census_data[scout_census.column_labels.id.DISTRICT] == district_id]
            units_by_year = {}
            for year in years:
                district_records_year = district_records.loc[district_records["Year"] == year]
                units_by_year[year] = district_records_year[sections_model.Explorers.unit_label].sum()

            increments = [units_by_year[year + 1] - units_by_year[year] for year in units_by_year.keys() if (year + 1) in units_by_year]
            if max(increments) > 0:
                opened_sections = []
                closed_sections = []
                for year in years[1:]:
                    change = units_by_year[year] - units_by_year[year - 1]
                    if change > 0:
                        # Extent life of current sections
                        for open_sections in opened_sections:
                            open_sections["years"].append(year)
                        # Create new section record
                        for ii in range(change):
                            opened_sections.append({"id": district_id, "section": "Explorers", "years": [year], "nu_sections": units_by_year})
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

                logger.debug(f"For {district_id} adding\n{opened_sections + closed_sections}")
                new_section_ids += opened_sections
                new_section_ids += closed_sections

        section_details = []
        for year in years:
            if year < 2017:
                section_details.append(f"{year}_Est_Members")
            else:
                section_details.append(f"{year}_Members")

        # fmt: off
        output_columns = [
            "Object_ID", "Section Name", "Section", "Group_ID", "Group", "District_ID", "District", "County", "Region",
            "Scout Country", "Postcode", "IMD Country", "IMD Rank", "IMD Decile", "First Year", "Last Year",
            f"{years[0]}_sections", *section_details
        ]
        # fmt: on
        output_data = pd.DataFrame(columns=output_columns)

        logger.info(f"Start iteration through {len(new_section_ids)} new Sections")
        used_compass_ids = set()
        count = 0
        total = len(new_section_ids)
        new_sections_id: dict
        for new_sections_id in new_section_ids:
            section_data = {}
            logger.debug(f"Recording {new_sections_id}")
            count += 1
            logger.info(f"{count} of {total}")
            section_id = new_sections_id["id"]
            open_years = new_sections_id["years"]
            section = new_sections_id["section"]
            section_type = getattr(scout_census.column_labels.sections, section).type

            if section in scout_census.SECTIONS_GROUP:
                records = census_data.loc[census_data[scout_census.column_labels.id.GROUP] == section_id]
                section_data["Group_ID"] = records[scout_census.column_labels.id.GROUP].unique()[0]
                section_data["Group"] = records[scout_census.column_labels.name.GROUP].unique()[0]
            elif section in scout_census.SECTIONS_DISTRICT:
                records = census_data.loc[census_data[scout_census.column_labels.id.DISTRICT] == section_id]
                section_data["Group_ID"] = ""
                section_data["Group"] = ""
            else:
                raise Exception(f"{section} neither belongs to a Group or District. id = {new_sections_id}")

            for year in open_years:
                members_cols = getattr(scout_census.column_labels.sections, section).total
                year_records = records.loc[records["Year"] == year]
                if year >= 2017:
                    compass_id = section_data.get("Object_ID")
                    section_year_records = year_records.loc[records[scout_census.column_labels.UNIT_TYPE] == section_type]

                    if compass_id:
                        section_record = section_year_records.loc[section_year_records["Object_ID"] == compass_id]
                        section_data[f"{year}_Members"] = section_record[members_cols].sum()
                    else:
                        section_year_ids: pd.Series = section_year_records["Object_ID"].drop_duplicates()
                        if open_years[0] >= 2017:
                            # If section became open after 31st January 2017 then can identify by Object_ID id
                            last_year_records = records.loc[records["Year"] == (year - 1)]
                            old_section_ids = last_year_records["Object_ID"].unique()
                            opened_section_ids = section_year_ids[~section_year_ids.isin(old_section_ids)]
                            if len(opened_section_ids) > 1:
                                logger.info(f"{len(opened_section_ids)} sections opened")
                                unused_ids = opened_section_ids[~opened_section_ids.isin(used_compass_ids)]
                                compass_id = unused_ids.iloc[0] if not unused_ids.empty else opened_section_ids.iloc[-1]
                            elif len(opened_section_ids) == 0:
                                logger.error(f"No sections opened\n{year}: {section_year_ids}\n{year-1}: {old_section_ids}")
                            elif len(opened_section_ids) == 1:
                                compass_id = opened_section_ids.iloc[0]
                                logger.debug(f"Assigned id: {compass_id}")

                            section_data["Object_ID"] = compass_id
                            used_compass_ids.add(compass_id)
                            section_data[f"{year}_Members"] = section_year_records.loc[section_year_records["Object_ID"] == compass_id, members_cols].sum()
                        else:
                            compass_id = section_year_ids.max()

                            if compass_id in used_compass_ids:
                                section_year_ids.sort_values(ascending=False)
                                unused_ids = section_year_ids[~section_year_ids.isin(used_compass_ids)]
                                if not unused_ids.empty:
                                    compass_id = unused_ids.iloc[0]
                                else:
                                    compass_id = section_year_ids.iloc[0]

                            section_data["Object_ID"] = compass_id
                            used_compass_ids.add(compass_id)
                            total_members = section_year_records.loc[section_year_records["Object_ID"] == compass_id, members_cols].sum()

                            logger.debug(f"{section} in {section_id} in {year} found {total_members} members")
                            section_data[f"{year}_Members"] = total_members
                else:
                    year_before_section_opened = open_years[0] - 1
                    year_before_records = records.loc[records["Year"] == year_before_section_opened]

                    number_of_new_sections = new_sections_id["nu_sections"][open_years[0]] - new_sections_id["nu_sections"][year_before_section_opened]

                    new_members = year_records[members_cols].sum()
                    old_members = year_before_records[members_cols].sum()

                    additional_members = (new_members - old_members) / number_of_new_sections
                    if additional_members < 0:
                        logger.warning(f"{section_id} increased number of {section} sections but membership decreased by {additional_members}")

                    logger.debug(f"{section} in {section_id} in {year} found {additional_members} members")
                    section_data[f"{year}_Est_Members"] = additional_members

            closed_years = [year for year in years if year not in open_years]
            for year in closed_years:
                if year >= 2017:
                    section_data[f"{year}_Members"] = 0
                else:
                    section_data[f"{year}_Est_Members"] = 0

            section_data[f"{years[0]}_sections"] = new_sections_id["nu_sections"][years[0]]

            section_records = None

            if section_data.get("Object_ID"):
                section_records = records.loc[records["Object_ID"] == section_data.get("Object_ID")]
                section_data["Section Name"] = section_records["name"].unique()[0]
            else:
                if open_years[-1] < 2017:
                    if section in scout_census.SECTIONS_GROUP:
                        section_records = records.loc[records[scout_census.column_labels.UNIT_TYPE] == scout_census.UNIT_LEVEL_GROUP]
                    elif section in scout_census.SECTIONS_DISTRICT:
                        section_records = records.loc[records[scout_census.column_labels.UNIT_TYPE] == scout_census.UNIT_LEVEL_DISTRICT]
                elif open_years[-1] == 2017:
                    section_records = records.loc[records[scout_census.column_labels.UNIT_TYPE] == section_type]
                else:
                    raise Exception(f"Unable to find section records for {new_section_ids}")

            section_data["Section"] = section
            section_data["District_ID"] = section_records[scout_census.column_labels.id.DISTRICT].unique()[0]
            section_data["District"] = section_records[scout_census.column_labels.name.DISTRICT].unique()[0]
            section_data["County"] = section_records["C_name"].unique()[0]
            section_data["Region"] = section_records["R_name"].unique()[0]
            section_data["Scout Country"] = section_records["X_name"].unique()[0]

            if open_years[0] == years[0]:
                section_data["First Year"] = f"{years[0]} or before"
            else:
                section_data["First Year"] = open_years[0]
            if open_years[-1] == years[-1]:
                section_data["Last Year"] = f"Open in {years[-1]}"
            else:
                section_data["Last Year"] = open_years[-1]

            # To find the postcode and IMD for a range of Sections and Group
            # records across several years. Find the most recent year, and then
            # choose the Postcode, where the IMD Rank is the lowest.
            most_recent_year = open_years[-1]
            logger.debug(f"Checking {most_recent_year}")
            most_recent = section_records.loc[section_records["Year"] == most_recent_year]
            if most_recent.shape[0] == 1:
                most_recent = most_recent.iloc[0]
            elif most_recent.shape[0] == 0:
                logger.warning("Inconsistent ids")
                if section in scout_census.SECTIONS_GROUP:
                    # In the event that the Object_IDs aren't consistent, pick a section in the group that's most recent
                    # is only applicable after 2017, so sections are assumed to exist.
                    most_recent = records.loc[
                        (records[scout_census.column_labels.id.GROUP] == section_data["Group_ID"])
                        & (records[scout_census.column_labels.UNIT_TYPE] == section_type)
                        & (records["Year"] == most_recent_year)
                    ].iloc[0]
                elif section in scout_census.SECTIONS_DISTRICT:
                    most_recent_record = records.loc[
                        (records[scout_census.column_labels.id.DISTRICT] == section_data["District_ID"])
                        & (records[scout_census.column_labels.UNIT_TYPE] == section_type)
                        & (records["Year"] == most_recent_year)
                    ]

                    if most_recent_record.empty:
                        logger.error(f"No records found with D_ID = {section_data['District_ID']} in {most_recent_year} that are {section}")

                    most_recent = most_recent_record.iloc[0]
            else:
                logger.warning("Multiple sections found, assigning a section")
                most_recent = most_recent.iloc[0]

            postcode_valid = most_recent.at["postcode_is_valid"]
            # logger.debug(f"Identified:\n{most_recent} determined postcode valid:\n{postcode_valid}\n{postcode_valid == 1}\n{postcode_valid == 1}")
            # add postcode
            if postcode_valid:
                logger.debug(f"Adding postcode {most_recent.at[scout_census.column_labels.POSTCODE]}")
                section_data["Postcode"] = most_recent.at[scout_census.column_labels.POSTCODE]
                country = ONS_PD.COUNTRY_CODES.get(most_recent.at["ctry"])
                section_data["IMD Country"] = country if country else scout_census.DEFAULT_VALUE
                section_data["IMD Decile"] = most_recent.at["imd_decile"]
                section_data["IMD Rank"] = most_recent.at["imd"]
            else:
                section_data["Postcode"] = scout_census.DEFAULT_VALUE
                section_data["IMD Country"] = scout_census.DEFAULT_VALUE
                section_data["IMD Decile"] = scout_census.DEFAULT_VALUE
                section_data["IMD Rank"] = scout_census.DEFAULT_VALUE

            section_data_df = pd.DataFrame([section_data], columns=output_columns)
            output_data = pd.concat([output_data, section_data_df], axis=0)

        output_data.reset_index(drop=True, inplace=True)
        if report_name:
            report_io.save_report(output_data, report_name)
        return output_data
