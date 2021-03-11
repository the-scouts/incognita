from pathlib import Path

import pandas as pd
from pyarrow import feather


class ScoutCensus:
    """Holds and accesses census data from a given file.

    Data is read from passed path, and imported with specified data types.
    Attributes are added to the class to aid accessing data in a structured way.
    All column labels from the Census report are set in column_labels and can be
        changed to reflect the input census file.

    :param str census_file_path: path to input file with Census data.

    :var ScoutCensus.column_labels: holds strings of all census csv column headings, structured to help access
    :var ScoutCensus.DEFAULT_VALUE: holds value for NaN values
    :var ScoutCensus.UNIT_LEVEL_GROUP: The value in column_labels["sections"]["level"] that denote a group
    :var ScoutCensus.UNIT_LEVEL_DISTRICT: The value in column_labels["sections"]["level"] that denote a district
    """

    # fmt: off
    column_labels = {
        "UNIT_TYPE": "type",  # Colony, Group, ASU, Region etc.
        "POSTCODE": "postcode",  # Postcode field
        "VALID_POSTCODE": "postcode_is_valid",
        "YEAR": "Year",
        "id": {
            "OBJECT": "Object_ID",
            "COMPASS": "compass",
            "GROUP": "G_ID",
            "DISTRICT": "D_ID",
            "COUNTY": "C_ID",
            "REGION": "R_ID",
            "COUNTRY": "X_ID",
        },
        "name": {
            "ITEM": "name",
            "GROUP": "G_name",
            "DISTRICT": "D_name",
            "COUNTY": "C_name",
            "REGION": "R_name",
            "COUNTRY": "X_name",
        },
        "sections": {
            "Beavers": {
                "type": "Colony", "unit_label": "Beavers_Units", "level": "Group",
                "male": "Beavers_m", "female": "Beavers_f", "total": "Beavers_total",
                "youth_cols": ["Beavers_m", "Beavers_f", "Beavers_SelfIdentify", "Beavers_PreferNoToSay"],
                "waiting_list": "WaitList_b",
                "top_award": "Chief_Scout_Bronze_Awards", "top_award_eligible": "Eligible4Bronze",
            },
            "Cubs": {
                "type": "Pack", "unit_label": "Cubs_Units", "level": "Group",
                "male": "Cubs_m", "female": "Cubs_f", "total": "Cubs_total",
                "youth_cols": ["Cubs_m", "Cubs_f", "Cubs_SelfIdentify", "Cubs_PreferNoToSay"],
                "waiting_list": "WaitList_c",
                "top_award": "Chief_Scout_Silver_Awards", "top_award_eligible": "Eligible4Silver",
            },
            "Scouts": {
                "type": "Troop", "unit_label": "Scouts_Units", "level": "Group",
                "male": "Scouts_m", "female": "Scouts_f", "total": "Scouts_total",
                "youth_cols": ["Scouts_m", "Scouts_f", "Scouts_SelfIdentify", "Scouts_PreferNoToSay"],
                "waiting_list": "WaitList_s",
                "top_award": "Chief_Scout_Gold_Awards", "top_award_eligible": "Eligible4Gold",
            },
            "Explorers": {
                "type": "Unit", "unit_label": "Explorers_Units", "level": "District",
                "male": "Explorers_m", "female": "Explorers_f", "total": "Explorers_total",
                "youth_cols": ["Explorers_m", "Explorers_f", "Explorers_SelfIdentify", "Explorers_PreferNoToSay"],
                "waiting_list": "WaitList_e",
                "is_yl_unit": "Young_Leader_Unit",
                "top_award": [
                    "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards", "Queens_Scout_Awards",
                    "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold",
                    "Explorer_Belts", "Young_Leader_Belts",
                ],
                "top_award_eligible": ["Eligible4Diamond", "Eligible4QSA"],
            },
            "Network": {
                "type": "Network", "unit_label": "Network_Units", "level": "District",
                "male": "Network_m", "female": "Network_f", "total": "Network_total",
                "youth_cols": ["Network_m", "Network_f", "Network_SelfIdentify", "Network_PreferNoToSay"],
                "top_award": [
                    "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards", "Queens_Scout_Awards",
                    "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold",
                    "Explorer_Belts",
                ],
                "top_award_eligible": "Eligible4QSA",
            },
        },
    }
    # fmt: on

    DEFAULT_VALUE = "error"  # DEPR ScoutCensus.DEFAULT_VALUE is deprecated in favour of ScoutData.DEFAULT_VALUE
    UNIT_LEVEL_GROUP = "Group"
    UNIT_LEVEL_DISTRICT = "District"

    def __init__(self, census_file_path: Path, load_data=True):
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

        data_values_bool = {key: "bool" for key in cols_bool}
        data_values_16 = {key: "Int16" for key in cols_int_16}
        data_values_32 = {key: "Int32" for key in cols_int_32}
        data_values_cat = {key: "category" for key in cols_categorical}
        data_values_sections = data_values_bool | data_values_16 | data_values_32 | data_values_cat
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

    @staticmethod
    def get_section_names(level: list) -> list:
        """Return list of section names that exist within a particular organisational level.

        :param list level: Organisational level. Usually Group or District.
        :return: List of section names.
        """
        section_dict: dict
        sections_labels = ScoutCensus.column_labels["sections"].items()
        return [section_name for section_name, section_dict in sections_labels if section_dict["level"] in level]

    @staticmethod
    def get_section_type(level: list) -> list:
        """Return list of section types that exist within a particular organisational level.

        :param list level: Organisational level. Usually Group or District.
        :return: List of section types
        """
        section_names_list = ScoutCensus.get_section_names(level)
        section_dict: dict = ScoutCensus.column_labels["sections"]
        return [section_dict[section]["type"] for section in section_names_list]
        # TODO: good collective name for Colonies, Packs, Troops, Units etc. Currently type.
