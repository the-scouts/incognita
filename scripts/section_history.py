from script_handler import ScriptHandler
from scout_map import ScoutMap

if __name__ == "__main__"

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.add_IMD_decile)
    script_handler.run(ScoutMap.filter_records, ["type", ["Colony","Pack","Troop","Unit"]])
    script_handler.run(ScoutMap.filter_records, ["Year", ["2014","2015","2016","2017","2018","2019"]])
    script_handler.run(ScoutMap.filter_records, ["imd_decile", [1,2]])
    script_handler.run(ScoutMap.section_history_summary, [["2014","2015","2016","2017","2018","2019"]], "Sections_opened_in_deprivation_since_2014")
