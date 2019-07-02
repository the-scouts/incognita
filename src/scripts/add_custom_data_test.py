from src.script_handler import ScriptHandler
from src.scout_map import ScoutMap

if __name__ == "__main__":
    script_handler = ScriptHandler(True, True)
    script_handler.run(ScoutMap.filter_records, ["Year", [2019]])
    script_handler.run(ScoutMap.filter_records, ["oslaua", ["E08000035"]])
    script_handler.run(ScoutMap.filter_records, ["postcode_is_valid", [1], False, True])
    script_handler.run(ScoutMap.set_boundary,["lsoa"])
    script_handler.run(ScoutMap.filter_boundaries, ["oslaua", ["E08000035"]])
    script_handler.run(ScoutMap.create_boundary_report, [["Section numbers"], False], "leeds_sections")
    script_handler.run(ScoutMap.create_map, ["Beavers-2019","Beavers 2019","Leeds","# Beavers", None, False])
    script_handler.run(ScoutMap.add_custom_data, ["../../data/National Statistical data/leeds_primary_schools.csv",
                                                  "Primary Schools",
                                                  "Postcodes",
                                                  "Postcode",
                                                  False,
                                                  ["EstablishmentName"]])
    script_handler.run(ScoutMap.add_single_section_to_map,["Beavers", script_handler.map.district_color_mapping(), ["youth membership"]])
    script_handler.run(ScoutMap.save_map)
    script_handler.run(ScoutMap.show_map)
    script_handler.close()
