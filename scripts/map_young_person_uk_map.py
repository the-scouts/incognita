from src.data.scout_data import ScoutData
from src.maps.map import Map
from src.reports.reports import Reports

if __name__ == "__main__":

    scout_data = ScoutData()
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("postcode_is_valid", [1])
    scout_data.filter_records("X_name", ["England", "Wales", "Scotland", "Northern Ireland"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("C_name", ["Cornwall"])

    map = Map(scout_data, map_name="uk_by_la_map")

    dimension = {"column": "All-2019", "tooltip": "Under 18s", "legend": "Scouts aged under 18"}
    reports = Reports("District", scout_data)
    reports.create_boundary_report(options=["Section numbers", "6 to 17 numbers"], report_name="uk_by_district")
    map.add_areas(dimension, reports, show=True)

    map.add_sections_to_map(scout_data, map.district_colour_mapping(), ["youth membership"], cluster_markers=True)
    map.save_map()

    # create_section_maps
    # for section_label in Geography.SECTION_AGES.keys():
    #     dimension = {"column": f"{section_label}-{scout_data.data["Year"].max()}", "tooltip": section_label, "legend": f"{scout_data.data["Year"].max()} {section_label} numbers"}
    #     section_map = Map(scout_data, boundary, dimension, map_name=f"uk_by_la_{section_label}", cluster_markers=True)
    #     section_map.add_sections_to_map(scout_data, section_map.district_colour_mapping(), ["youth membership"], single_section=section_label)
    #     section_map.save_map()

    scout_data.close()
