from src.data.scout_data import ScoutData
from src.reports.history_summary import HistorySummary

if __name__ == "__main__":
    years = [2015, 2016, 2017, 2018, 2019, 2020]

    scout_data = ScoutData()
    scout_data.filter_records("Year", years)
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])

    # If filtering on IMD, remove NA values
    # scout_data.filter_records("imd_decile", ["nan"], mask=True)
    # scout_data.filter_records("imd_decile", [1, 2, 3])

    section_history = HistorySummary(scout_data)
    section_history.new_section_history_summary(years, report_name="opened_section_data")
    scout_data.close()
