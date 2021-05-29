"""Awards Mapping

This script produces a boundary report by local authority district, and plots
the percentage of Chief Scout Bronze Awards awarded between 31st January 2018
and 31st January 2019 of the eligible Beavers. and percentage of QSAs.

This script has no command line options.
"""
from incognita.data.scout_data import ScoutData
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import timing

if __name__ == "__main__":
    census_id = 20

    scout_data = ScoutData()
    scout_data.filter_records("postcode_is_valid", {True})
    scout_data.filter_records("Census_ID", {census_id})
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    scout_data.filter_records("C_name", {"Bailiwick of Guernsey", "Isle of Man", "Jersey"}, exclude_matching=True)

    # Generate boundary report
    reports = Reports("Local Authority", scout_data)
    boundary_report = reports.create_boundary_report({"awards"}, report_name="laua_awards_report")

    # Create map object
    mapper = Map(map_name="UK_QSA_awards")

    # Plot
    mapper.add_areas("%-QSA", "QSA %", "QSA %", boundary_report, reports.geography.metadata, show=True)
    mapper.add_sections_to_map(scout_data, "D_ID", {"youth membership", "awards"}, single_section="Explorers", cluster_markers=True)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    timing.close(scout_data)
