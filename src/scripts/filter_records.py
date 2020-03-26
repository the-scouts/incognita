from data.scout_data import ScoutData

if __name__ == "__main__":
    scout_data = ScoutData()

    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("Year", [2019])
    scout_data.add_imd_decile()
    # scout_data.close()
