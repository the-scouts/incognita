from src.scout_data import ScoutData
from src.boundary import Boundary
from src.map import Map

if __name__ == "__main__":

    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("postcode_is_valid", [1])
    scout_data.filter_records("X_name", ["England"])
    scout_data.filter_records("type", ["Colony","Pack","Troop","Unit"])
    scout_data.add_imd_decile()

    boundary = Boundary("lsoa", scout_data)
    boundary.filter_boundaries_near_scout_area("pcon" , "R_name", ["Greater London"], 1000, exec_tm=True)
    boundary.filter_records_by_boundary()
    boundary.create_boundary_report(["Section numbers"], historical=False, report_name="gt_london_by_lsoas")   # TODO: before postcode filtering

    scout_data.filter_records("Year", [2019])

    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    static_scale = {"index": [1, 3, 10], "min": 1, "max": 10, "boundaries": [1, 2, 4, 6, 8, 10], "show": True, "label_suffix": ""}
    map = Map(scout_data, boundary, dimension, map_name="gt_london_imd", scales=[static_scale])

    map.map_plotter.add_layer(name='Your Sections', markers_clustered=False, show=True)
    map.map_plotter.add_layer(name='Other Sections', markers_clustered=False, show=False)
    map.add_meeting_places_to_map(scout_data.data.loc[~(scout_data.data["R_name"] == "Greater London")], 'lightgray', ["youth membership"], 'Other Sections')
    map.add_meeting_places_to_map(scout_data.data.loc[scout_data.data["R_name"] == "Greater London"], map.district_colour_mapping(), ["youth membership"], 'Your Sections')

    map.save_map()
    map.show_map()
    scout_data.close()
