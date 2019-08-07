from src.scout_data import ScoutData
from src.boundary import Boundary

if __name__ == "__main__":
    scout_data = ScoutData()
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("ctry", ["S92000003"])
    scout_data.filter_records("postcode_is_valid", [1])
    scout_data.add_imd_decile()

    boundary = Boundary("imd_decile", scout_data)
    boundary.create_boundary_report(["Section numbers"], report_name="scotland_2019_imd_report", exec_tm=True)

    scout_data.close()
