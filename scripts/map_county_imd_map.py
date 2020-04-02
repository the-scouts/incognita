from src.data.scout_data import ScoutData
from src.maps.map import Map
from src.reports.reports import Reports

if __name__ == "__main__":
    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("C_ID", [10000111, 10000119])
    scout_data.filter_records("Year", [2015, 2016, 2017, 2018, 2019])
    scout_data.filter_records("postcode_is_valid", [1])
    scout_data.add_imd_decile()

    map = Map(scout_data, map_name="shropshire")

    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    reports = Reports("lsoa", scout_data)
    reports.filter_boundaries("C_ID", [10000111, 10000119], "oslaua")
    reports.create_boundary_report(["Section numbers"], historical=True, report_name="shropshire_by_lsoa")  # TODO: before postcode filtering
    map.add_areas(dimension, reports, show=True)

    map.set_region_of_colour("C_ID", [10000111])
    map.add_sections_to_map(scout_data, map.district_colour_mapping(), ["youth membership"])

    map.save_map()
    map.show_map()
    scout_data.close()
