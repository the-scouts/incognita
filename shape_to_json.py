import shapefile
import pandas as pd
import folium
import geopandas
from bng_to_latlon import OSGB36toWGS84
from json import dumps

def plot_constituencies():
    constituencies = geopandas.GeoDataFrame.from_file(r"C:\Users\tyems\Documents\Scouting\Operations\Census 2018\England_parl_2011_gen_clipped\england_parl_2011_gen_clipped.shp")
    gjson = constituencies.to_crs(epsg='4326').to_json()
    map = folium.Map(location=[53.5,-1.49],zoom_start=13)

    map_csv = r'C:\Users\tyems\Documents\Scouting\Operations\Census 2018\barnsley_constituency_data.csv'
    map_data = pd.read_csv(map_csv)

    map.choropleth(geo_data=gjson,
                 data=map_data,
                 columns=['Seat','zScore'],
                 key_on='feature.properties.code',
                 fill_color='YlGn',
                 fill_opacity=0.9,
                 line_opacity=0.2,
                 legend_name='Scouting %')


    folium.LayerControl().add_to(map)
    map.save('map_wgs84.html')




def shape2json(fname, outfile="map_wgs84.json"):
    reader = shapefile.Reader(fname)
    fields = reader.fields[1:]
    field_names = [field[0] for field in fields]

    data = []

    for sr in reader.shapeRecords():
        atr = dict(zip(field_names, sr.record))
        geom = sr.shape.__geo_interface__
        # if geom['type'] == "Polygon":
        #     wgs84_geom = []
        #     for coords in geom['coordinates']:
        #         wgs84_coords = []
        #         for coord in coords:
        #             WGS84 = OSGB36toWGS84(coord[0],coord[1])
        #             wgs84_coords.append((WGS84[1],WGS84[0]))
        #     wgs84_geom.append(wgs84_coords)
        #     wgs84_geom_dict = {'type':'Polygon','coordinates':wgs84_geom}
        # elif geom['type'] == "MultiPolygon":
        #     wgs84_geom = []
        #     for coords in geom['coordinates']:
        #         wgs84_coords = []
        #         for multi_coord in coords:
        #             wgs84_multi = []
        #             for coord in multi_coord:
        #                 WGS84 = OSGB36toWGS84(coord[0],coord[1])
        #                 wgs84_multi.append((WGS84[1],WGS84[0]))
        #         wgs84_coords.append(wgs84_multi)
        #     wgs84_geom.append(wgs84_coords)
        #     wgs84_geom_dict = {'type':'MultiPolygon','coordinates':wgs84_geom}
        # else:
        #     print("Type unrecognized")
        #     exit()
        data.append(dict(type="Feature", geometry=wgs84_geom_dict, properties=atr))

    # keys = ['code', 'name', 'altname']
    #for b in data:
#         for key in keys:
    #             print(b['properties'][key])
    #             b['properties'][key] = b['properties'][key]
                #b['properties'][key] = b['properties'][key].decode('latin-1')

    with open(outfile, "w") as geojson:
         geojson.write(dumps({"type": "FeatureCollection",
                              "features": data}, indent=2) + "\n")

    map_geo = r'map_wgs84.json'
    map_csv = r'C:\Users\tyems\Documents\Scouting\Operations\Census 2018\barnsley_constituency_data.csv'
    map_data = pd.read_csv(map_csv)
    map = folium.Map(location=[53.5,-1.49],zoom_start=13)
    map.choropleth(geo_data=map_geo,
                 data=map_data,
                 columns=['Seat','zScore'],
                 key_on='feature.properties.code',
                 fill_color='YlGn',
                 fill_opacity=0.9,
                 line_opacity=0.2,
                 legend_name='Scouting %')

    folium.LayerControl().add_to(map)
    map.save('map_wgs84.html')


if __name__ == "__main__":
    shape2json(r"C:\Users\tyems\Documents\Scouting\Operations\Census 2018\England_parl_2011_gen_clipped\england_parl_2011_gen_clipped.shp")
