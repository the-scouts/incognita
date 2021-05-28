from collections.abc import Sequence
from typing import Union

import geopandas as gpd
import shapely.geometry
import numpy as np
import pandas as pd
import pygeos

from incognita.data import scout_census
from incognita.logger import logger
from incognita.utility import constants

TYPES_SHAPELY_POLY = Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]


def create_voronoi_pygeos(points: Sequence[pygeos.Geometry]) -> Sequence[pygeos.Geometry]:
    mp = pygeos.multipoints(points)
    polys = pygeos.get_parts(pygeos.voronoi_polygons(mp))
    convex_hull = pygeos.buffer(pygeos.convex_hull(mp), 2)
    return pygeos.intersection(convex_hull, polys)


def create_district_boundaries(census_data: pd.DataFrame) -> None:
    """Creates a GeoJSON file for the District Boundaries of the Scout Census.

    Aims to create a circular boundary around every section of maximal size
    that doesn't overlap or leave gaps between Districts.
    """

    # Finds all the records with valid postcodes in the Scout Census
    all_locations = census_data.loc[census_data[scout_census.column_labels.VALID_POSTCODE], ["D_ID", "lat", "long"]].drop_duplicates(subset=["lat", "long"]).reset_index(drop=True)

    # Create points from lat / long co-ordinates above
    points = gpd.points_from_xy(all_locations["long"], all_locations["lat"])

    # create a GeoDataFrame and converts the co-ordinate reference system into
    # OS36. This is uses (x-y) coordinates in metres, rather than (long, lat)
    # coordinates, meaning that we can operate in metres from now on.
    all_points = gpd.GeoDataFrame(all_locations[["D_ID"]], geometry=points, crs=constants.WGS_84).to_crs(epsg=constants.BNG)

    points = all_points["geometry"].array.data
    groups_voronoi_polygons = create_voronoi_pygeos(points)
    tree = pygeos.STRtree(groups_voronoi_polygons)
    qbi = tree.query_bulk(points, predicate="intersects")
    df = pd.DataFrame({"D_ID": all_points["D_ID"], "polys": groups_voronoi_polygons[qbi[1]]})
    district_polygons = df.groupby("D_ID")["polys"].apply(pygeos.coverage_union_all)

    return district_polygons
