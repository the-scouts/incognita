from geo_scout.src.script_handler import ScriptHandler
from geo_scout.src.scout_map import ScoutMap

if __name__ == "__main__":

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.filter_records, ["X_name",["England", "Scotland","Wales","Northern Ireland"]])
    script_handler.run(ScoutMap.add_IMD_decile)
    script_handler.run(ScoutMap.filter_records, ["Year", "2019"])
    script_handler.close()
