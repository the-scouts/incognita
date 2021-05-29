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
    census_id = 20

    # setup data
    scout_data = ScoutData()
    scout_data.filter_records("Census_ID", {census_id})
    scout_data.filter_records("X_name", {"England", "Scotland", "Wales", "Northern Ireland"})
    scout_data.filter_records("C_name", {"Bailiwick of Guernsey", "Isle of Man", "Jersey"}, exclude_matching=True)
    scout_data.filter_records("type", {"Colony", "Pack", "Troop", "Unit"})
    scout_data.filter_records("C_name", {county_name})
    scout_data.filter_records("postcode_is_valid", {True}, exclusion_analysis=True)

    # # % 6-17 pcon uptake from Jan-2020 Scout Census with May 2019 ONS
    # pcon_reports = Reports("Constituency", scout_data)
    # pcon_reports.filter_boundaries("C_name", {county_name}, "pcon")
    # pcon_boundary_report = pcon_reports.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name=f"{county_name} - westminster constituencies")
    # pcon_reports.create_uptake_report(pcon_boundary_report, report_name=f"{county_name} - westminster constituencies (uptake)")
    #
    # # 6-17 IMD from Jan-2020 Scout Census with May 2019 ONS
    # imd_reports = Reports("LSOA", scout_data)
    # imd_reports.filter_boundaries("C_name", {county_name}, "pcon")
    # imd_boundary_report = imd_reports.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name=f"{county_name} - IMD")
    #
    # # % 6-17 LAs uptake from Jan-2020 Scout Census with May 2019 ONS
    # # lad_reports = Reports("Local Authority", scout_data)
    # # lad_reports.filter_boundaries("C_name", {county_name}, "pcon")
    # # lad_boundary_report = lad_reports.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name=f"{county_name} - local authorities")
    # # lad_reports.create_uptake_report(lad_boundary_report, report_name=f"{county_name} - local authorities (uptake)")
    #
    # # % 6-17 Wards uptake from Jan-2020 Scout Census with May 2019 ONS
    # wards_reports = Reports("Ward", scout_data)
    # wards_reports.filter_boundaries("C_name", {county_name}, "oslaua")
    # wards_boundary_report = wards_reports.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name=f"{county_name} - wards")
    # wards_reports.create_uptake_report(wards_boundary_report, report_name=f"{county_name} - wards (uptake)")

    # % 6-17 LAs uptake from Jan-2020 Scout Census with May 2019 ONS
    nys_reports = Reports("District (NYS)", scout_data)
    nys_reports.filter_boundaries("C_name", {county_name}, "oslaua")
    nys_reports.add_shapefile_data()
    nys_boundary_report = nys_reports.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name=f"{county_name} - nys")
    nys_reports.create_uptake_report(nys_boundary_report, report_name=f"{county_name} - nys (uptake)")

    # Create map object
    mapper = Map(map_name=f"{county_name} uptake map")

    # # Create 6 to 17 map - Westminster Constituencies
    # mapper.add_areas(f"%-All-{census_id}", "% 6-17 Uptake", "% 6-17 Uptake (PCon)", pcon_boundary_report, pcon_reports.geography.metadata, show=True)
    #
    # # Create 6 to 17 map - IMD deciles
    # mapper.add_areas("imd_decile", "IMD", "IMD Decile", imd_boundary_report, imd_reports.geography.metadata)
    #
    # # Create 6 to 17 map - Local Authorities
    # mapper.add_areas(f"%-All-{census_id}", "% 6-17 Uptake", "% 6-17 Uptake (LAs)", lad_boundary_report, lad_reports.geography.metadata)
    #
    # # Create 6 to 17 map - Wards
    # mapper.add_areas(f"%-All-{census_id}", "% 6-17 Uptake", "% 6-17 Uptake (Wards)", wards_boundary_report, wards_reports.geography.metadata)

    # Create 6 to 17 map - Wards
    mapper.add_areas(f"%-All-{census_id}", "% 6-17 Uptake", "% 6-17 Uptake (Districts)", nys_boundary_report, nys_reports.geography.metadata, show=True)

    # Plot sections
    sections_in_county = scout_data.census_data["C_name"] == county_name
    # mapper.add_meeting_places_to_map(
    #     scout_data.census_data.loc[~sections_in_county],
    #     "lightgray",
    #     {"youth membership"},
    #     "Other Sections",
    #     show_layer=False,
    #     coloured_region={county_name},
    #     coloured_region_key="C_name",
    # )
    mapper.add_meeting_places_to_map(
        scout_data.census_data.loc[sections_in_county],
        "D_ID",
        {"youth membership"},
        "Your Sections",
        coloured_region={county_name},
        coloured_region_key="C_name",
    )

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    # create_section_maps
    # for section_label in Reports.SECTION_AGES.keys():
    #     section_map = Map(map_name=f"pcon_uptake_report_{section_label}")
    #     section_map.add_areas(f"%-{section_label}-{year}", section_label, f"{year} {section_label} uptake (%)", pcon_boundary_report, pcon_reports.geography.metadata, colour_bounds=[0, 3, 4, 6, 8, 11])
    #     section_map.add_sections_to_map(scout_data, section_map.district_colour_mapping(scout_data), {"youth membership"}, single_section=section_label)
    #     section_map.save_map()

    # get script execution time etc.
    scout_data.close()
