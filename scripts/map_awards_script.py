"""Awards Mapping

This script produces a boundary report by local authority district, and plots
the percentage of Chief Scout Bronze Awards awarded between 31st January 2018
and 31st January 2019 of the eligible Beavers. and percentage of QSAs.

This script has no command line options.
"""
import time

from incognita.data.scout_census import load_census_data
from incognita.logger import logger
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    census_id = 20

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "postcode_is_valid", {True})
    census_data = filter.filter_records(census_data, "Census_ID", {census_id})
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    census_data = filter.filter_records(census_data, "C_name", {"Bailiwick of Guernsey", "Isle of Man", "Jersey"}, exclude_matching=True)

    # Generate boundary report
    reports = Reports("Local Authority", census_data)
    boundary_report = reports.create_boundary_report({"awards"}, report_name="laua_awards_report")

    # Create map object
    mapper = Map(map_name="UK_QSA_awards")

    # Plot
    mapper.add_areas("%-QSA", "QSA %", "QSA %", boundary_report, reports.geography.metadata, show=True)
    mapper.add_sections_to_map(census_data, "D_ID", {"youth membership", "awards"}, single_section="Explorers", cluster_markers=True)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    timing.close(start_time)
