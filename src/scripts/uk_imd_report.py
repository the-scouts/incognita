from src.script_handler import ScriptHandler
from src.scout_map import ScoutMap
import pandas as pd

if __name__ == "__main__":

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.set_boundary,["imd_decile"])
    script_handler.run(ScoutMap.filter_records,["Year",[2019]])
    script_handler.run(ScoutMap.filter_records,["ctry",["S92000003"]])
    script_handler.run(ScoutMap.filter_records,["postcode_is_valid",[1]])
    script_handler.run(ScoutMap.add_IMD_decile)
    script_handler.run(ScoutMap.create_boundary_report,["Section numbers"],"scotland_2019_imd_report")
    script_handler.close()
