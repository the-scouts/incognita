from src.data.scout_data import ScoutData
from src.reports.history_summary import HistorySummary

if __name__ == "__main__":
    years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]

    scout_data = ScoutData()
    scout_data.filter_records("Year", years)
    scout_data.filter_records("ctry", ["E92000001", "N92000002", "S92000003", "W92000004"], exclusion_analysis=True)
    # scout_data.filter_records("imd_decile", [1, 2, 3])

    section_history = HistorySummary(scout_data)
    section_history.new_section_history_summary(years, report_name="Sections_opened_in_deprivation_since_2010")
