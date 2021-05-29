import time

from incognita.data.scout_data import ScoutData
from incognita.geographies import district_boundaries
from incognita.logger import logger
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    region_name = "South West"
    census_id = 20

    scout_data = ScoutData()
    scout_data.census_data = filter.filter_records(scout_data.census_data, "Census_ID", {census_id})
    scout_data.census_data = filter.filter_records(scout_data.census_data, "R_name", {region_name})
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    scout_data.census_data = filter.filter_records(scout_data.census_data, "C_name", {"Bailiwick of Guernsey", "Isle of Man", "Jersey"}, exclude_matching=True)
    scout_data.census_data = filter.filter_records(scout_data.census_data, "postcode_is_valid", {True})

    # generate district boundaries
    district_boundaries.create_district_boundaries(scout_data.census_data)

    # generate boundary report
    reports = Reports("District", scout_data)
    boundary_report = reports.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name="uk_by_district")

    mapper = Map(map_name="uk_by_la_map")
    mapper.add_areas(f"All-{census_id}", "Under 18s", "Scouts aged under 18", boundary_report, reports.geography.metadata, show=True)
    mapper.add_sections_to_map(scout_data, "D_ID", {"youth membership"}, cluster_markers=True)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    timing.close(start_time)
