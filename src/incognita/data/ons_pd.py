from pathlib import Path
from typing import Optional, Union

import pydantic

PathLike = Union[Path, str]

# class DeprivationMaximums(pydantic.BaseModel):
#     england: int
#     wales: int
#     scotland: int
#     northern_ireland: int


class BoundaryCodes(pydantic.BaseModel):
    path: PathLike
    key: str
    key_type: str  # TODO literal dtypes
    name: str


class BoundaryShapeFile(pydantic.BaseModel):
    path: PathLike
    key: str
    name: Optional[str]


class BoundaryAgeProfile(pydantic.BaseModel):
    path: PathLike
    key: str
    pivot_key: Optional[str] = None


class Boundary(pydantic.BaseModel):
    key: str  # Column name in the ONS postcode directory file
    codes: BoundaryCodes
    shapefile: Optional[BoundaryShapeFile] = None
    age_profile: Optional[BoundaryAgeProfile] = None


class ONSPostcodeDirectory(pydantic.BaseModel):
    """Used for holding and accessing ONS Postcode Directory data."""

    fields: set[str]  # columns to read from the full csv file
    index_column: str  # column to use as the index when merging. Must contain unique values
    data_types: dict[str, str]  # pandas data types for the columns to load

    PUBLICATION_DATE: str  # ONS Postcode Directory Publication date
    # IMD_MAX: DeprivationMaximums  # Highest IMD rank in each of IMD 2015, WIMD 2014, SIMD 2016, NIMDM2017
    IMD_MAX: dict[str, int]  # Highest ranked Lower Level Super Output Area (or equivalent) in each country
    COUNTRY_CODES: dict[str, str]  # ONS Postcode Directory codes for each country
    BOUNDARIES: dict[str, Boundary]  # Dictionary holding dictionaries with information for each type of boundary
