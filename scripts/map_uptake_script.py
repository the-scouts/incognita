"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""
from src.data.scout_data import ScoutData
from src.reports.reports import Reports
from src.maps.map import Map

if __name__ == "__main__":
    county_name = "Central Yorkshire"
    year = 2020

    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("C_name", [county_name])
    scout_data.filter_records("Year", [year])
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    map = Map(scout_data, map_name=f"{county_name} uptake map")

    # % 6-17 pcon uptake from Jan-2020 Scout Census with May 2019 ONS
    pcon_reports = Reports("pcon", scout_data)
    pcon_reports.filter_boundaries("C_name", [county_name], "pcon")
    pcon_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name=f"{county_name} - westminster constituencies")
    pcon_reports.create_uptake_report(report_name=f"{county_name} - westminster constituencies (uptake)")

    imd_reports = Reports("lsoa", scout_data)
    imd_reports.filter_boundaries("C_name", [county_name], "pcon")
    imd_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name=f"{county_name} - IMD")

    # lad = Reports("lad", scout_data)
    # lad.filter_boundaries("C_name", [county_name], "pcon")
    # lad.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name=f"{county_name} - local authorities")
    # lad.create_uptake_report(report_name="las_wales_uptake_report")

    # Create 6 to 17 map - Westminster Constituencies
    static_scale = {"index": [0, 8, 20], "min": 0, "max": 20, "boundaries": [0, 3, 4, 6, 8, 11]}
    dimension = {"column": f"%-All-{year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake (PCon)"}
    map.add_areas(dimension, pcon_reports, show=True)

    # Create 6 to 17 map - IMD deciles
    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    map.add_areas(dimension, imd_reports)

    # Create 6 to 17 map - Local Authorities
    # dimension = {"column": f"%-All-{year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake (LAs)"}
    # map.add_areas(dimension, lad)

    # Plotting the sections
    map.set_region_of_colour("C_name", [county_name])
    map.map_plotter.add_layer(name="Your Sections", markers_clustered=False, show=True)
    map.map_plotter.add_layer(name="Other Sections", markers_clustered=False, show=False)
    map.add_meeting_places_to_map(scout_data.data.loc[~(scout_data.data["C_name"] == county_name)], "lightgray", ["youth membership"], "Other Sections")
    map.add_meeting_places_to_map(scout_data.data.loc[scout_data.data["C_name"] == county_name], map.district_colour_mapping(), ["youth membership"], "Your Sections")
    map.save_map()
    map.show_map()

    # create_section_maps
    # for section_label in Reports.SECTION_AGES.keys():
    #     dimension = {"column": f"%-{section_label}-{year}", "tooltip": section_label, "legend": f"{year} {section_label} uptake (%)"}
    #     section_map = Map(scout_data, map_name=f"pcon_uptake_report_{section_label}")
    #     section_map.add_areas(dimension, pcon_reports, scale=static_scale)
    #     section_map.add_sections_to_map(scout_data, section_map.district_colour_mapping(), ["youth membership"], single_section=section_label)
    #     section_map.save_map()

    scout_data.close()
