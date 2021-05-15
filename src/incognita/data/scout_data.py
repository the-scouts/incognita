from __future__ import annotations

from pathlib import Path
import time

import geopandas as gpd
import pandas as pd
from pyarrow import feather

from incognita.data import scout_census
from incognita.data.ons_pd_may_19 import ons_postcode_directory_may_19
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import utility

pd.options.display.width = pd.options.display.max_columns = 5000

# TODO add yp total columns, clean postcode/valid postcode, Asst leaders, SOWA/SOWA eligible, ONS PD fields
# fmt: off
cols_bool = ["postcode_is_valid"]
cols_int_16 = [
    "Year", "Beavers_Units", "Cubs_Units", "Scouts_Units", "Explorers_Units", "Network_Units", "Beavers_f", "Beavers_m", "Cubs_f", "Beavers_total", "Cubs_m", "Cubs_total",
    "Scouts_f", "Scouts_m", "Scouts_total", "Explorers_f", "Explorers_m", "Explorers_total", "Network_f", "Network_m", "Network_total", "Yls", "WaitList_b", "WaitList_c",
    "WaitList_s", "WaitList_e", "Leaders", "AssistantLeaders", "SectAssistants", "OtherAdults", "Chief_Scout_Bronze_Awards", "Chief_Scout_Silver_Awards",
    "Chief_Scout_Gold_Awards", "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards", "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver",
    "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "Queens_Scout_Awards", "Eligible4Bronze", "Eligible4Silver", "Eligible4Gold", "Eligible4Diamond",
    "Eligible4QSA", "ScoutsOfTheWorldAward", "Eligible4SOWA", "imd_decile"
]
cols_int_32 = ["Object_ID", "G_ID", "D_ID", "C_ID", "R_ID", "X_ID", "imd"]
cols_categorical = ["compass", "type", "name", "G_name", "D_name", "C_name", "R_name", "X_name", "postcode", "clean_postcode", "Young_Leader_Unit"]
# fmt: on


def _load_census_data(census_file_path: Path) -> pd.DataFrame:
    """Loads census data from a given file.

    Args:
        census_file_path: path to input file with Census data.

    """
    if census_file_path.suffix == ".csv":
        dtypes = {key: "bool" for key in cols_bool} | {key: "Int16" for key in cols_int_16} | {key: "Int32" for key in cols_int_32} | {key: "category" for key in cols_categorical}
        return pd.read_csv(census_file_path, dtype=dtypes, encoding="utf-8")
    elif census_file_path.suffix == ".feather":
        data = feather.read_feather(census_file_path)
        data[cols_bool] = data[cols_bool].astype(bool)
        data[cols_int_16] = data[cols_int_16].astype("Int16")
        data[cols_int_32] = data[cols_int_32].astype("Int32")
        data[cols_categorical] = data[cols_categorical].astype("category")
        return data
        # ['oscty', 'oslaua', 'osward', 'ctry', 'rgn', 'pcon', 'lsoa11', 'msoa11', 'lat', 'long'] not dtyped
    else:
        raise ValueError(f"Unknown census extract file extension ({census_file_path.suffix})!\n Should be CSV or Feather.")


class ScoutData:
    """Provides access to manipulate and process data."""

    @property
    def filterable_columns(self) -> set[str]:
        """Returns ID and name columns of the dataset"""
        id_cols = scout_census.column_labels.id.__dict__.values()
        name_cols = scout_census.column_labels.name.__dict__.values()
        return {*id_cols, *name_cols}

    # TODO: Add column name properties (e.g. scout_census.column_labels.VALID_POSTCODE

    def __init__(self, merged_csv: bool = True, census_path: Path = config.SETTINGS.census_extract.merged, load_census_data: bool = True):
        # record a class-wide start time
        self.start_time = time.time()

        logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime())}")

        logger.info("Loading Scout Census data")
        # Loads Scout Census Data from disk. We assume no custom path has been
        # passed, but allow for one to by passing a custom `census_path` value.
        self.census_data = _load_census_data(census_path) if load_census_data else pd.DataFrame()
        self.points_data = gpd.GeoDataFrame()
        logger.info(f"Loading Scout Census data finished, {time.time() - self.start_time:.2f} seconds elapsed.")

        if merged_csv:
            logger.info("Loading ONS data")
            start_time = time.time()

            # Check if the data has been merged with the ONS postcode directory
            if scout_census.column_labels.VALID_POSTCODE in self.census_data.columns:
                self.ons_pd = ons_postcode_directory_may_19
            else:
                raise Exception(f"The ScoutCensus file has no ONS data, because it doesn't have a {scout_census.column_labels.VALID_POSTCODE} column")

            logger.info(f"Loading {self.ons_pd.PUBLICATION_DATE} ONS data finished, {time.time() - start_time:.2f} seconds elapsed.")

    def filter_records(self, field: str, value_list: set, mask: bool = False, exclusion_analysis: bool = False) -> None:
        """Filters the Census records by any field in ONS PD.

        Args:
            field: The field on which to filter
            value_list: The values on which to filter
            mask: If True, exclude the values that match the filter. If False, keep the values that match the filter.
            exclusion_analysis:

        """
        self.census_data = utility.filter_records(self.census_data, field, value_list, mask, exclusion_analysis)

    def add_shape_data(self, shapes_key: str, path: Path = None, gdf: gpd.GeoDataFrame = None) -> None:
        if path is not None:
            uid = Path(f"{hash(self.census_data.shape)}_{shapes_key}_{path.stem}.feather")
            if uid.is_file():
                data = pd.read_feather(uid).set_index("index")
                assert self.census_data.equals(data[self.census_data.columns])
                self.census_data = data
                return
        else:
            uid = None

        if self.points_data.empty:
            idx = pd.Series(self.census_data.index, name="object_index")
            self.points_data = gpd.GeoDataFrame(idx, geometry=gpd.points_from_xy(self.census_data.long, self.census_data.lat), crs=utility.WGS_84)

        if path is not None:
            all_shapes = gpd.read_file(path)
        elif gdf is not None:
            all_shapes = gdf
        else:
            raise ValueError("A path to a shapefile or a GeoDataFrame must be passed")
        shapes = all_shapes[[shapes_key, "geometry"]].to_crs(epsg=utility.WGS_84)

        spatial_merged = gpd.sjoin(self.points_data, shapes, how="left", op="within").set_index("object_index")
        merged = self.census_data.merge(spatial_merged[[shapes_key]], how="left", left_index=True, right_index=True)
        assert self.census_data.equals(merged[self.census_data.columns])
        self.census_data = merged
        if path is not None and uid is not None:
            merged.reset_index(drop=False).to_feather(uid)

    def close(self) -> None:
        """Outputs the duration of the programme"""
        logger.info(f"Script finished, {time.time() - self.start_time:.2f} seconds elapsed.")
