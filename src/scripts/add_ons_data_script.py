"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory published in May 2018.

This script has no command line options.
"""

from src.script_handler import ScriptHandler
from src.scout_map import ScoutMap
from src.ONS_data_May_18 import ONSDataMay18
import json

if __name__ == "__main__":

    script_handler = ScriptHandler(csv_has_ons_data=False)
    with open("settings.json", "r") as read_file:
        settings = json.load(read_file)["settings"]
    ons_data = ONSDataMay18(settings["ONS PD location"])
    script_handler.run(ScoutMap.create_ONS_lookup, [ons_data])
