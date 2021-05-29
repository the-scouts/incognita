import time

from incognita.data.scout_data import load_census_data
from incognita.logger import logger
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    county_name = "Birmingham"
    census_id = 21

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "Census_ID", {census_id})  # 16, 17, 18, 19, 20
    census_data = filter.filter_records(census_data, "C_name", {county_name})  # "Shropshire", "West Mercia"
    census_data = filter.filter_records(census_data, "postcode_is_valid", {True})

    reports = Reports("LSOA", census_data)
    reports.filter_boundaries("C_name", {county_name}, "oslaua")
    boundary_report = reports.create_boundary_report({"Section numbers"}, report_name=f"{county_name} by LSOA")  # TODO: before postcode filtering
    # boundary_report = reports.create_boundary_report({"Section numbers"}, historical=True, report_name=f"{county_name}_by_lsoa")  # TODO: before postcode filtering

    # Create map object
    mapper = Map(map_name=f"{county_name}", map_title=f"{county_name} Sections by IMD Decile")

    # Plot
    mapper.add_areas("imd_decile", "IMD", "IMD Decile", boundary_report, reports.geography.metadata, show=True, significance_threshold=0)
    mapper.add_sections_to_map(census_data, "D_ID", {"youth membership"}, coloured_region={county_name}, coloured_region_key="C_name")

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    timing.close(start_time)
