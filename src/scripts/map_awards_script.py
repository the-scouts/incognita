"""Awards Mapping

This script produces a boundary report by local authority district, and plots
the percentage of Chief Scout Bronze Awards awarded between 31st January 2018
and 31st January 2019 of the eligible Beavers. and percentage of QSAs.

This script has no command line options.
"""

from data.scout_data import ScoutData
from geographies.geography import Geography
from maps.map import Map
from reports.reports import Reports

if __name__ == "__main__":
    scout_data = ScoutData()
    # scout_data.filter_records("postcode_is_valid", [1])
    scout_data.filter_records("Year", [2019])
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    scout_data.filter_records("D_ID", [10001886, 10001334, 10001332], mask=True)

    map = Map(scout_data, map_name="UK_QSA_awards2", cluster_markers=True)

    dimension = {"column": "%-QSA", "tooltip": "QSA %", "legend": "QSA %"}
    boundary = Geography("lad", scout_data.ons_pd)
    reports = Reports(boundary, scout_data)
    reports.create_boundary_report(options=["awards"], report_name="laua_awards_report")
    map.add_areas(dimension, boundary, reports, show=True)

    map.add_sections_to_map(scout_data, map.district_colour_mapping(), ["youth membership", "awards"], single_section="Beavers")
    map.save_map()
    map.show_map()
    scout_data.close()