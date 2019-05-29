import pandas as pd
import collections

class SectionData:
    def __init__(self, file_path_csv):
        self.sections_file_path = file_path_csv
        self.sections_pd = pd.read_csv(file_path_csv,encoding='latin-1',dtype='str')

        self.DEFAULT_VALUE = "error"

        # Column headings
        self.CLEAN_POSTCODE = "clean_postcode"
        self.ONSPD_POSTCODE_FIELD = 'pcd'
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
        # The value in the self.CENSUS_TYPE_HEADING that denote an entity made
        # up of sections.
        self.CENSUS_TYPE_ENTITY = [self.CENSUS_TYPE_GROUP, self.CENSUS_TYPE_DISTRICT]

        numeric_cols = ([self.SECTIONS[section]["female"] for section in self.SECTIONS.keys()] +
                        [self.SECTIONS[section]["male"] for section in self.SECTIONS.keys()])

        numeric_cols.append("Leaders")
        numeric_cols.append("SectAssistants")
        numeric_cols.append("OtherAdults")
        numeric_cols.append("Object_ID")
        numeric_cols += [section + "_Units" for section in self.SECTIONS.keys()]
        numeric_cols += [self.SECTIONS["Beavers"]["top_award"], self.SECTIONS["Beavers"]["top_award_eligible"]]
        numeric_cols.append("Eligible4QSA")
        numeric_cols.append("Queens_Scout_Awards")

        for col in numeric_cols:
            self.sections_pd[col] = pd.to_numeric(self.sections_pd[col])

        #self.sections_pd["G_ID"] = self.sections_pd.apply(lambda row: str(row["G_ID"]), axis=1)

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
        return (self.CLEAN_POSTCODE in list(self.sections_pd.columns.values))
