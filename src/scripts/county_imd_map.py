from src.script_handler import ScriptHandler
from src.scout_map import ScoutMap
import pandas as pd

if __name__ == "__main__":

    script_handler = ScriptHandler(csv_has_ons_data=True, load_ons_data=True)
    script_handler.run(ScoutMap.set_boundary,["lsoa"])
    script_handler.run(ScoutMap.filter_records,["Year",[2015, 2016, 2017, 2018, 2019]])
    script_handler.run(ScoutMap.set_region_of_color,["C_ID", [10000111]])
    la_list = script_handler.run(ScoutMap.ons_from_scout_area,["oslaua" , "C_ID", [10000111, 10000119]])
    script_handler.run(ScoutMap.filter_records,["oslaua", la_list])
    script_handler.run(ScoutMap.filter_boundaries,["oslaua", la_list])
    script_handler.run(ScoutMap.create_boundary_report,["Section numbers", True],"shropshire_by_lsoa")  # TODO: before postcode filtering
    script_handler.run(ScoutMap.filter_records,["postcode_is_valid",[1]])
    script_handler.run(ScoutMap.add_IMD_decile)
    script_handler.run(ScoutMap.create_map,["imd_decile","IMD","shropshire","IMD Decile", None, False])
    script_handler.run(ScoutMap.add_all_sections_to_map,[script_handler.map.district_color_mapping(), ["youth membership"]])
    script_handler.run(ScoutMap.save_map)
    script_handler.run(ScoutMap.show_map)
    script_handler.close()
