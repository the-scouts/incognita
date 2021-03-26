from incognita.data.scout_data import ScoutData
from incognita.maps.map import Map
from incognita.reports.reports import Reports

if __name__ == "__main__":
    county_name = "Birmingham"
    year = 2020

    scout_data = ScoutData()
    scout_data.filter_records("Year", {year})  # 2016, 2017, 2018, 2019, 2020
    scout_data.filter_records("C_name", {county_name})  # "Shropshire", "West Mercia"
    scout_data.filter_records("postcode_is_valid", {1})

    reports = Reports("LSOA", scout_data)
    reports.filter_boundaries("C_name", {county_name}, "oslaua")
    reports.create_boundary_report(["Section numbers"], report_name=f"{county_name} by LSOA")  # TODO: before postcode filtering
    # reports.create_boundary_report(["Section numbers"], historical=True, report_name=f"{county_name}_by_lsoa")  # TODO: before postcode filtering

    # Create map object
    mapper = Map(map_name=f"{county_name}")

    # Plot
    mapper.add_areas("imd_decile", "IMD", "IMD Decile", reports, show=True, significance_threshold=0)
    mapper.add_sections_to_map(scout_data, mapper.county_colour_mapping(scout_data), {"youth membership"}, coloured_region={county_name}, coloured_region_key="C_name")

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    scout_data.close()
