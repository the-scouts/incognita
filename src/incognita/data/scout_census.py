import time
from typing import Optional

import pandas as pd
import pydantic
from pyarrow import feather

from incognita.logger import logger
from incognita.utility import config


def load_census_data():
    # Loads Scout Census Data from disk.
    start_time = time.time()
    census_data = feather.read_feather(config.SETTINGS.census_extract.merged) if load_census_data else pd.DataFrame()
    logger.info(f"Loaded Scout Census data, {time.time() - start_time:.2f} seconds elapsed.")
    return census_data


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
    CENSUS_ID: str = "Census_ID"
    DATE: str = "Census Date"
    id: ColumnLabelsID = ColumnLabelsID()
    name: ColumnLabelsName = ColumnLabelsName()
    sections: ColumnLabelsSections = ColumnLabelsSections()


# in 2021 Census but not in column_labels:
# ['eastings', 'northings', 'IMD', 'Yls', 'Leaders', 'AssistantLeaders', 'SectAssistants', 'OtherAdults', 'ScoutsOfTheWorldAward', 'Eligible4SOWA']
column_labels = ColumnLabels()  # holds strings of all census csv column headings, structured to help access
DEFAULT_VALUE = "error"  # holds value for NaN values
UNIT_LEVEL_GROUP = "Group"  # The value in column_labels.sections.<level> that denote a group
UNIT_LEVEL_DISTRICT = "District"  # The value in column_labels.sections.<level> that denote a district

SECTIONS_GROUP: set[str] = {"Beavers", "Cubs", "Scouts"}
SECTIONS_DISTRICT: set[str] = {"Explorers", "Network"}

# TODO: good collective name for Colonies, Packs, Troops, Units etc. Currently type.
TYPES_GROUP: set[str] = {"Colony", "Pack", "Troop"}
TYPES_DISTRICT: set[str] = {"Network", "Unit"}
