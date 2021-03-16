"""Uptake of Scouting by local authority.

This script produces a boundary report by local authority district, and plots
the percentage of young people.

This script has no command line options.
"""

from incognita.data.scout_data import ScoutData
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import utility

if __name__ == "__main__":
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

    country_names = [
        "Wales",
    ]
    location_name = "Wales"
    years = [2019, 2020]

    # setup data
    scout_data = ScoutData()
    scout_data.filter_records("Year", years)
    scout_data.filter_records("X_name", country_names)
    # scout_data.filter_records("C_name", ["Bailiwick of Guernsey", "Isle of Man", "Jersey"], mask=True)
    scout_data.filter_records("type", ["Colony", "Pack", "Troop", "Unit"])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    offset = 5
    opts = [
        "Section numbers",
        "6 to 17 numbers",
        "Adult numbers",
        "Number of Sections",
    ]

    # lad_reports = Reports("lad", scout_data)
    # lad_reports.filter_boundaries("X_name", set(country_names), "oslaua")
    # lad_reports.create_boundary_report(opts, historical=True, report_name=f"{location_name} - LADs")
    # for i in range(offset):
    #     j = i * 2
    #     lad_reports.data[f"{lad_reports.data.iloc[:, j + 3].name.split('-')[0]}_change"] = (lad_reports.data.iloc[:, j + 3 + offset * 2] / lad_reports.data.iloc[:, j + 3]) * 100 - 100
    # lad_reports.data[f"Adults_change"] = (lad_reports.data.iloc[:, 22] / lad_reports.data.iloc[:, 12]) * 100 - 100
    # lad_reports.data[f"Sections_change"] = (lad_reports.data[['Colonys-2020', 'Packs-2020', 'Troops-2020', 'Units-2020']].sum(axis=1) / lad_reports.data[['Colonys-2019', 'Packs-2019', 'Troops-2019', 'Units-2019']].sum(axis=1) - 1) * 100

    cty_reports = Reports("County", scout_data)
    cty_reports.ons_pd.fields.append(cty_reports.geography.metadata.name)
    cty_reports.filter_boundaries("ctry", {"W92000004"})
    cty_reports.geography.region_ids_mapping = cty_reports.geography.region_ids_mapping[
        cty_reports.geography.region_ids_mapping["ctyua19cd"].str.startswith("W")
    ]
    cty_reports.add_shapefile_data()
    cty_reports.create_boundary_report(opts, historical=True, report_name=f"{location_name} - Counties")
    cty_reports.create_uptake_report(report_name=f"{location_name} - Counties (uptake)")
    for i in range(offset):
        j = i * 2
        cty_reports.data[f"{cty_reports.data.iloc[:, j + 3].name.split('-')[0]}_change"] = (
            cty_reports.data.iloc[:, j + 3 + offset * 2] / cty_reports.data.iloc[:, j + 3]
        ) * 100 - 100
        print(f"{cty_reports.data.iloc[:, j + 3 + offset * 2].name} / {cty_reports.data.iloc[:, j + 3].name}")
    cty_reports.data[f"Adults_change"] = (cty_reports.data.iloc[:, 22] / cty_reports.data.iloc[:, 12]) * 100 - 100
    cty_reports.data[f"Sections_change"] = (
        cty_reports.data[["Colonys-2020", "Packs-2020", "Troops-2020", "Units-2020"]].sum(axis=1)
        / cty_reports.data[["Colonys-2019", "Packs-2019", "Troops-2019", "Units-2019"]].sum(axis=1)
        - 1
    ) * 100
    cty_reports._save_report(cty_reports.data, f"{location_name} - Counties with change")

    # Create map object
    mapper = Map(scout_data, map_name=f"{location_name} uptake map")

    # dimension = {"column": "All_change", "tooltip": "% Change 6-18", "legend": "% Change 6-18 (LADs)"}
    # mapper.add_areas(dimension, lad_reports)

    # TODO BUG only last add areas has correct colour mapping for same reports instance

    dimension = {"column": "All_change", "tooltip": "% Change 6-18", "legend": "% Change 6-18 (Counties)"}
    mapper.add_areas(dimension, cty_reports, show=True)

    dimension = {"column": "Beavers_change", "tooltip": "% Change Beavers", "legend": "% Change Beavers (Counties)"}
    mapper.add_areas(dimension, cty_reports)

    dimension = {"column": "Cubs_change", "tooltip": "% Change Cubs", "legend": "% Change Cubs (Counties)"}
    mapper.add_areas(dimension, cty_reports)

    dimension = {"column": "Scouts_change", "tooltip": "% Change Scouts", "legend": "% Change Scouts (Counties)"}
    mapper.add_areas(dimension, cty_reports)

    dimension = {"column": "Explorers_change", "tooltip": "% Change Explorers", "legend": "% Change Explorers (Counties)"}
    mapper.add_areas(dimension, cty_reports)

    dimension = {"column": "Adults_change", "tooltip": "% Change Adults", "legend": "% Change Adults (Counties)"}
    mapper.add_areas(dimension, cty_reports)

    dimension = {"column": "Sections_change", "tooltip": "% Change # Sections", "legend": "% Change # Sections (Counties)"}
    mapper.add_areas(dimension, cty_reports)

    # dimension = {"column": "%-All-2020", "tooltip": "% Uptake 6-18", "legend": "% Uptake 6-18 (Counties)"}
    # mapper.add_areas(dimension, cty_reports, significance_threshold=0)
    #
    # dimension = {"column": "%-Beavers-2020", "tooltip": "% Uptake Beavers", "legend": "% Uptake Beavers (Counties)"}
    # mapper.add_areas(dimension, cty_reports, significance_threshold=0)
    #
    # dimension = {"column": "%-Cubs-2020", "tooltip": "% Uptake Cubs", "legend": "% Uptake Cubs (Counties)"}
    # mapper.add_areas(dimension, cty_reports, significance_threshold=0)
    #
    # dimension = {"column": "%-Scouts-2020", "tooltip": "% Uptake Scouts", "legend": "% Uptake Scouts (Counties)"}
    # mapper.add_areas(dimension, cty_reports, significance_threshold=0)
    #
    # dimension = {"column": "%-Explorers-2020", "tooltip": "% Uptake Explorers", "legend": "% Uptake Explorers (Counties)"}
    # mapper.add_areas(dimension, cty_reports, significance_threshold=0)

    # Save the map and display
    mapper.save_map()
    mapper.show_map()

    # create_section_maps
    # static_scale = {"index": [0, 8, 20], "min": 0, "max": 20, "boundaries": [0, 3, 4, 6, 8, 11]}
    # for section_label in Reports.SECTION_AGES.keys():
    #     dimension = {"column": f"%-{section_label}-{year}", "tooltip": section_label, "legend": f"{year} {section_label} uptake (%)"}
    #     section_map = Map(scout_data, map_name=f"pcon_uptake_report_{section_label}")
    #     section_map.add_areas(dimension, pcon_reports, scale=static_scale)
    #     section_map.add_sections_to_map(scout_data, section_map.district_colour_mapping(), ["youth membership"], single_section=section_label)
    #     section_map.save_map()

    # get script execution time etc.
    scout_data.close()
