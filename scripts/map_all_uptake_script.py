"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""

from src.data.scout_data import ScoutData
from src.reports.reports import Reports
from src.maps.map import Map

if __name__ == "__main__":
    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("X_name", ["Wales"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    pcon = Reports("pcon", scout_data)
    pcon.filter_boundaries(field="X_name", value_list=["Wales"], boundary="pcon", distance=3000, near=True)
    pcon.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name="pcon_wales")
    pcon.create_uptake_report(report_name="pcon_wales_uptake_report")

    imd = Reports("lsoa", scout_data)
    pcon_list = pcon.data["pcon"]
    imd.filter_boundaries(field="pcon", value_list=pcon_list)

    imd.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name="imd_wales")

    lad = Reports("lad", scout_data)
    lad.filter_boundaries(field="pcon", value_list=pcon_list)
    lad.create_boundary_report(["Section numbers", "6 to 17 numbers"], report_name="las_wales")
    lad.create_uptake_report(report_name="las_wales_uptake_report")

    max_year = 2019

    # create_6_to_17_map
    dimension = {"column": f"%-All-{max_year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake (pcon)"}
    map = Map(scout_data, map_name="all_wales_uptake_map6")
    map.add_areas(dimension, pcon, show=True)

    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    map.add_areas(dimension, imd)

    # dimension = {"column": f"%-All-{max_year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake (la)"}
    # map.add_areas(dimension, lad)

    # Plotting the sections
    map.set_region_of_colour("X_name", ["Wales"])
    map.map_plotter.add_layer(name="Your Sections", markers_clustered=False, show=True)
    # map.map_plotter.add_layer(name="Other Sections", markers_clustered=False, show=False)
    # map.add_meeting_places_to_map(scout_data.data.loc[~(scout_data.data["X_name"] == "Wales")], "lightgray", ["youth membership"], "Other Sections")
    map.add_meeting_places_to_map(scout_data.data.loc[scout_data.data["X_name"] == "Wales"], map.district_colour_mapping(), ["youth membership"], "Your Sections")
    map.save_map()

    scout_data.close()
