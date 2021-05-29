"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""

import time

from incognita.data.scout_data import ScoutData
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import report_io
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()

    # # % 6-17 LAs uptake from Jan-2020 Scout Census with May 2019 ONS
    #
    # from incognita.utility import utility
    # import pandas as pd
    # import geopandas as gpd
    # from time import time
    # start = time()
    # # a = geofeather.from_geofeather(utility.SETTINGS.ons_pd.minified) # 60-80s
    # ons_full = pd.read_feather(utility.SETTINGS.ons_pd.minified)
    # geo_column = gpd.points_from_xy(ons_full.long, ons_full.lat)
    # reduced_data_with_geo = gpd.GeoDataFrame(ons_full, geometry=geo_column, crs=utility.WGS_84)
    # print(f"Loading ONS took: {time() - start:.3f}s")
    # start = time()
    # counties = gpd.GeoDataFrame.from_file(utility.SETTINGS.folders.boundaries / "Counties_and_Unitary_Authorities__December_2019__Boundaries_UK_BUC/Counties_and_Unitary_Authorities__December_2019__Boundaries_UK_BUC.shp")
    # counties = counties[['ctyua19cd', 'geometry']]
    # print(f"Loading shapefile took: {time() - start:.3f}s")
    # start = time()
    # a = gpd.sjoin(reduced_data_with_geo.to_crs(epsg=27700), counties, how="left",  op='within') # 793s - speed up!!
    # print(f"Spatial join: {time() - start:.3f}s")
    # c = a[['oscty', 'oslaua', 'osward', 'ctry', 'rgn', 'pcon', 'lsoa11', 'msoa11', 'imd', 'imd_decile', 'ctyua19cd']].drop_duplicates()
    # c.to_feather(utility.SETTINGS.ons_pd.reduced.with_suffix(".feather"))

    # TODO show growth by yp numbers ✔
    # TODO produce separate YP and Adults maps ✔
    # TODO show growth by sections ✔
    # TODO show uptake across UK
    # TODO include G/J/IoM

    country_names = {
        "Wales",
    }
    location_name = "Wales"
    census_ids = {19, 20}

    # setup data
    scout_data = ScoutData()
    scout_data.filter_records("Census_ID", census_ids)
    scout_data.filter_records("X_name", country_names)
    # scout_data.filter_records("C_name", {"Bailiwick of Guernsey", "Isle of Man", "Jersey"}, exclude_matching=True)
    scout_data.filter_records("type", {"Colony", "Pack", "Troop", "Unit"})
    scout_data.filter_records("postcode_is_valid", {True}, exclusion_analysis=True)

    offset = 5
    opts = [
        "Section numbers",
        "6 to 17 numbers",
        "Adult numbers",
        "Number of Sections",
    ]

    # lad_reports = Reports("Local Authority", scout_data)
    # lad_reports.filter_boundaries("X_name", country_names, "oslaua")
    # lad_boundary_report = lad_reports.create_boundary_report(opts, historical=True, report_name=f"{location_name} - LADs")
    # for i in range(offset):
    #     j = i * 2
    #     lad_reports.data[f"{lad_reports.data.iloc[:, j + 3].name.split('-')[0]}_change"] = (lad_reports.data.iloc[:, j + 3 + offset * 2] / lad_reports.data.iloc[:, j + 3]) * 100 - 100
    # lad_reports.data[f"Adults_change"] = (lad_reports.data.iloc[:, 22] / lad_reports.data.iloc[:, 12]) * 100 - 100
    # lad_reports.data[f"Sections_change"] = (lad_reports.data[['Colonys-2020', 'Packs-2020', 'Troops-2020', 'Units-2020']].sum(axis=1) / lad_reports.data[['Colonys-2019', 'Packs-2019', 'Troops-2019', 'Units-2019']].sum(axis=1) - 1) * 100

    cty_reports = Reports("County", scout_data)
    cty_reports.ons_pd.fields.add(cty_reports.geography.metadata.key)
    cty_reports.filter_boundaries("ctry", {"W92000004"})
    cty_reports.geography.boundary_codes = cty_reports.geography.boundary_codes[cty_reports.geography.boundary_codes["codes"].str.startswith("W")]
    cty_reports.add_shapefile_data()
    cty_boundary_report = cty_reports.create_boundary_report(opts, historical=True, report_name=f"{location_name} - Counties")
    cty_reports.create_uptake_report(cty_boundary_report, report_name=f"{location_name} - Counties (uptake)")
    data = cty_boundary_report
    for i in range(offset):
        j = i * 2
        data[f"{data.iloc[:, j + 3].name.split('-')[0]}_change"] = (
            data.iloc[:, j + 3 + offset * 2] / data.iloc[:, j + 3]
        ) * 100 - 100
        print(f"{data.iloc[:, j + 3 + offset * 2].name} / {data.iloc[:, j + 3].name}")
    data[f"Adults_change"] = (data.iloc[:, 22] / data.iloc[:, 12]) * 100 - 100
    data[f"Sections_change"] = (
        data[["Colonys-2020", "Packs-2020", "Troops-2020", "Units-2020"]].sum(axis=1)
        / data[["Colonys-2019", "Packs-2019", "Troops-2019", "Units-2019"]].sum(axis=1)
        - 1
    ) * 100
    report_io.save_report(data, f"{location_name} - Counties with change")

    # Create map object
    mapper = Map(map_name=f"{location_name} uptake map")

    # mapper.add_areas("All_change", "% Change 6-18", "% Change 6-18 (LADs)", lad_boundary_report, lad_reports.geography.metadata)

    # TODO BUG only last add areas has correct colour mapping for same reports instance

    mapper.add_areas("All_change", "% Change 6-18", "% Change 6-18 (Counties)", cty_boundary_report, cty_reports.geography.metadata, show=True)

    mapper.add_areas("Beavers_change", "% Change Beavers", "% Change Beavers (Counties)", cty_boundary_report, cty_reports.geography.metadata)

    mapper.add_areas("Cubs_change", "% Change Cubs", "% Change Cubs (Counties)", cty_boundary_report, cty_reports.geography.metadata)

    mapper.add_areas("Scouts_change", "% Change Scouts", "% Change Scouts (Counties)", cty_boundary_report, cty_reports.geography.metadata)

    mapper.add_areas("Explorers_change", "% Change Explorers", "% Change Explorers (Counties)", cty_boundary_report, cty_reports.geography.metadata)

    mapper.add_areas("Adults_change", "% Change Adults", "% Change Adults (Counties)", cty_boundary_report, cty_reports.geography.metadata)

    mapper.add_areas("Sections_change", "% Change # Sections", "% Change # Sections (Counties)", cty_boundary_report, cty_reports.geography.metadata)

    # mapper.add_areas("%-All-2020", "% Uptake 6-18", "% Uptake 6-18 (Counties)", cty_boundary_report, cty_reports.geography.metadata, significance_threshold=0)
    #
    # mapper.add_areas("%-Beavers-2020", "% Uptake Beavers", "% Uptake Beavers (Counties)", cty_boundary_report, cty_reports.geography.metadata, significance_threshold=0)
    #
    # mapper.add_areas("%-Cubs-2020", "% Uptake Cubs", "% Uptake Cubs (Counties)", cty_boundary_report, cty_reports.geography.metadata, significance_threshold=0)
    #
    # mapper.add_areas("%-Scouts-2020", "% Uptake Scouts", "% Uptake Scouts (Counties)", cty_boundary_report, cty_reports.geography.metadata, significance_threshold=0)
    #
    # mapper.add_areas("%-Explorers-2020", "% Uptake Explorers", "% Uptake Explorers (Counties)", cty_boundary_report, cty_reports.geography.metadata, significance_threshold=0)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    # create_section_maps
    # for section_label in Reports.SECTION_AGES.keys():
    #     section_map = Map(map_name=f"pcon_uptake_report_{section_label}")
    #     section_map.add_areas(f"%-{section_label}-{year}", section_label, f"{year} {section_label} uptake (%)", pcon_reports, colour_bounds=[0, 3, 4, 6, 8, 11])
    #     section_map.add_sections_to_map(scout_data, section_map.district_colour_mapping(scout_data), {"youth membership"}, single_section=section_label)
    #     section_map.save_map()

    # get script execution time etc.
    timing.close(start_time)
