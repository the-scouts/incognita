import time

from incognita.data.scout_census import load_census_data
from incognita.logger import logger
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import config
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    county_name = "Central Yorkshire"
    la_code = "E08000035"  # Leeds LA code
    census_id = 20

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "Census_ID", {census_id})
    census_data = filter.filter_records(census_data, "oslaua", {la_code})
    census_data = filter.filter_records(census_data, "postcode_is_valid", {True}, exclusion_analysis=True)

    # Generate boundary report
    reports = Reports("LSOA", census_data)
    reports.filter_boundaries("oslaua", {la_code})  # Leeds LA code
    boundary_report = reports.create_boundary_report({"Section numbers"}, report_name="leeds_sections")

    # Create map object
    mapper = Map(map_name="Leeds")

    # Plot
    mapper.add_areas(f"Beavers-{census_id}", f"Beavers {census_id}", "# Beavers", boundary_report, reports.geography.metadata, show=True)
    mapper.add_custom_data(
        config.SETTINGS.folders.national_statistical / "leeds_primary_schools.csv",
        "Primary Schools",
        location_cols="Postcodes",
        marker_data=["EstablishmentName"],
    )
    mapper.add_sections_to_map(census_data, "D_ID", {"youth membership"}, single_section="Beavers")

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    timing.close(start_time)
