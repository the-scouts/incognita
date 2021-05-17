from incognita.data.scout_data import ScoutData
from incognita.geographies import district_boundaries
from incognita.maps.map import Map
from incognita.reports.reports import Reports

if __name__ == "__main__":
    region_name = "South West"
    census_id = 20

    scout_data = ScoutData()
    scout_data.filter_records("Census_ID", {census_id})
    scout_data.filter_records("R_name", {region_name})
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    scout_data.filter_records("C_name", {"Bailiwick of Guernsey", "Isle of Man", "Jersey"}, mask=True)
    scout_data.filter_records("postcode_is_valid", {True})

    # generate district boundaries
    district_boundaries.create_district_boundaries(scout_data.census_data)

    # generate boundary report
    reports = Reports("District", scout_data)
    reports.create_boundary_report({"Section numbers", "6 to 17 numbers"}, report_name="uk_by_district")

    mapper = Map(map_name="uk_by_la_map")
    mapper.add_areas(f"All-{census_id}", "Under 18s", "Scouts aged under 18", reports, show=True)
    mapper.add_sections_to_map(scout_data, "D_ID", {"youth membership"}, cluster_markers=True)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    scout_data.close()
