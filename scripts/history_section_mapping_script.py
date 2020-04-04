from src.data.scout_data import ScoutData
from src.reports.history_summary import HistorySummary

if __name__ == "__main__":
    scout_data = ScoutData()
    scout_data.add_imd_decile()
    history_summary = HistorySummary(scout_data)
    history_summary.group_history_summary(["2019"], report_name="2019_groups_with_IMD")
