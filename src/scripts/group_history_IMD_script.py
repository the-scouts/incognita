from script_handler import ScriptHandler
from scout_map import ScoutMap
import pandas as pd

if __name__ == "__main__"

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.add_IMD_decile)
    script_handler.run(ScoutMap.filter_records,["imd_decile", [1,2]])
    script_handler.run(ScoutMap.group_history_summary, [["2010","2011","2012","2013","2014","2015","2016","2017","2018","2019"]], "low_IMD_group_history")
