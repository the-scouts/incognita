"""Awards Mapping

This script produces a boundary report by local authority district, and plots
the percentage of Chief Scout Bronze Awards awarded between 31st January 2018
and 31st January 2019 of the eligible Beavers. and percentage of QSAs.

This script has no command line options.
"""

from src.scout_data import ScoutData
from src.geography import Geography
from src.map import Map

if __name__ == "__main__":
    scout_data = ScoutData()
    # scout_data.filter_records("postcode_is_valid", [1])
    scout_data.filter_records("Year", [2019])
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    scout_data.filter_records("D_ID", [10001886, 10001334, 10001332], mask=True)

    boundary = Geography("lad", scout_data)
    boundary.create_boundary_report(options=["awards"], report_name="laua_awards_report")

    dimension = {"column": "%-QSA", "tooltip": "QSA %", "legend": "QSA %"}
    map = Map(scout_data, boundary, dimension, map_name="UK_QSA_awards2", cluster_markers=True)
    map.add_sections_to_map(map.district_colour_mapping(), ["youth membership", "awards"], single_section="Beavers")
    map.save_map()
    map.show_map()
    scout_data.close()
