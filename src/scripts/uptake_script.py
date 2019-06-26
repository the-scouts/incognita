"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""

from src.script_handler import ScriptHandler
from src.scout_map import ScoutMap

if __name__ == "__main__":
    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.set_boundary, ["pcon"])
    script_handler.run(ScoutMap.filter_records, ["X_name", ["England", "Scotland", "Wales", "Northern Ireland"]])
    script_handler.run(ScoutMap.filter_records, ["Year", [2014, 2015, 2016, 2017, 2018, 2019]])
    script_handler.run(ScoutMap.filter_records, ["type", ["Colony", "Pack", "Troop", "Unit"]])
    script_handler.run(ScoutMap.filter_records, ["postcode_is_valid", [1], False, True])

    script_handler.run(ScoutMap.create_boundary_report, [["Groups", "Section numbers", "6 to 17 numbers", "Waiting List"], True], "pcon_report")
    script_handler.run(ScoutMap.create_uptake_report, [], "pcon_uptake_report")
    #static_scale = {"index": [0, 8, 20], "min": 0, "max": 20, "boundaries":[0,5,8,11,14,20]}
    #script_handler.run(ScoutMap.create_6_to_17_map, ["pcon_uptake_report", static_scale])
    #script_handler.run(ScoutMap.create_section_maps, ["pcon_uptake_report", static_scale])
    script_handler.close()
