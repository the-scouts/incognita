from incognita.data.scout_data import ScoutData
from incognita.reports.history_summary import HistorySummary
from incognita.utility import timing

if __name__ == "__main__":
    scout_data = ScoutData()
    scout_data.filter_records("imd_decile", {1, 2})
    scout_data.filter_records("C_name", {"Shropshire"})

    # # Read group list - with a column headed "G_ID"
    # groups = pd.read_csv(r"Output\yuf_groups.csv")
    # group_ids = groups["G_ID"].drop_duplicates().dropna().to_list()
    # scout_data.filter_records("G_ID", {group_ids})

    years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
    history_summary = HistorySummary(scout_data)
    history_summary.group_history_summary(years, report_name="group_history_report")
    timing.close(scout_data)
