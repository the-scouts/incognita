from incognita.data.scout_data import ScoutData
from incognita.geographies.district_boundaries import DistrictBoundaries
from incognita.maps.map import Map
from incognita.reports.reports import Reports

if __name__ == "__main__":
    region_name = "South West"
    year = 2020

    scout_data = ScoutData()
    scout_data.filter_records("Year", [year])
    scout_data.filter_records("R_name", [region_name])
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("postcode_is_valid", [1])

    # generate district boundaries
    district_boundaries = DistrictBoundaries(scout_data)
    district_boundaries.create_district_boundaries()

    # generate boundary report
    reports = Reports("District", scout_data)
    reports.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name="uk_by_district")

    mapper = Map(scout_data, map_name="uk_by_la_map")

    dimension = {"column": f"All-{year}", "tooltip": "Under 18s", "legend": "Scouts aged under 18"}
    mapper.add_areas(dimension, reports, show=True)
    mapper.add_sections_to_map(scout_data, mapper.district_colour_mapping(), ["youth membership"], cluster_markers=True)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    scout_data.close()
