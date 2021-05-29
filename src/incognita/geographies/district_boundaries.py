from collections.abc import Sequence

import geopandas as gpd
import pandas as pd
import pygeos

from incognita.data import scout_census
from incognita.utility import constants


def create_voronoi(points: Sequence[pygeos.Geometry]) -> Sequence[pygeos.Geometry]:
    mp = pygeos.multipoints(points)
    polys = pygeos.get_parts(pygeos.voronoi_polygons(mp))
    convex_hull = pygeos.buffer(pygeos.convex_hull(mp), 2)
    return pygeos.intersection(convex_hull, polys)


def spatial_join(points: Sequence[pygeos.Geometry], voronoi_polygons: Sequence[pygeos.Geometry]) -> Sequence[int]:
    query_result = pygeos.STRtree(voronoi_polygons).query_bulk(points, predicate="intersects")
    assert (query_result[0] == range(query_result[0].size)).all()  # check that the first array is a standard range
    return query_result[1]


def merge_to_districts(district_ids, points: Sequence[pygeos.Geometry]) -> pd.Series:
    voronoi_polygons = create_voronoi(points)
    index_map = spatial_join(points, voronoi_polygons)
    df = pd.DataFrame({"D_ID": district_ids, "polys": voronoi_polygons[index_map]})
    merged_polys = df.groupby("D_ID")["polys"].apply(pygeos.coverage_union_all)
    merged_polys.index.name = None
    return merged_polys


def create_district_boundaries(census_data: pd.DataFrame, *, clip_to: pygeos.Geometry = None) -> gpd.GeoSeries:
    """Estimates district boundaries from group locations.

    Aims to estimate district boundaries from Group points, using the Voronoi
    diagram method.

    Args:
        census_data: Dataframe with census data
        clip_to: Optional area to clip results to. Must be in WGS84 projection.

    Returns: GeoDataFrame of district IDs -> district polygons

    Todo:
        Spatial transforms add 20x overhead, but buffering relies on them to work. Fix.

    """
    # Finds and de-duplicates all the records with valid postcodes in the Scout Census
    all_locations = census_data.loc[census_data[scout_census.column_labels.VALID_POSTCODE], ["D_ID", "lat", "long"]]
    all_locations = all_locations.drop_duplicates(subset=["lat", "long"]).dropna(subset=["lat", "long"]).reset_index(drop=True)

    # Create points from lat / long co-ordinates above
    points = gpd.points_from_xy(all_locations["long"], all_locations["lat"], crs=constants.WGS_84)
    # convert the co-ordinate reference system into OS36 (British National
    # Grid). This is uses (x-y) coordinates in metres, rather than (long, lat)
    # coordinates, meaning that we can operate in metres from now on.
    points = points.to_crs(epsg=constants.BNG).data

    districts = gpd.GeoSeries(merge_to_districts(all_locations["D_ID"], points), crs=constants.BNG).to_crs(epsg=constants.WGS_84)
    if clip_to is not None:
        districts.geometry.array.data = pygeos.intersection(districts.geometry.array.data, clip_to)
    return districts.reset_index()  # return district IDs (the index) as a field/column
