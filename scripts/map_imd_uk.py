"""Scouting by Lower Super Output Area.

This script produces a report of the Sections in England and Wales and plots them on a map with a base layer of the
Index of Multiple Deprivation Deciles.

This script has no command line options.
"""
import time

from incognita.data.scout_data import ScoutData
from incognita.logger import logger
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    countries = {"England", "Wales"}
    country_codes = {"E92000001", "W92000004"}

    # setup data
    scout_data = ScoutData()
    scout_data.census_data = filter.filter_records(scout_data.census_data, "Census_ID", {20})
    scout_data.census_data = filter.filter_records(scout_data.census_data, "X_name", countries)
    scout_data.census_data = filter.filter_records(scout_data.census_data, "type", {"Colony", "Pack", "Troop", "Unit"})
    scout_data.census_data = filter.filter_records(scout_data.census_data, "ctry", country_codes)
    scout_data.census_data = filter.filter_records(scout_data.census_data, "postcode_is_valid", {True}, exclusion_analysis=True)

    lsoa = Reports("LSOA", scout_data)
    lsoa.filter_boundaries("ctry", country_codes)
    lsoa_boundary_report = lsoa.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name="lsoa_ew")

    # iz = Reports("Intermediate Zone", scout_data)
    # iz.filter_boundaries(field="ctry", value_list={"S92000003"})
    # iz_boundary_report = iz.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name="iz_all")

    # Create map object
    mapper = Map(map_name="lsoa_ew_map 6")

    # Create 6 to 17 map - IMD deciles
    mapper.add_areas("imd_decile", "IMD", "Index of Multiple Deprivation Decile", lsoa_boundary_report, lsoa.geography.metadata, show=True, colour_bounds=[1, 3, 7, 10])
    # mapper.add_areas("imd_decile", "IMD", "Index of Multiple Deprivation Decile", iz_boundary_report, iz.geography.metadata, show=True)

    # Plot sections
    mapper.add_meeting_places_to_map(
        sections=scout_data.census_data,
        colour_key="D_ID",
        marker_data={"youth membership"},
        cluster_markers=True,
        coloured_region=countries,
        coloured_region_key="X_name",
    )

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    timing.close(start_time)
