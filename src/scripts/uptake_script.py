"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""

from src.scout_data import ScoutData
from src.boundary import Boundary
from src.map import Map

if __name__ == "__main__":
    scout_data = ScoutData()
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("Year", [2014, 2015, 2016, 2017, 2018, 2019])
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    boundary = Boundary("pcon", scout_data)
    boundary.create_boundary_report(["Groups", "Section numbers", "6 to 17 numbers", "Waiting List"], historical=True, report_name="pcon_report")
    boundary.create_uptake_report(report_name="pcon_uptake_report")

    static_scale = {"index": [0, 8, 20], "min": 0, "max": 20, "boundaries": [0, 5, 8, 11, 14, 20]}

    max_year = scout_data.max_year

    # create_6_to_17_map
    dimension = {"column": f"%-All-{max_year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake"}
    map = Map(scout_data, boundary, dimension, map_name="pcon_uptake_report", static_scale=static_scale)
    map.add_sections_to_map(map.district_colour_mapping(), ["youth membership"])
    map.save_map()

    # create_section_maps
    for section_label in Boundary.SECTION_AGES.keys():
        dimension = {"column": f"%-{section_label}-{max_year}", "tooltip": section_label, "legend": f"{max_year} {section_label} uptake (%)"}
        section_map = Map(scout_data, boundary, dimension, map_name=f"pcon_uptake_report_{section_label}", static_scale=static_scale)
        section_map.add_sections_to_map(section_map.district_colour_mapping(), ["youth membership"], single_section=section_label)
        section_map.save_map()

    scout_data.close()
