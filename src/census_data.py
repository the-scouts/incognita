import pandas as pd
import collections


class CensusData:
    constants = {
        'DEFAULT_VALUE': "error",

        # Column headings
        'CLEAN_POSTCODE': "clean_postcode",
        'ONSPD_POSTCODE_FIELD': 'pcd',
        'CENSUS_TYPE_HEADING': "type",
        'CENSUS_POSTCODE_HEADING': "postcode",
        'CENSUS_GROUP_ID': 'G_ID',
        'CENSUS_DISTRICT_ID': 'D_ID',
        'CENSUS_GROUP_NAME': "G_name",
        'CENSUS_DISTRICT_NAME': "D_name",
        'CENSUS_BEAVERS_WAITING': "WaitList_b",
        'CENSUS_CUBS_WAITING': "WaitList_c",
        'CENSUS_SCOUTS_WAITING': "WaitList_s",
        'CENSUS_EXPLORERS_WAITING': "WaitList_e",
        'CENSUS_VALID_POSTCODE': "postcode_is_valid",
        'CENSUS_YEAR_HEADING': "Year"}

    def __init__(self, file_path_csv):
        data_values_32 = {key: "Int32" for key in ["Object_ID", "G_ID", "D_ID", "C_ID", "R_ID", "X_ID", "eastings", "northings"]}
        data_values_cat = {key: "category" for key in ["compass", "type", "name", "G_name", "D_name", "C_name", "R_name", "X_name", "postcode", "Young_Leader_Unit"]}
        data_values_16 = {key: "Int16" for key in ["Year", "Beavers_Units", "Cubs_Units", "Scouts_Units", "Explorers_Units", "Network_Units", "Beavers_f", "Beavers_m", "Cubs_f", "Cubs_m", "Scouts_f", "Scouts_m", "Explorers_f", "Explorers_m", "Network_f", "Network_m", "Yls", "WaitList_b", "WaitList_c", "WaitList_s", "WaitList_e", "Leaders", "SectAssistants", "OtherAdults", "Chief_Scout_Bronze_Awards", "Chief_Scout_Silver_Awards", "Chief_Scout_Gold_Awards", "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards", "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "Queens_Scout_Awards", "Eligible4Bronze", "Eligible4Silver", "Eligible4Gold", "Eligible4Diamond", "Eligible4QSA"]}
        data_values_sections = {**data_values_32, **data_values_cat, **data_values_16}
        self.sections_file_path = file_path_csv
        self.sections_postcode_data = pd.read_csv(file_path_csv, dtype=data_values_sections, encoding='utf-8')
        self.DEFAULT_VALUE = "error"

        # Column headings
        self.CLEAN_POSTCODE = "clean_postcode"
        #self.ONSPD_POSTCODE_FIELD = 'pcd'
        self.CENSUS_TYPE_HEADING = "type"
        self.CENSUS_POSTCODE_HEADING = "postcode"
        self.CENSUS_GROUP_ID = 'G_ID'
        self.CENSUS_DISTRICT_ID = 'D_ID'
        self.CENSUS_GROUP_NAME = "G_name"
        self.CENSUS_DISTRICT_NAME = "D_name"
        self.CENSUS_BEAVERS_WAITING = "WaitList_b"
        self.CENSUS_CUBS_WAITING = "WaitList_c"
        self.CENSUS_SCOUTS_WAITING = "WaitList_s"
        self.CENSUS_EXPLORERS_WAITING = "WaitList_e"
        self.CENSUS_VALID_POSTCODE = "postcode_is_valid"
        self.CENSUS_YEAR_HEADING = "Year"

        # The values in self.CENSUS_TYPE_HEADING that denote a section.
        self.SECTIONS = collections.OrderedDict()
        self.SECTIONS["Beavers"] = {"name": 'Colony', "male": "Beavers_m", "female": "Beavers_f", "waitlist": self.CENSUS_BEAVERS_WAITING, "unit_label": "Beavers_Units", "level":"Group", "top_award": "Chief_Scout_Bronze_Awards", "top_award_eligible": "Eligible4Bronze"}
        self.SECTIONS["Cubs"] = {"name": 'Pack', "male": "Cubs_m", "female": "Cubs_f", "waitlist": self.CENSUS_CUBS_WAITING, "unit_label": "Cubs_Units", "level":"Group"}
        self.SECTIONS["Scouts"] = {"name": 'Troop', "male": "Scouts_m", "female": "Scouts_f", "waitlist": self.CENSUS_SCOUTS_WAITING, "unit_label": "Scouts_Units", "level":"Group"}
        self.SECTIONS["Explorers"] = {"name": 'Unit', "male": "Explorers_m", "female": "Explorers_f", "waitlist": self.CENSUS_EXPLORERS_WAITING, "unit_label": "Explorers_Units", "level":"District"}
        # The value in self.CENSUS_TYPE_HEADING that denote a group
        self.CENSUS_TYPE_GROUP = "Group"
        # The value in self.CENSUS_TYPE_HEADING that denote a district
        self.CENSUS_TYPE_DISTRICT = "District"
        # The value in the self.CENSUS_TYPE_HEADING that denote an entity made up of sections.
        self.CENSUS_TYPE_ENTITY = [self.CENSUS_TYPE_GROUP, self.CENSUS_TYPE_DISTRICT]

    def group_sections(self):
        return [section for section in self.SECTIONS.keys() if self.SECTIONS[section]["level"] == "Group"]

    def section_group_types(self):
        return [self.SECTIONS[section]["name"] for section in self.SECTIONS.keys() if self.SECTIONS[section]["level"] == "Group"]

    def district_sections(self):
        return [section for section in self.SECTIONS.keys() if self.SECTIONS[section]["level"] == "District"]

    def section_district_types(self):
        return [self.SECTIONS[section]["name"] for section in self.SECTIONS.keys() if self.SECTIONS[section]["level"] == "District"]

    def section_types(self):
        return [self.SECTIONS[section]["name"] for section in self.SECTIONS.keys()]

    def has_ons_data(self):
        """Finds whether ONS data has been added

        :returns: Whether the Scout Census data has ONS data added
        :rtype: bool
        """
        return (self.CLEAN_POSTCODE in list(self.sections_postcode_data.columns.values))
