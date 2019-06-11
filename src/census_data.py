import pandas as pd
import collections


class CensusData:
    # Column headings
    column_labels = {
        'UNIT_TYPE': "type",  # Colony, Group, ASU, Region etc.
        'POSTCODE': "postcode",  # Postcode field
        'VALID_POSTCODE': "postcode_is_valid",
        'YEAR': "Year",
        'id': {
            'GROUP': 'G_ID',
            'DISTRICT': 'D_ID',
            'COUNTY': 'C_ID',
            'REGION': 'R_ID',
            'COUNTRY': 'X_ID',
        },
        'name': {
            'GROUP': "G_name",
            'DISTRICT': "D_name",
            'COUNTY': 'C_name',
            'REGION': 'R_name',
            'COUNTRY': 'X_name',
        },
        'sections': {
            "Beavers": {
                "name": 'Colony', "unit_label": "Beavers_Units", "level": "Group",
                "male": "Beavers_m", "female": "Beavers_f",
                "waiting_list": "WaitList_b",
                "top_award": "Chief_Scout_Bronze_Awards", "top_award_eligible": "Eligible4Bronze", },
            "Cubs": {
                "name": 'Pack', "unit_label": "Cubs_Units", "level": "Group",
                "male": "Cubs_m", "female": "Cubs_f",
                "waiting_list": "WaitList_c",
                "top_award": "Chief_Scout_Silver_Awards", "top_award_eligible": "Eligible4Silver", },
            "Scouts": {
                "name": 'Troop', "unit_label": "Scouts_Units", "level": "Group",
                "male": "Scouts_m", "female": "Scouts_f",
                "waiting_list": "WaitList_s",
                "top_award": "Chief_Scout_Gold_Awards", "top_award_eligible": "Eligible4Gold", },
            "Explorers": {
                "name": 'Unit', "unit_label": "Explorers_Units", "level": "District",
                "male": "Explorers_m", "female": "Explorers_f",
                "waiting_list": "WaitList_e", "is_yl_unit": "Young_Leader_Unit",
                "top_award": ["Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards", "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "Queens_Scout_Awards", ],
                "top_award_eligible": ["Eligible4Diamond", "Eligible4QSA"], },
            "Network": {
                "name": 'Network', "unit_label": "Network_Units", "level": "District",
                "male": "Network_m", "female": "Network_f",
                "top_award": ["Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards", "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold", "Explorer_Belts", "Queens_Scout_Awards", ],
                "top_award_eligible": "Eligible4QSA", },
        },
    }
    DEFAULT_VALUE = "error"

    # The value in column_labels['UNIT_TYPE'] that denote a group
    UNIT_TYPE_GROUP = "Group"
    # The value in column_labels['UNIT_TYPE'] that denote a district
    UNIT_TYPE_DISTRICT = "District"
    # The value in the column_labels['UNIT_TYPE'] that denote an entity made up of sections.
    CENSUS_TYPE_ENTITY = [UNIT_TYPE_GROUP, UNIT_TYPE_DISTRICT]

    def __init__(self, file_path_csv):
        data_values_32 = {key: "Int32" for key in ["Object_ID", "G_ID", "D_ID", "C_ID", "R_ID", "X_ID", "eastings", "northings"]}
        data_values_cat = {key: "category" for key in ["compass", "type", "name", "G_name", "D_name", "C_name", "R_name", "X_name", "postcode", "Young_Leader_Unit"]}
        data_values_16 = {key: "Int16" for key in ["Year", "Beavers_Units", "Cubs_Units", "Scouts_Units", "Explorers_Units", "Network_Units", "Beavers_f", "Beavers_m", "Cubs_f", "Cubs_m", "Scouts_f", "Scouts_m", "Explorers_f", "Explorers_m", "Network_f", "Network_m", "Yls", "WaitList_b", "WaitList_c", "WaitList_s", "WaitList_e", "Leaders", "SectAssistants", "OtherAdults", "Chief_Scout_Bronze_Awards", "Chief_Scout_Silver_Awards", "Chief_Scout_Gold_Awards", "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards", "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "Queens_Scout_Awards", "Eligible4Bronze", "Eligible4Silver", "Eligible4Gold", "Eligible4Diamond", "Eligible4QSA"]}
        data_values_sections = {**data_values_32, **data_values_cat, **data_values_16}
        self.sections_file_path = file_path_csv
        self.data = pd.read_csv(file_path_csv, dtype=data_values_sections, encoding='utf-8')

    def sections_name_by_level(self, level):
        return [section for section in self.column_labels['sections'].keys() if self.column_labels['sections'][section]["level"] == level]

    def section_labels_by_level(self, level):
        section_names = self.sections_name_by_level(level)
        return [self.column_labels['sections'][section]["name"] for section in section_names]

    def section_types(self):
        return [self.column_labels['sections'][section]["name"] for section in self.column_labels['sections'].keys()]

    def has_ons_data(self):
        """Finds whether ONS data has been added

        :returns: Whether the Scout Census data has ONS data added
        :rtype: bool
        """
        return CensusData.column_labels['VALID_POSTCODE'] in list(self.data.columns.values)
