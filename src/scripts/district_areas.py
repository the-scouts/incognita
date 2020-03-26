from data.scout_data import ScoutData
from geographies.geography import Geography
from maps.map import Map
from geographies.district_boundaries import DistrictBoundaries
from reports.reports import Reports

if __name__ == "__main__":
    scout_data = ScoutData()

    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("R_ID", [10000046])
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    scout_data.filter_records("D_ID", [10001886, 10001334, 10001332], mask=True)

    district_boundaries = DistrictBoundaries(scout_data)
    district_boundaries.create_district_boundaries()

    boundary = Geography("District", scout_data.ons_pd)

    reports = Reports(scout_data, boundary)
    reports.create_boundary_report(["Section numbers", "6 to 17 numbers", "awards"], report_name="scout_district_report")

    dimension = {"column": "%-Chief_Scout_Bronze_Awards", "tooltip": "% Bronze", "legend": "% Bronze"}
    map = Map(scout_data, map_name="UK_Bronze_district", cluster_markers=True)
    map.add_areas(dimension, boundary, reports, show=True)
    map.add_sections_to_map(map.district_colour_mapping(), ["youth membership", "awards"], single_section="Beavers")
    map.save_map()
    map.show_map()
    scout_data.close()
