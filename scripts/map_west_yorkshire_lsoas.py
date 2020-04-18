from src.data.scout_data import ScoutData
from src.reports.reports import Reports
from src.maps.map import Map

if __name__ == "__main__":
    county_name = "Central Yorkshire"
    year = 2020

    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("Year", [year])
    scout_data.filter_records("C_name", [county_name])
    scout_data.filter_records("postcode_is_valid", [1])

    reports = Reports("lsoa", scout_data)
    reports.filter_boundaries("C_name", [county_name], "oslaua")
    reports.create_boundary_report(["Section numbers"], historical=True, report_name=f"{county_name} by LSOA")  # TODO: before postcode filtering

    mapper = Map(scout_data, map_name=f"{county_name}")

    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    mapper.add_areas(dimension, reports, show=True)
    mapper.add_sections_to_map(scout_data, mapper.district_colour_mapping(), ["youth membership"])

    mapper.save_map()
    mapper.show_map()
    scout_data.close()
