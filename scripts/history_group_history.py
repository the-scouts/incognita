import time

from incognita.data.scout_census import load_census_data
from incognita.logger import logger
from incognita.reports.history_summary import HistorySummary
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "imd_decile", {1, 2})
    census_data = filter.filter_records(census_data, "C_name", {"Shropshire"})

    # # Read group list - with a column headed "G_ID"
    # groups = pd.read_csv(r"Output\yuf_groups.csv")
    # group_ids = groups["G_ID"].drop_duplicates().dropna().to_list()
    # census_data = filter.filter_records(census_data, "G_ID", {group_ids})

    years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
    history_summary = HistorySummary(census_data)
    history_summary.group_history_summary(years, report_name="group_history_report")
    timing.close(start_time)
