from src.data.scout_data import ScoutData
from src.maps.map import Map
from src.reports.reports import Reports

if __name__ == "__main__":
    county_name = "Birmingham"
    year = 2020

    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("Year", [year])  # 2016, 2017, 2018, 2019, 2020
    scout_data.filter_records("C_name", [county_name])  # "Shropshire", "West Mercia"
    scout_data.filter_records("postcode_is_valid", [1])

    reports = Reports("lsoa", scout_data)
    reports.filter_boundaries("C_name", [county_name], "oslaua")
    reports.create_boundary_report(["Section numbers"], report_name=f"{county_name} by LSOA")  # TODO: before postcode filtering
    # reports.create_boundary_report(["Section numbers"], historical=True, report_name=f"{county_name}_by_lsoa")  # TODO: before postcode filtering

    # Create map object
    mapper = Map(scout_data, map_name=f"{county_name}")

    # Plot
    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    mapper.add_areas(dimension, reports, show=True, significance_threshold=0)
    mapper.set_region_of_colour("C_name", [county_name])
    mapper.add_sections_to_map(scout_data, mapper.county_colour_mapping(), ["youth membership"])

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    scout_data.close()
