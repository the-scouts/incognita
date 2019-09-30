from src.scout_data import ScoutData

if __name__ == "__main__":
    years = [2014, 2015, 2016, 2017, 2018, 2019]

    scout_data = ScoutData()
    scout_data.add_imd_decile()
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("Year", years)
    scout_data.filter_records("imd_decile", [1, 2])
    scout_data.section_history_summary(years, report_name="Sections_opened_in_deprivation_since_2014")
