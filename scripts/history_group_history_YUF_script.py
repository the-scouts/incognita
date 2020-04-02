import pandas as pd
from data.scout_data import ScoutData
from reports.history_summary import HistorySummary

if __name__ == "__main__":
    scout_data = ScoutData()

    # Read group list - with a column headed "G_ID"
    groups = pd.read_csv(r"Output\yuf_groups.csv")
    group_ids = groups["G_ID"].drop_duplicates().dropna().to_list()

    scout_data.filter_records("G_ID", [group_ids])
    scout_data.add_imd_decile()
    history_summary = HistorySummary(scout_data)
    history_summary.group_history_summary([2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019], report_name="YUF_group_history")
