"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""
from base import time_function
from data.scout_data import ScoutData
from geographies.geography import Geography
from maps.map import Map
from reports.reports import Reports

if __name__ == "__main__":
    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    map = Map(scout_data, map_name="pcon_uk_uptake_map")

    # % 6-17 pcon uptake from Jan-2019 Scout Census with May 2019 ONS
    max_year = scout_data.data["Year"].max()
    dimension = {"column": f"%-All-{max_year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake"}
    boundary = Geography("pcon", scout_data.ons_pd)
    # time_function(boundary.filter_boundaries_near_scout_area)("pcon" , "C_ID", [10000122])
    reports = Reports(boundary, scout_data)
    time_function(reports.create_boundary_report)(["Section numbers", "6 to 17 numbers"], historical=True, report_name="pcon_county")
    time_function(reports.create_uptake_report)(report_name="pcon_uk_uptake_report")
    # create_6_to_17_map
    map.add_areas(dimension, boundary, reports, show=True)

    # map.set_region_of_colour("C_name", ["Central Yorkshire"])
    # map.map_plotter.add_layer(name='Your Sections', markers_clustered=False, show=True)
    # map.map_plotter.add_layer(name='Other Sections', markers_clustered=False, show=False)
    # map.add_meeting_places_to_map(scout_data.data.loc[~(scout_data.data["C_name"] == "Central Yorkshire")], 'lightgray', ["youth membership"], 'Other Sections')
    # map.add_meeting_places_to_map(scout_data.data.loc[scout_data.data["C_name"] == "Central Yorkshire"], map.district_colour_mapping(), ["youth membership"], 'Your Sections')
    map.add_meeting_places_to_map(scout_data.data, map.district_colour_mapping(), ["youth membership"], 'Sections', cluster_markers=True)
    map.save_map()

    # static_scale = {"index": [0, 8, 20], "min": 0, "max": 20, "boundaries": [0, 3, 4, 6, 8, 11]}
    # create_section_maps
    # for section_label in Geography.SECTION_AGES.keys():
    #     dimension = {"column": f"%-{section_label}-{max_year}", "tooltip": section_label, "legend": f"{max_year} {section_label} uptake (%)"}
    #     section_map = Map(scout_data, boundary, dimension, map_name=f"pcon_uptake_report_{section_label}", static_scale=static_scale)
    #     section_map.add_sections_to_map(scout_data, section_map.district_colour_mapping(), ["youth membership"], single_section=section_label)
    #     section_map.save_map()

    scout_data.close()
