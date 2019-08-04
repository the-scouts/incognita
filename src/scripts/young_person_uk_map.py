from src.scout_data import ScoutData
from src.boundary import Boundary
from src.map import Map

if __name__ == "__main__":

    scout_data = ScoutData()
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("postcode_is_valid", [1])
    scout_data.filter_records("X_name", ["England", "Wales", "Scotland", "Northern Ireland"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    # scout_data.filter_records("R_ID", [10000046])
    scout_data.filter_records("C_name", ["Cornwall"])

    boundary = Boundary("District", scout_data)
    boundary.create_boundary_report(options=["Section numbers", "6 to 17 numbers"], report_name="uk_by_district")

    dimension = {"column": "All-2019", "tooltip": "Under 18s", "legend": "Scouts aged under 18"}
    map = Map(scout_data, boundary, dimension, map_name="uk_by_la_map", cluster_markers=True)
    map.add_sections_to_map(map.district_colour_mapping(), ["youth membership"])
    map.save_map()

    # # create_section_maps
    # for section_label in ScoutMap.SECTION_AGES.keys():
    #     dimension = {"column": f"{section_label}-{scout_data.max_year}", "tooltip": section_label, "legend": f"{scout_data.max_year} {section_label} numbers"}
    #     section_map = Map(scout_data, boundary, dimension, map_name=f"uk_by_la_{section_label}", cluster_markers=True)
    #     section_map.add_sections_to_map(section_map.district_colour_mapping(), ["youth membership"], single_section=section_label)
    #     section_map.save_map()

    scout_data.close()