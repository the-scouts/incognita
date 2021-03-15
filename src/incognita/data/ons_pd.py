from pathlib import Path
from typing import Optional

import pydantic


# class DeprivationMaximums(pydantic.BaseModel):
#     england: int
#     wales: int
#     scotland: int
#     northern_ireland: int


class BoundaryCodes(pydantic.BaseModel):
    path: Optional[Path]
    key: Optional[str]
    key_type: Optional[str]
    name: Optional[str]


class BoundaryShapeFile(pydantic.BaseModel):
    path: Path
    key: str
    name: str


class BoundaryAgeProfile(pydantic.BaseModel):
    path: Path
    key: str
    pivot_key: str


class Boundary(pydantic.BaseModel):
    name: str
    codes: BoundaryCodes
    shapefile: Optional[BoundaryShapeFile] = None
    age_profile: Optional[BoundaryAgeProfile] = None


class ONSPostcodeDirectory(pydantic.BaseModel):
    """Used for holding and accessing ONS Postcode Directory data

    Attributes:
        PUBLICATION_DATE: Date of publication of the ONS Postcode Directory data
        IMD_MAX: Highest ranked Lower Level Super Output Area (or equivalent) in each country
        COUNTRY_CODES: ONS Postcode Directory codes for each country

    """

    PUBLICATION_DATE: str
    # IMD_MAX: DeprivationMaximums
    IMD_MAX: dict[str, int]
    COUNTRY_CODES: dict[str, str]
    BOUNDARIES: dict[str, Boundary]
