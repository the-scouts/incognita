from src.script_handler import ScriptHandler
from src.scout_map import ScoutMap
import pandas as pd

if __name__ == "__main__":

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.set_boundary,["District"])
    script_handler.run(ScoutMap.filter_records,["Year",[2019]])
    script_handler.run(ScoutMap.filter_records,["postcode_is_valid",[1]])
    script_handler.run(ScoutMap.filter_records,["X_name",["England", "Wales", "Scotland", "Northern Ireland"]])
    #script_handler.run(ScoutMap.filter_records,["R_ID", [10000046]])
    script_handler.run(ScoutMap.filter_records,["C_name", ["Cornwall"]])
    script_handler.run(ScoutMap.filter_records,["C_name",["Bailiwick of Guernsey", "Isle of Man", "Jersey"], True])
    script_handler.run(ScoutMap.create_boundary_report,[["Section numbers", "6 to 17 numbers"]] ,"uk_by_district")
    #script_handler.run(ScoutMap.load_boundary_report, ["uk_by_district"])
    script_handler.run(ScoutMap.create_map,["All-2019","Under 18s","uk_by_la_map","Scouts aged under 18", None, True])
    script_handler.run(ScoutMap.add_all_sections_to_map, [script_handler.map.district_color_mapping(), ["youth membership"]])
    script_handler.run(ScoutMap.save_map)
    #script_handler.run(ScoutMap.create_section_maps, ["uk_by_la", None, "Numbers", True])
    script_handler.close()
