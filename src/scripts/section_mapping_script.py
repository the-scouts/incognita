from src.scout_data import ScoutData

if __name__ == "__main__":
    scout_data = ScoutData()
    scout_data.add_imd_decile()
    scout_data.group_history_summary(["2019"], report_name="2019_groups_with_IMD")
