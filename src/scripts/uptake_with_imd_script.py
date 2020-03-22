"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""

from src.scout_data import ScoutData
from src.boundary import Boundary
from src.map import Map

if __name__ == "__main__":
    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    pcon = Boundary("pcon", scout_data)
    pcon.filter_boundaries_near_scout_area("pcon" , "C_name", ["Hampshire"], exec_tm=True)
    pcon.filter_records_by_boundary(exec_tm=True)
    pcon.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name="pcon_central_yorkshire", exec_tm=True)
    pcon.create_uptake_report(report_name="pcon_uptake_report", exec_tm=True)

    imd = Boundary("lsoa", scout_data)
    pcon_list = pcon.boundary_regions_data[pcon.boundary_dict["codes"]["key"]]
    imd.filter_boundaries("pcon", pcon_list)
    #lsoa_list = boundary.ons_from_scout_area("lsoa11", "pcon", pcon_list)
    #imd.filter_boundaries("lsoa11", lsoa_list)

    #imd.filter_boundaries_near_scout_area("imd", "C_ID", [10000112], exec_tm=True)
    #imd.filter_records_by_boundary(exec_tm=True)
    imd.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name="imd_central_yorkshire", exec_tm=True)

    max_year = scout_data.data["Year"].max()

    # create_6_to_17_map
    dimension = {"column": f"%-All-{max_year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake"}
    map = Map(scout_data, map_name="pcon_imd_uptake_map")
    map.add_areas(dimension, pcon, show=True)

    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    map.add_areas(dimension, imd)

    # Plotting the sections
    map.set_region_of_colour("C_name", ["Hampshire"])
    map.map_plotter.add_layer(name='Your Sections', markers_clustered=False, show=True)
    map.map_plotter.add_layer(name='Other Sections', markers_clustered=False, show=False)
    map.add_meeting_places_to_map(scout_data.data.loc[~(scout_data.data["C_name"] == "Hampshire")], 'lightgray', ["youth membership"], 'Other Sections')
    map.add_meeting_places_to_map(scout_data.data.loc[scout_data.data["C_name"] == "Hampshire"], map.district_colour_mapping(), ["youth membership"], 'Your Sections')
    map.save_map()

    # create_section_maps
    #for section_label in Boundary.SECTION_AGES.keys():
        #dimension = {"column": f"%-{section_label}-{max_year}", "tooltip": section_label, "legend": f"{max_year} {section_label} uptake (%)"}
        #section_map = Map(scout_data, boundary, dimension, map_name=f"pcon_uptake_report_{section_label}", static_scale=static_scale)
        #section_map.add_sections_to_map(section_map.district_colour_mapping(), ["youth membership"], single_section=section_label)
        #section_map.save_map()

    scout_data.close()
