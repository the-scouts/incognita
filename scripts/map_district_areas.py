from src.data.scout_data import ScoutData
from src.maps.map import Map
from src.geographies.district_boundaries import DistrictBoundaries
from src.reports.reports import Reports

if __name__ == "__main__":
    year = 2020

    scout_data = ScoutData()
    scout_data.filter_records("Year", [year])
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("R_Name", ["South West"])
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)

    # generate district boundaries
    district_boundaries = DistrictBoundaries(scout_data)
    district_boundaries.create_district_boundaries()

    # create boundary report
    reports = Reports("District", scout_data)
    reports.create_boundary_report(["Section numbers", "6 to 17 numbers", "awards"], report_name="scout_district_report")

    # create map object
    mapper = Map(scout_data, map_name="UK_Bronze_district")

    # plot maps
    dimension = {"column": "%-Chief_Scout_Bronze_Awards", "tooltip": "% Bronze", "legend": "% Bronze"}
    mapper.add_areas(dimension, reports, show=True)
    mapper.add_sections_to_map(scout_data, mapper.district_colour_mapping(), ["youth membership", "awards"], single_section="Beavers", cluster_markers=True)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    scout_data.close()
