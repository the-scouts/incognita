from src.scout_data import ScoutData

if __name__ == "__main__":
    scout_data = ScoutData()
    scout_data.add_imd_decile()
    sections = scout_data.filter_records("imd_decile", [1, 2])
