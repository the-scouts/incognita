from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19
from src.reports.reports import Reports
from src.data.scout_data import ScoutData
from src.maps.map import Map

if __name__ == "__main__":

    scout_data = ScoutData(load_ons_pd_data=False)
    scout_data.filter_records("Year", [2015, 2016, 2017, 2018, 2019])
    scout_data.filter_records("postcode_is_valid", [1])
    scout_data.filter_records("C_ID", [10000122])
    scout_data.add_imd_decile()

    map = Map(scout_data, map_name="central_yorkshire")

    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    ons_pd = ONSPostcodeDirectoryMay19(scout_data.settings["ONS PD location"], load_data=True)
    reports = Reports("lsoa", scout_data, ons_pd)
    reports.filter_boundaries("C_ID", [10000122], "oslaua")
    reports.create_boundary_report(["Section numbers"], historical=True, report_name="central_yorkshire_by_lsoa8")   # TODO: before postcode filtering
    map.add_areas(dimension, reports, show=True)

    map.add_sections_to_map(scout_data, map.district_colour_mapping(), ["youth membership"])
    map.save_map()
    map.show_map()
    scout_data.close()
