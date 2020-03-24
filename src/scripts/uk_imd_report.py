from src.scout_data import ScoutData
from src.geography import Geography

if __name__ == "__main__":
    scout_data = ScoutData()
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("C_name",["Gt. London South"])
    #scout_data.filter_records("oslaua", ["E08000025","E08000026","E08000027","E08000028",
    #                                    "E08000029","E08000030","E08000031"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)
    scout_data.add_imd_decile()

    boundary = Geography("imd_decile", scout_data)
    boundary.create_boundary_report(["Groups", "Number of Groups", "Number of Sections", "Section numbers", "waiting list total"], report_name="gt_london_south_2019_imd_report", exec_tm=True)

    scout_data.close()
