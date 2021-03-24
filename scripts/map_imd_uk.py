"""Scouting by Lower Super Output Area.

This script produces a report of the Sections in England and Wales and plots them on a map with a base layer of the
Index of Multiple Deprivation Deciles.

This script has no command line options.
"""
from incognita.data.scout_data import ScoutData
from incognita.maps.map import Map
from incognita.reports.reports import Reports

if __name__ == "__main__":
    countries = {"England", "Wales"}
    country_codes = {"E92000001", "W92000004"}

    # setup data
    scout_data = ScoutData()
    scout_data.filter_records("Year", {2020})
    scout_data.filter_records("X_name", countries)
    scout_data.filter_records("type", {"Colony", "Pack", "Troop", "Unit"})
    scout_data.filter_records("ctry", country_codes)
    scout_data.filter_records("postcode_is_valid", {1}, exclusion_analysis=True)

    lsoa = Reports("LSOA", scout_data)
    lsoa.filter_boundaries("ctry", country_codes)
    lsoa.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name="lsoa_ew")

    # iz = Reports("Intermediate Zone", scout_data)
    # iz.filter_boundaries(field="ctry", value_list={"S92000003"})
    # iz.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name="iz_all")

    # Create map object
    mapper = Map(map_name="lsoa_ew_map 6")

    # Create 6 to 17 map - IMD deciles
    mapper.add_areas("imd_decile", "IMD", "Index of Multiple Deprivation Decile", lsoa, show=True, scale_index=[1, 3, 7, 10], scale_step_boundaries=[1, 3, 7, 10])
    # mapper.add_areas("imd_decile", "IMD", "Index of Multiple Deprivation Decile", iz, show=True)

    # Plot sections
    mapper.set_region_of_colour("X_name", countries)
    mapper.add_meeting_places_to_map(sections=scout_data.census_data, colour=mapper.district_colour_mapping(scout_data), marker_data=["youth membership"], cluster_markers=True)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    scout_data.close()
