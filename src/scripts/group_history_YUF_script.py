from geo_scout.src.script_handler import ScriptHandler
from geo_scout.src.scout_map import ScoutMap
import pandas as pd

if __name__ == "__main__":

    # Read group list - with a column headed "G_ID"
    groups = pd.read_csv(r"Output\yuf_groups.csv")
    group_ids = groups["G_ID"].unique()
    group_ids = [str(int(group)) for group in group_ids if str(group) != "nan"]

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.filter_records,["G_ID", group_ids])
    script_handler.run(ScoutMap.add_IMD_decile)
    script_handler.run(ScoutMap.group_history_summary, [["2010","2011","2012","2013","2014","2015","2016","2017","2018","2019"]], "YUF_group_history")
