from src.data.scout_data import ScoutData
from src.reports.reports import Reports
from src.maps.map import Map

if __name__ == "__main__":
    county_name = "Shropshire"
    county_name2 = "West Mercia"

    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("C_Name", [county_name, county_name2])
    scout_data.filter_records("Year", [2016, 2017, 2018, 2019, 2020])
    scout_data.filter_records("postcode_is_valid", [1])

    reports = Reports("lsoa", scout_data)
    reports.filter_boundaries("C_Name", [county_name, county_name2], "oslaua")
    reports.create_boundary_report(["Section numbers"], historical=True, report_name=f"{county_name}_by_lsoa")  # TODO: before postcode filtering

    # Create map object
    mapper = Map(scout_data, map_name=f"{county_name}")

    # Plot
    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    mapper.add_areas(dimension, reports, show=True)
    mapper.set_region_of_colour("C_Name", [county_name])
    mapper.add_sections_to_map(scout_data, mapper.district_colour_mapping(), ["youth membership"])

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    scout_data.close()
