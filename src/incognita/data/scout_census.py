from pathlib import Path
from typing import Optional

import pandas as pd
from pyarrow import feather
import pydantic


class ColumnLabelsID(pydantic.BaseModel):
    OBJECT: str = "Object_ID"
    COMPASS: str = "compass"
    GROUP: str = "G_ID"
    DISTRICT: str = "D_ID"
    COUNTY: str = "C_ID"
    REGION: str = "R_ID"
    COUNTRY: str = "X_ID"


class ColumnLabelsName(pydantic.BaseModel):
    ITEM: str = "name"
    GROUP: str = "G_name"
    DISTRICT: str = "D_name"
    COUNTY: str = "C_name"
    REGION: str = "R_name"
    COUNTRY: str = "X_name"


class ColumnLabelsSection(pydantic.BaseModel):
    type: str
    unit_label: str
    level: str
    male: str
    female: str
    total: str
    youth_cols: list[str]
    waiting_list: Optional[str]
    is_yl_unit: Optional[str] = None
    top_award: list[str]
    top_award_eligible: list[str]


class ColumnLabelsSections(pydantic.BaseModel):
    Beavers: ColumnLabelsSection = ColumnLabelsSection(
        type="Colony",
        unit_label="Beavers_Units",
        level="Group",
        male="Beavers_m",
        female="Beavers_f",
        total="Beavers_total",
        youth_cols=["Beavers_m", "Beavers_f", "Beavers_SelfIdentify", "Beavers_PreferNoToSay"],
        waiting_list="WaitList_b",
        top_award=["Chief_Scout_Bronze_Awards"],
        top_award_eligible=["Eligible4Bronze"],
    )
    Cubs: ColumnLabelsSection = ColumnLabelsSection(
        type="Pack",
        unit_label="Cubs_Units",
        level="Group",
        male="Cubs_m",
        female="Cubs_f",
        total="Cubs_total",
        youth_cols=["Cubs_m", "Cubs_f", "Cubs_SelfIdentify", "Cubs_PreferNoToSay"],
        waiting_list="WaitList_c",
        top_award=["Chief_Scout_Silver_Awards"],
        top_award_eligible=["Eligible4Silver"],
    )
    Scouts: ColumnLabelsSection = ColumnLabelsSection(
        type="Troop",
        unit_label="Scouts_Units",
        level="Group",
        male="Scouts_m",
        female="Scouts_f",
        total="Scouts_total",
        youth_cols=["Scouts_m", "Scouts_f", "Scouts_SelfIdentify", "Scouts_PreferNoToSay"],
        waiting_list="WaitList_s",
        top_award=["Chief_Scout_Gold_Awards"],
        top_award_eligible=["Eligible4Gold"],
    )
    Explorers: ColumnLabelsSection = ColumnLabelsSection(
        type="Unit",
        unit_label="Explorers_Units",
        level="District",
        male="Explorers_m",
        female="Explorers_f",
        total="Explorers_total",
        youth_cols=["Explorers_m", "Explorers_f", "Explorers_SelfIdentify", "Explorers_PreferNoToSay"],
        waiting_list="WaitList_e",
        is_yl_unit="Young_Leader_Unit",
        top_award=[
            "Chief_Scout_Diamond_Awards",  # reorder for Diamond first
            "Chief_Scout_Platinum_Awards",
            "Queens_Scout_Awards",
            "Duke_Of_Edinburghs_Bronze",
            "Duke_Of_Edinburghs_Silver",
            "Duke_Of_Edinburghs_Gold",
            "Explorer_Belts",
            "Young_Leader_Belts",
        ],
        top_award_eligible=["Eligible4Diamond", "Eligible4QSA"],
    )
    Network: ColumnLabelsSection = ColumnLabelsSection(
        type="Network",
        unit_label="Network_Units",
        level="District",
        male="Network_m",
        female="Network_f",
        total="Network_total",
        youth_cols=["Network_m", "Network_f", "Network_SelfIdentify", "Network_PreferNoToSay"],
        waiting_list=None,
        top_award=[
            "Queens_Scout_Awards",  # reorder for QSA first
            "Chief_Scout_Platinum_Awards",
            "Chief_Scout_Diamond_Awards",
            "Duke_Of_Edinburghs_Bronze",
            "Duke_Of_Edinburghs_Silver",
            "Duke_Of_Edinburghs_Gold",
            "Explorer_Belts",
        ],
        top_award_eligible=["Eligible4QSA"],
    )


class ColumnLabels(pydantic.BaseModel):
    UNIT_TYPE: str = "type"  # Colony, Group, ASU, Region etc.
    POSTCODE: str = "postcode"  # Postcode field
    VALID_POSTCODE: str = "postcode_is_valid"
    YEAR: str = "Year"
    id: ColumnLabelsID = ColumnLabelsID()
    name: ColumnLabelsName = ColumnLabelsName()
    sections: ColumnLabelsSections = ColumnLabelsSections()


column_labels = ColumnLabels()  # holds strings of all census csv column headings, structured to help access
DEFAULT_VALUE = "error"  # holds value for NaN values
UNIT_LEVEL_GROUP = "Group"  # The value in column_labels.sections.<level> that denote a group
UNIT_LEVEL_DISTRICT = "District"  # The value in column_labels.sections.<level> that denote a district

SECTIONS_GROUP: set[str] = {name for name, model in column_labels.sections if model.level == "Group"}
SECTIONS_DISTRICT: set[str] = {name for name, model in column_labels.sections if model.level == "District"}

# TODO: good collective name for Colonies, Packs, Troops, Units etc. Currently type.
TYPES_GROUP: set[str] = {model.type for name, model in column_labels.sections if model.level == "Group"}
TYPES_DISTRICT: set[str] = {model.type for name, model in column_labels.sections if model.level == "District"}


class ScoutCensus:
    """Holds and accesses census data from a given file.

    Data is read from passed path, and imported with specified data types.
    Attributes are added to the class to aid accessing data in a structured way.
    All column labels from the Census report are set in column_labels and can be
        changed to reflect the input census file.

    Args:
        census_file_path: path to input file with Census data.

    """

    def __init__(self, census_file_path: Path, load_data: bool = True):
        if not load_data:
            self.data = pd.DataFrame()
            return

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

        # TODO add yp total columns, clean postcode/valid postcode, Asst leaders, SOWA/SOWA eligible, ONS PD fields
        data_values_sections = (
            {key: "bool" for key in cols_bool} | {key: "Int16" for key in cols_int_16} | {key: "Int32" for key in cols_int_32} | {key: "category" for key in cols_categorical}
        )
        if census_file_path.suffix == ".csv":
            self.data = pd.read_csv(census_file_path, dtype=data_values_sections, encoding="utf-8")
        elif census_file_path.suffix == ".feather":
            self.data = feather.read_feather(census_file_path)
            self.data[cols_bool] = self.data[cols_bool].astype(bool)
            self.data[cols_int_16] = self.data[cols_int_16].astype("Int16")
            self.data[cols_int_32] = self.data[cols_int_32].astype("Int32")
            self.data[cols_categorical] = self.data[cols_categorical].astype("category")
            # ['oscty', 'oslaua', 'osward', 'ctry', 'rgn', 'pcon', 'lsoa11', 'msoa11', 'lat', 'long'] not dtyped
        else:
            raise ValueError(f"Unknown census extract file extension ({census_file_path.suffix})!\n Should be CSV or Feather.")
