"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""
from incognita.data.scout_data import ScoutData
from incognita.maps.map import Map
from incognita.reports.reports import Reports

if __name__ == "__main__":
    county_name = "North Yorkshire"
    year = 2020

    # setup data
    scout_data = ScoutData()
    scout_data.filter_records("Year", {year})
    scout_data.filter_records("X_name", {"England", "Scotland", "Wales", "Northern Ireland"})
    scout_data.filter_records("C_name", {"Bailiwick of Guernsey", "Isle of Man", "Jersey"}, mask=True)
    scout_data.filter_records("type", {"Colony", "Pack", "Troop", "Unit"})
    scout_data.filter_records("C_name", {county_name})
    scout_data.filter_records("postcode_is_valid", {1}, exclusion_analysis=True)

    # # % 6-17 pcon uptake from Jan-2020 Scout Census with May 2019 ONS
    # pcon_reports = Reports("Constituency", scout_data)
    # pcon_reports.filter_boundaries("C_name", {county_name}, "pcon")
    # pcon_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name=f"{county_name} - westminster constituencies")
    # pcon_reports.create_uptake_report(report_name=f"{county_name} - westminster constituencies (uptake)")
    #
    # # 6-17 IMD from Jan-2020 Scout Census with May 2019 ONS
    # imd_reports = Reports("LSOA", scout_data)
    # imd_reports.filter_boundaries("C_name", {county_name}, "pcon")
    # imd_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name=f"{county_name} - IMD")
    #
    # # % 6-17 LAs uptake from Jan-2020 Scout Census with May 2019 ONS
    # # lad_reports = Reports("Local Authority", scout_data)
    # # lad_reports.filter_boundaries("C_name", {county_name}, "pcon")
    # # lad_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name=f"{county_name} - local authorities")
    # # lad_reports.create_uptake_report(report_name=f"{county_name} - local authorities (uptake)")
    #
    # # % 6-17 Wards uptake from Jan-2020 Scout Census with May 2019 ONS
    # wards_reports = Reports("Ward", scout_data)
    # wards_reports.filter_boundaries("C_name", {county_name}, "oslaua")
    # wards_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name=f"{county_name} - wards")
    # wards_reports.create_uptake_report(report_name=f"{county_name} - wards (uptake)")

    # % 6-17 LAs uptake from Jan-2020 Scout Census with May 2019 ONS
    nys_reports = Reports("District (NYS)", scout_data)
    nys_reports.filter_boundaries("C_name", {county_name}, "oslaua")
    nys_reports.add_shapefile_data()
    nys_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name=f"{county_name} - nys")
    nys_reports.create_uptake_report(report_name=f"{county_name} - nys (uptake)")

    # Create map object
    mapper = Map(map_name=f"{county_name} uptake map")

    # # Create 6 to 17 map - Westminster Constituencies
    # mapper.add_areas(f"%-All-{year}", "% 6-17 Uptake", "% 6-17 Uptake (PCon)", pcon_reports, show=True)
    #
    # # Create 6 to 17 map - IMD deciles
    # mapper.add_areas("imd_decile", "IMD", "IMD Decile", imd_reports)
    #
    # # Create 6 to 17 map - Local Authorities
    # mapper.add_areas(f"%-All-{year}", "% 6-17 Uptake", "% 6-17 Uptake (LAs)", lad_reports)
    #
    # # Create 6 to 17 map - Wards
    # mapper.add_areas(f"%-All-{year}", "% 6-17 Uptake", "% 6-17 Uptake (Wards)", wards_reports)

    # Create 6 to 17 map - Wards
    mapper.add_areas(f"%-All-{year}", "% 6-17 Uptake", "% 6-17 Uptake (Districts)", nys_reports, show=True)

    # Plot sections
    mapper.set_region_of_colour("C_name", {county_name})
    # mapper.add_meeting_places_to_map(scout_data.census_data.loc[~(scout_data.census_data["C_name"] == county_name)], "lightgray", ["youth membership"], "Other Sections", show_layer=False)
    mapper.add_meeting_places_to_map(scout_data.census_data.loc[scout_data.census_data["C_name"] == county_name], mapper.district_colour_mapping(scout_data), ["youth membership"], "Your Sections")

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    # create_section_maps
    # for section_label in Reports.SECTION_AGES.keys():
    #     section_map = Map(map_name=f"pcon_uptake_report_{section_label}")
    #     section_map.add_areas(f"%-{section_label}-{year}", section_label, f"{year} {section_label} uptake (%)", pcon_reports, scale_index=[0, 8, 20], scale_step_boundaries=[0, 3, 4, 6, 8, 11])
    #     section_map.add_sections_to_map(scout_data, section_map.district_colour_mapping(scout_data), ["youth membership"], single_section=section_label)
    #     section_map.save_map()

    # get script execution time etc.
    scout_data.close()
