import time

from incognita.data.scout_data import load_census_data
from incognita.logger import logger
from incognita.reports.reports import Reports
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    county_name = "Gt. London South"
    census_id = 20

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "Census_ID", {census_id})
    census_data = filter.filter_records(census_data, "C_name", {county_name})
    census_data = filter.filter_records(census_data, "postcode_is_valid", {True}, exclusion_analysis=True)

    reports = Reports("IMD Decile", census_data)
    boundary_report = reports.create_boundary_report({"Groups", "Number of Sections", "Section numbers", "waiting list total"}, report_name=f"{county_name} - {census_id} IMD report")

    timing.close(start_time)
