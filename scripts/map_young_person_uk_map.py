from src.data.scout_data import ScoutData
from src.reports.reports import Reports
from src.maps.map import Map

if __name__ == "__main__":
    county_name = "Cornwall"
    year = 2020

    scout_data = ScoutData()
    scout_data.filter_records("Year", [year])
    scout_data.filter_records("postcode_is_valid", [1])
    scout_data.filter_records("X_name", ["England", "Wales", "Scotland", "Northern Ireland"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("C_name", [county_name])

    # generate boundary report
    reports = Reports("District", scout_data)
    reports.create_boundary_report(options=["Section numbers", "6 to 17 numbers"], report_name="uk_by_district")

    mapper = Map(scout_data, map_name="uk_by_la_map")

    dimension = {"column": "All-2019", "tooltip": "Under 18s", "legend": "Scouts aged under 18"}
    mapper.add_areas(dimension, reports, show=True)
    mapper.add_sections_to_map(scout_data, mapper.district_colour_mapping(), ["youth membership"], cluster_markers=True)

    mapper.save_map()

    scout_data.close()
