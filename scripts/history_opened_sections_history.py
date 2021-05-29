import time

from incognita.data.scout_census import load_census_data
from incognita.logger import logger
from incognita.reports.history_summary import HistorySummary
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    census_ids = {15, 16, 17, 18, 19, 20}

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "Census_ID", census_ids)
    census_data = filter.filter_records(census_data, "X_name", {"England", "Scotland", "Wales", "Northern Ireland"})

    # If filtering on IMD, remove NA values
    # census_data = filter.filter_records(census_data, "imd_decile", ["nan"], exclude_matching=True)
    # census_data = filter.filter_records(census_data, "imd_decile", [1, 2, 3])

    section_history = HistorySummary(census_data)
    section_history.new_section_history_summary(sorted(census_ids), report_name="opened_section_data")
    timing.close(start_time)
