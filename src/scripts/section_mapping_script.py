from geo_scout.src.script_handler import ScriptHandler
from geo_scout.src.scout_map import ScoutMap

if __name__ == "__main__":

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.add_IMD_decile)
    script_handler.run(ScoutMap.group_history_summary, [["2019"]], "2019_groups_with_IMD")
