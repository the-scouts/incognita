from incognita.data.scout_data import ScoutData
from incognita.reports.history_summary import HistorySummary
from incognita.utility import timing

if __name__ == "__main__":
    census_ids = {15, 16, 17, 18, 19, 20}

    scout_data = ScoutData()
    scout_data.filter_records("Census_ID", census_ids)
    scout_data.filter_records("X_name", {"England", "Scotland", "Wales", "Northern Ireland"})

    # If filtering on IMD, remove NA values
    # scout_data.filter_records("imd_decile", ["nan"], exclude_matching=True)
    # scout_data.filter_records("imd_decile", [1, 2, 3])

    section_history = HistorySummary(scout_data)
    section_history.new_section_history_summary(sorted(census_ids), report_name="opened_section_data")
    timing.close(scout_data)
