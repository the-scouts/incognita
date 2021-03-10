from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time
from typing import TYPE_CHECKING

import geopandas as gpd
import pandas as pd

from incognita import utility
from incognita.data.census_merge_data import CensusMergeData
from incognita.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19
from incognita.data.scout_census import ScoutCensus
from incognita.logger import logger

# type hints
if TYPE_CHECKING:
    from incognita.data.ons_pd import ONSPostcodeDirectory


class ScoutData:
    """Provides access to manipulate and process data."""

    @property
    def columns(self):
        """Returns ID and name columns of the dataset"""
        id_cols = self.scout_census.column_labels["id"].values()
        name_cols = self.scout_census.column_labels["name"].values()
        return [*id_cols, *name_cols]

    # TODO: Add column name properties (e.g. ScoutCensus.column_labels["valid_postcode"]

    DEFAULT_VALUE = ScoutCensus.DEFAULT_VALUE

    def __init__(self, merged_csv=True, load_ons_pd_data=False, census_path=None, load_census_data=True):
        # record a class-wide start time
        self.start_time = time.time()

        logger.info(f"Starting at {datetime.now().time()}")

        logger.info("Loading Scout Census data")
        # Loads Scout Census Data from a path to a .csv file that contains Scout Census data
        # We assume no custom path has been passed, but allow for one to be used
        census_path = utility.SETTINGS["Scout Census location"] if not census_path else census_path
        self.scout_census: ScoutCensus = ScoutCensus(utility.DATA_ROOT / census_path, load_data=load_census_data)
        self.data: pd.DataFrame = self.scout_census.data
        self.points_data: gpd.GeoDataFrame = gpd.GeoDataFrame()
        logger.info(f"Loading Scout Census data finished, {time.time() - self.start_time:.2f} seconds elapsed.")

        if merged_csv:
            logger.info("Loading ONS data")
            start_time = time.time()

            has_ons_pd_data = ScoutCensus.column_labels["VALID_POSTCODE"] in list(self.data.columns.values)

            if has_ons_pd_data:
                self.ons_pd = ONSPostcodeDirectoryMay19(utility.DATA_ROOT / utility.SETTINGS["Reduced ONS PD location"], load_data=load_ons_pd_data)
            else:
                raise Exception(f"The ScoutCensus file has no ONS data, because it doesn't have a {ScoutCensus.column_labels['VALID_POSTCODE']} column")

            logger.info(f"Loading {self.ons_pd.PUBLICATION_DATE} ONS Postcode data finished, {time.time() - start_time:.2f} seconds elapsed.")

    def merge_ons_postcode_directory(self, ons_pd: ONSPostcodeDirectory):
        """Merges census extract data with ONS data

        :param ONSPostcodeDirectory ons_pd: Refers to the ONS Postcode Directory
        """
        ons_fields_data_types = {
            "categorical": ["lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "ctry", "rgn"],
            "int": ["oseast1m", "osnrth1m", "lat", "long", "imd"],
        }

        logger.debug("Initialising merge object")
        merge = CensusMergeData()

        logger.info("Cleaning the postcodes")
        merge.clean_and_verify_postcode(self.data, ScoutCensus.column_labels["POSTCODE"])

        logger.info("Adding ONS postcode directory data to Census and outputting")

        # initially merge just Country column to test what postcodes can match
        self.data = merge.merge_data(self.data, ons_pd.data["ctry"], "clean_postcode")

        # attempt to fix invalid postcodes
        self.data = merge.try_fix_invalid_postcodes(self.data, ons_pd.data["ctry"])

        # fully merge the data
        self.data = merge.merge_data(self.data, ons_pd.data, "clean_postcode")

        # fill unmerged rows with default values
        logger.info("filling unmerged rows")
        self.data = merge.fill_unmerged_rows(self.data, ScoutCensus.column_labels["VALID_POSTCODE"], ons_fields_data_types)

        # Filter to useful columns
        # fmt: off
        self.data = self.data[[
            "Object_ID", "compass", "type", "name", "G_ID", "G_name", "D_ID", "D_name", "C_ID", "C_name", "R_ID", "R_name", "X_ID", "X_name",
            "postcode", "clean_postcode", "postcode_is_valid", "Year", "Beavers_Units", "Cubs_Units", "Scouts_Units", "Explorers_Units", "Network_Units", "Young_Leader_Unit",
            "Beavers_f", "Beavers_m", "Beavers_total", "Cubs_f", "Cubs_m", "Cubs_total", "Scouts_f", "Scouts_m", "Scouts_total", "Explorers_f", "Explorers_m", "Explorers_total",
            "Network_f", "Network_m", "Network_total", "Yls", "WaitList_b", "WaitList_c", "WaitList_s", "WaitList_e", "Leaders", "AssistantLeaders", "SectAssistants", "OtherAdults",
            "Chief_Scout_Bronze_Awards", "Chief_Scout_Silver_Awards", "Chief_Scout_Gold_Awards", "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards",
            "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "ScoutsOfTheWorldAward", "Queens_Scout_Awards",
            "Eligible4Bronze", "Eligible4Silver", "Eligible4Gold", "Eligible4Diamond", "Eligible4QSA", "Eligible4SOWA",
            "oscty", "oslaua", "osward", "ctry", "rgn", "pcon", "lsoa11", "msoa11", "lat", "long", "imd"
        ]]
        # fmt: on

        # Add IMD decile column
        self.data["imd_decile"] = utility.calc_imd_decile(self.data["imd"], self.data["ctry"], ons_pd).astype("UInt8")

    def save_merged_data(self, ons_pd_publication_date: str):
        """Save passed dataframe to csv file.

        Also output list of errors in the merge process to a text file

        :param str ons_pd_publication_date: Refers to the ONS Postcode Directory's publication date
        """
        raw_extract_path = utility.DATA_ROOT / utility.SETTINGS["Raw Census Extract location"]
        output_path = raw_extract_path.parent / f"{raw_extract_path.stem} with {ons_pd_publication_date} fields"
        error_output_path = utility.OUTPUT_FOLDER / "error_file.csv"

        valid_postcode_label = ScoutCensus.column_labels["VALID_POSTCODE"]
        postcode_merge_column = "clean_postcode"
        original_postcode_label = ScoutCensus.column_labels["POSTCODE"]
        compass_id_label = ScoutCensus.column_labels["id"]["COMPASS"]

        # The errors file contains all the postcodes that failed to be looked up in the ONS Postcode Directory
        error_output_fields = [postcode_merge_column, original_postcode_label, compass_id_label, "type", "name", "G_name", "D_name", "C_name", "R_name", "X_name", "Year"]
        self.data.loc[self.data[valid_postcode_label] == 0, error_output_fields].to_csv(error_output_path, index=False, encoding="utf-8-sig")

        # Write the new data to a csv file (utf-8-sig only to force excel to use UTF-8)
        logger.info("Writing merged data")
        self.data.to_csv(output_path.with_suffix(".csv"), index=False, encoding="utf-8-sig")
        self.data.to_feather(output_path.with_suffix(".feather"))

    def filter_records(self, field: str, value_list: list, mask: bool = False, exclusion_analysis: bool = False):
        """Filters the Census records by any field in ONS PD.

        :param str field: The field on which to filter
        :param list value_list: The values on which to filter
        :param bool mask: If True, exclude the values that match the filter. If False, keep the values that match the filter.
        :param bool exclusion_analysis:

        :returns None: Nothing
        """
        self.data = utility.filter_records(self.data, field, value_list, logger, mask, exclusion_analysis)

    def add_shape_data(self, shapes_key: str, path: Path = None, gdf: gpd.GeoDataFrame = None):
        if path is not None:
            uid = Path(f"{hash(self.data.shape)}_{shapes_key}_{path.stem}.feather")
            if uid.is_file():
                data = pd.read_feather(uid).set_index("index")
                assert self.data.equals(data[self.data.columns])
                self.data = data
                return

        if self.points_data.empty:
            idx = pd.Series(self.data.index, name="object_index")
            self.points_data = gpd.GeoDataFrame(idx, geometry=gpd.points_from_xy(self.data.long, self.data.lat), crs=utility.WGS_84)

        if path is not None:
            all_shapes = gpd.GeoDataFrame.from_file(str(path))  # FIXME geopandas does not support os.PathLike (2021-03-09)
        elif gdf is not None:
            all_shapes = gdf
        else:
            raise ValueError("A path to a shapefile or a GeoDataFrame must be passed")
        shapes = all_shapes[[shapes_key, "geometry"]].to_crs(utility.WGS_84)

        spatial_merged = gpd.sjoin(self.points_data, shapes, how="left", op="within").set_index("object_index")
        merged = self.data.merge(spatial_merged[[shapes_key]], how="left", left_index=True, right_index=True)
        assert self.data.equals(merged[self.data.columns])
        self.data = merged
        if path is not None:
            merged.reset_index(drop=False).to_feather(uid)

    def close(self):
        """Outputs the duration of the programme """
        logger.info(f"Script finished, {time.time() - self.start_time:.2f} seconds elapsed.")
