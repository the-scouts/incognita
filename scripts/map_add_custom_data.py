from incognita.data.scout_data import ScoutData
from incognita.maps.map import Map
from incognita.reports.reports import Reports
from incognita.utility import config

if __name__ == "__main__":
    county_name = "Central Yorkshire"
    la_code = "E08000035"  # Leeds LA code
    year = 2020

    scout_data = ScoutData(load_ons_pd_data=True)
    scout_data.filter_records("Year", [year])
    scout_data.filter_records("oslaua", [la_code])
    scout_data.filter_records("postcode_is_valid", [1], exclusion_analysis=True)

    # Generate boundary report
    reports = Reports("lsoa", scout_data)
    reports.filter_boundaries("oslaua", [la_code])  # Leeds LA code
    reports.create_boundary_report(["Section numbers"], report_name="leeds_sections")

    # Create map object
    mapper = Map(scout_data, map_name="Leeds")

    # Plot
    dimension = {"column": f"Beavers-{year}", "tooltip": f"Beavers {year}", "legend": "# Beavers"}
    mapper.add_areas(dimension, reports, show=True)
    mapper.add_custom_data(
        config.SETTINGS.folders.national_statistical / "leeds_primary_schools.csv",
        "Primary Schools",
        location_cols="Postcode",
        marker_data=["EstablishmentName"],
    )
    mapper.add_sections_to_map(scout_data, mapper.district_colour_mapping(), ["youth membership"], single_section="Beavers")

    # Save the map and display
    mapper.save_map()
    mapper.show_map()
    scout_data.close()
