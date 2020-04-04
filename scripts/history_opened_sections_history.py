from src.data.scout_data import ScoutData
from src.reports.history_summary import HistorySummary

if __name__ == "__main__":
    years = [2014, 2015, 2016, 2017, 2018, 2019]

    scout_data = ScoutData()
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("Year", years)
    scout_data.add_imd_decile()
    history_summary = HistorySummary(scout_data)
    history_summary.new_section_history_summary(years, report_name="opened_section_data")
    scout_data.close()
