from incognita.data.scout_data import ScoutData
from incognita.reports.history_summary import HistorySummary

if __name__ == "__main__":
    scout_data = ScoutData()
    # scout_data.filter_records("imd_decile", {1, 2})
    # scout_data.filter_records("C_name", {"Shropshire"})

    years = [2020]  # + [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]
    history_summary = HistorySummary(scout_data)
    history_summary.group_history_summary(sorted(years), report_name="group_history_report")
    scout_data.close()
