from geo_scout.src.script_handler import ScriptHandler
from geo_scout.src.scout_map import ScoutMap

if __name__ == "__main__":

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.add_IMD_decile)
    sections = script_handler.run(ScoutMap.filter_records, [["imd_decile"],[1,2]])
