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

    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    map = Map(scout_data, map_name="pcon_imd_uptake_map")

    # % 6-17 pcon uptake from Jan-2020 Scout Census with May 2019 ONS
    max_year = scout_data.data["Year"].max()
    dimension = {"column": f"%-All-{max_year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake"}
    pcon_reports = Reports("pcon", scout_data)
    pcon_reports.filter_boundaries("C_name", [county_name], "pcon")
    pcon_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name="pcon_central_yorkshire")
    pcon_reports.create_uptake_report(report_name="pcon_uptake_report")
    # create_6_to_17_map
    map.add_areas(dimension, pcon_reports, show=True)

    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    imd_reports = Reports("lsoa", scout_data.ons_pd)
    # pcon list is purely list of all constituency codes remaining
    imd_reports.filter_boundaries("C_name", [county_name], "pcon")
    imd_reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name="imd_central_yorkshire")
    map.add_areas(dimension, imd_reports)

    # Plotting the sections
    map.set_region_of_colour("C_name", [county_name])
    map.map_plotter.add_layer(name="Your Sections", markers_clustered=False, show=True)
    map.map_plotter.add_layer(name="Other Sections", markers_clustered=False, show=False)
    map.add_meeting_places_to_map(scout_data.data.loc[~(scout_data.data["C_name"] == county_name)], "lightgray", ["youth membership"], "Other Sections")
    map.add_meeting_places_to_map(scout_data.data.loc[scout_data.data["C_name"] == county_name], map.district_colour_mapping(), ["youth membership"], "Your Sections")
    map.save_map()

    scout_data.close()
