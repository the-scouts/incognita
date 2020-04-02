from src.data.scout_data import ScoutData
from src.reports.history_summary import HistorySummary

if __name__ == "__main__":
    scout_data = ScoutData()
    scout_data.add_imd_decile()
    scout_data.filter_records("imd_decile", [1, 2])
    scout_data.filter_records("C_name", ["Shropshire"])

    history_summary = HistorySummary(scout_data)
    history_summary.group_history_summary([2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019], report_name="low_IMD_group_history")
    scout_data.close()
