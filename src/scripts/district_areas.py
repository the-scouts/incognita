from src.script_handler import ScriptHandler
from src.scout_map import ScoutMap

if __name__ == "__main__":

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.filter_records, ["Year", [2019]])
    script_handler.run(ScoutMap.filter_records, ["X_name", ["England", "Scotland", "Wales", "Northern Ireland"]])
    #script_handler.run(ScoutMap.filter_records, ["R_ID", [10000046]])
    #script_handler.run(ScoutMap.filter_records, ["C_name", ["Cornwall"]])
    #script_handler.run(ScoutMap.filter_records, ["D_name", ["North Dorset", "East Somerset"]])
    # Remove Jersey, Guernsey, and Isle of Man as they don't have lat long coordinates in their postcodes
    script_handler.run(ScoutMap.filter_records, ["D_ID", [10001886, 10001334, 10001332], True])
    script_handler.run(ScoutMap.create_district_boundaries)
    script_handler.run(ScoutMap.set_boundary,["District"])
    script_handler.run(ScoutMap.create_boundary_report, [["Section numbers", "6 to 17 numbers"]], "scout_district_report")
    script_handler.run(ScoutMap.create_map, ["All-2019", "2019", "SW_membership_district", "Under 18s", None, True])
    script_handler.run(ScoutMap.add_all_sections_to_map, [script_handler.map.district_color_mapping(), ["youth membership"]])
    script_handler.run(ScoutMap.save_map)
    script_handler.run(ScoutMap.show_map)
    script_handler.close()
