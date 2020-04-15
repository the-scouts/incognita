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
    scout_data.add_imd_decile()
    #scout_data.filter_records("X_name", ["England", "Scotland", "Wales", "Northern Ireland"])
    scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("Year", [2019])
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    pcon = Reports("pcon", scout_data)
    pcon.filter_boundaries(field="X_name",
                           value_list=["Wales"],
                           boundary="pcon",
                           distance=3000,
                           near=True)
    pcon.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name="pcon_wales")
    pcon.create_uptake_report(report_name="pcon_wales_uptake_report")

    imd = Reports("lsoa", scout_data)
    pcon_list = pcon.data["pcon"]
    imd.filter_boundaries(field="pcon", value_list=pcon_list)
    #lsoa_list = boundary.ons_from_scout_area("lsoa11", "pcon", pcon_list)
    #imd.filter_boundaries("lsoa11", lsoa_list)

    #imd.filter_boundaries_near_scout_area("imd", "C_ID", [10000112], exec_tm=True)
    #imd.filter_records_by_boundary(exec_tm=True)
    imd.create_boundary_report(["Section numbers", "6 to 17 numbers"], historical=False, report_name="imd_wales")

    #district = Boundary("District", scout_data)
    #districts = scout_data.data.loc[scout_data.data["pcon"].isin(pcon_list)]["D_ID"].unique()
    #district.boundary_regions_data = district.boundary_regions_data.loc[district.boundary_regions_data["D_ID"].isin(districts)]
    #district.create_boundary_report(["Section numbers", "6 to 17 numbers"],
    #                                report_name="districts_devon")

    lad = Reports("lad", scout_data)
    lad.filter_boundaries(field="pcon", value_list=pcon_list)
    lad.create_boundary_report(["Section numbers", "6 to 17 numbers"],
                               report_name="las_wales")
    lad.create_uptake_report(report_name="las_wales_uptake_report")

    max_year = 2019

    # create_6_to_17_map
    dimension = {"column": f"%-All-{max_year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake (pcon)"}
    map = Map(scout_data, map_name="all_wales_uptake_map")
    map.add_areas(dimension, pcon, show=True)

    dimension = {"column": "imd_decile", "tooltip": "IMD", "legend": "IMD Decile"}
    map.add_areas(dimension, imd)

    dimension = {"column": f"All-{max_year}", "tooltip": "Ages 6-17", "legend": "Districts"}
    #print(district.boundary_dict)
    #map.add_areas(dimension, district)

    dimension = {"column": f"%-All-{max_year}", "tooltip": "% 6-17 Uptake", "legend": "% 6-17 Uptake (la)"}
    #map.add_areas(dimension, lad)

    # Plotting the sections
    map.set_region_of_colour("X_name", ["Wales"])
    map.map_plotter.add_layer(name='Your Sections', markers_clustered=False, show=True)
    #map.map_plotter.add_layer(name='Other Sections', markers_clustered=False, show=False)
    #map.add_meeting_places_to_map(scout_data.data.loc[~(scout_data.data["X_name"] == "Wales")], 'lightgray', ["youth membership"], 'Other Sections')
    map.add_meeting_places_to_map(scout_data.data.loc[scout_data.data["X_name"] == "Wales"], map.district_colour_mapping(), ["youth membership"], 'Your Sections')
    map.save_map()

    # create_section_maps
    #for section_label in Boundary.SECTION_AGES.keys():
        #dimension = {"column": f"%-{section_label}-{max_year}", "tooltip": section_label, "legend": f"{max_year} {section_label} uptake (%)"}
        #section_map = Map(scout_data, boundary, dimension, map_name=f"pcon_uptake_report_{section_label}", static_scale=static_scale)
        #section_map.add_sections_to_map(section_map.district_colour_mapping(), ["youth membership"], single_section=section_label)
        #section_map.save_map()

    scout_data.close()
