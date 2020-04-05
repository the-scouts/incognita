import pandas as pd
from typing import Dict


class ScoutCensus:
    """Holds and accesses census data from a given file.

    Data is read from passed path, and imported with specified data types.
    Attributes are added to the class to aid accessing data in a structured way.
    All column labels from the Census report are set in column_labels and can be
        changed to reflect the input census file.

    :param str file_path_csv: path to input file with Census data.

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
                "male": "Beavers_m", "female": "Beavers_f",
                "waiting_list": "WaitList_b",
                "top_award": "Chief_Scout_Bronze_Awards", "top_award_eligible": "Eligible4Bronze",
            },
            "Cubs": {
                "type": "Pack", "unit_label": "Cubs_Units", "level": "Group",
                "male": "Cubs_m", "female": "Cubs_f",
                "waiting_list": "WaitList_c",
                "top_award": "Chief_Scout_Silver_Awards", "top_award_eligible": "Eligible4Silver",
            },
            "Scouts": {
                "type": "Troop", "unit_label": "Scouts_Units", "level": "Group",
                "male": "Scouts_m", "female": "Scouts_f",
                "waiting_list": "WaitList_s",
                "top_award": "Chief_Scout_Gold_Awards", "top_award_eligible": "Eligible4Gold",
            },
            "Explorers": {
                "type": "Unit", "unit_label": "Explorers_Units", "level": "District",
                "male": "Explorers_m", "female": "Explorers_f",
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
                "male": "Network_m", "female": "Network_f",
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

    def __init__(self, file_path_csv):
        cols_int_32 = ["Object_ID", "G_ID", "D_ID", "C_ID", "R_ID", "X_ID", "eastings", "northings"]
        cols_categorical = ["compass", "type", "name", "G_name", "D_name", "C_name", "R_name", "X_name", "postcode", "Young_Leader_Unit"]
        # fmt: off
        cols_int_16 = [
            "Year", "Beavers_Units", "Cubs_Units", "Scouts_Units", "Explorers_Units", "Network_Units", "Beavers_f", "Beavers_m", "Cubs_f", "Cubs_m", "Scouts_f", "Scouts_m",
            "Explorers_f", "Explorers_m", "Network_f", "Network_m", "Yls", "WaitList_b", "WaitList_c", "WaitList_s", "WaitList_e", "Leaders", "SectAssistants", "OtherAdults",
            "Chief_Scout_Bronze_Awards", "Chief_Scout_Silver_Awards", "Chief_Scout_Gold_Awards", "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards",
            "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "Queens_Scout_Awards", "Eligible4Bronze",
            "Eligible4Silver", "Eligible4Gold", "Eligible4Diamond", "Eligible4QSA"
        ]
        # fmt: on

        data_values_32 = {key: "Int32" for key in cols_int_32}
        data_values_cat = {key: "category" for key in cols_categorical}
        data_values_16 = {key: "Int16" for key in cols_int_16}
        data_values_sections = {**data_values_32, **data_values_cat, **data_values_16}

        self.data = pd.read_csv(file_path_csv, dtype=data_values_sections, encoding="utf-8")

    @staticmethod
    def get_section_names(level):
        """Return list of section names that exist within a particular organisational level.

        :param level: Organisational level. Usually Group or District.
        :type level: str or list
        :return: List of section names.
        """
        section_dict: Dict
        sections_labels = ScoutCensus.column_labels["sections"].items()
        return [section_name for section_name, section_dict in sections_labels if section_dict["level"] in level]

    @staticmethod
    def get_section_type(level):
        """Return list of section types that exist within a particular organisational level.

        :param level: Organisational level. Usually Group or District.
        :type level: str or list
        :return: List of section types
        """
        section_names_list = ScoutCensus.get_section_names(level)
        section_dict: Dict = ScoutCensus.column_labels["sections"]
        return [section_dict[section]["type"] for section in section_names_list]
        # TODO: good collective name for Colonies, Packs, Troops, Units etc. Currently type.
