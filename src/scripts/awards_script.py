"""Awards Mapping

This script produces a boundary report by local authority district, and plots
the percentage of Chief Scout Bronze Awards awarded between 31st January 2018
and 31st January 2019 of the eligible Beavers. and percentage of QSAs.

This script has no command line options.
"""


from script_handler import ScriptHandler
from scout_map import ScoutMap

if __name__ == "__main__":

    script_handler = ScriptHandler()
    script_handler.run(ScoutMap.set_boundary, ["lad"])
    script_handler.run(ScoutMap.filter_records, ["Year", ["2019"]])
    #script_handler.run(ScoutMap.filter_records, ["postcode_is_valid", ["1"]])
    #script_handler.run(ScoutMap.ons_to_district_mapping, ["oslaua"])

    script_handler.run(ScoutMap.create_boundary_report, ["awards"], "laua_awards_report")
    script_handler.run(ScoutMap.create_map, ["%-QSA", "QSA %", "UK_QSA_awards", "QSA %"])

    #script_handler.run(ScoutMap.add_single_section_to_map, ["Beavers", script_handler.map.district_mapping(), ["youth membership", "awards"]])
    script_handler.run(ScoutMap.save_map)
    script_handler.run(ScoutMap.show_map)

    script_handler.close()
