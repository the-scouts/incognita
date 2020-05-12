"""Scouting by Lower Super Output Area.

This script produces a report of the Sections in England and Wales and plots them on a map with a base layer of the
Index of Multiple Deprivation Deciles.

This script has no command line options.
"""
from src.reports.reports import Reports
from src.data.scout_data import ScoutData
from src.maps.map import Map

if __name__ == "__main__":
    countries = ["England", "Wales"]
    country_codes = ["E92000001", "W92000004"]

    # setup data
    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("Year", [2020])
    scout_data.filter_records("X_name", countries)
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("ctry", country_codes)
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    lsoa = Reports("lsoa", scout_data)
    lsoa.filter_boundaries("ctry", country_codes)
    lsoa.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name="lsoa_ew")

    # iz = Reports("iz", scout_data)
    # iz.filter_boundaries(field="ctry", value_list=["S92000003"])
    # iz.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name="iz_all")

    # Create map object
    mapper = Map(scout_data, map_name="lsoa_ew_map 6")

    # Create 6 to 17 map - IMD deciles
    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "Index of Multiple Deprivation Decile"}
    scale = {"min": 1, "max": 10, "index": [1, 3, 7, 10], "boundaries": [1, 3, 7, 10]}
    mapper.add_areas(dimension, lsoa, show=True, scale=scale)
    # map.add_areas(dimension, iz, show=True)

    # Plot sections
    mapper.set_region_of_colour("X_name", countries)
    sections = dict(name="Sections", markers_clustered=True, show=True)
    mapper.add_meeting_places_to_map(sections=scout_data.data, colour=mapper.district_colour_mapping(), marker_data=["youth membership"], layer=sections)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    scout_data.close()
