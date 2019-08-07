from src.scout_data import ScoutData
from src.boundary import Boundary
from src.map import Map

if __name__ == "__main__":
    scout_data = ScoutData(csv_has_ons_pd_data=True, load_ons_pd_data=True)
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("oslaua", ["E08000035"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    boundary = Boundary("lsoa", scout_data)
    boundary.filter_boundaries("oslaua", ["E08000035"])
    boundary.create_boundary_report(["Section numbers", False], report_name="leeds_sections")

    dimension = {"column": "Beavers-2019", "tooltip": "Beavers 2019", "legend": "# Beavers"}
    map = Map(scout_data, boundary, dimension, map_name="Leeds")
    map.add_custom_data("../../data/National Statistical data/leeds_primary_schools.csv",
                        "Primary Schools",
                        location_cols="Postcode",
                        marker_data=["EstablishmentName"])
    map.add_sections_to_map(map.district_colour_mapping(), ["youth membership"], single_section="Beavers")
    map.save_map()
    map.show_map()
    # scout_data.close()
