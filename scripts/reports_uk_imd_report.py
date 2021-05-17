from incognita.data.scout_data import ScoutData
from incognita.reports.reports import Reports

if __name__ == "__main__":
    county_name = "Gt. London South"
    census_id = 20

    scout_data = ScoutData()
    scout_data.filter_records("Census_ID", {census_id})
    scout_data.filter_records("C_name", {county_name})
    scout_data.filter_records("postcode_is_valid", {True}, exclusion_analysis=True)

    reports = Reports("IMD Decile", scout_data)
    reports.create_boundary_report({"Groups", "Number of Sections", "Section numbers", "waiting list total"}, report_name=f"{county_name} - {census_id} IMD report")

    scout_data.close()
