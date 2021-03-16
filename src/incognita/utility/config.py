from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import pydantic
import pydantic.validators
import toml

from incognita.utility import root
from incognita.data.ons_pd import Boundary
from incognita.data.ons_pd import BoundaryShapeFile
from incognita.data.ons_pd import BoundaryAgeProfile
from incognita.data.ons_pd import BoundaryCodes

if TYPE_CHECKING:
    import pydantic.typing


def concretise_path(value: Path) -> Path:
    """Make relative config paths concrete by prepending project root."""
    try:
        return (root.PROJECT_ROOT / value).resolve()
    except TypeError:
        raise pydantic.errors.PathError()


class ProjectFilePath(pydantic.FilePath):
    @classmethod
    def __get_validators__(cls) -> pydantic.typing.CallableGenerator:
        if os.getenv("CI"):  # CI doesn't have files in incognita-config.toml
            yield pydantic.validators.path_validator
        else:
            yield concretise_path
            yield from super().__get_validators__()


class ProjectDirectoryPath(pydantic.DirectoryPath):
    @classmethod
    def __get_validators__(cls) -> pydantic.typing.CallableGenerator:
        if os.getenv("CI"):  # CI doesn't have files in incognita-config.toml
            yield pydantic.validators.path_validator
        else:
            yield concretise_path
            yield from super().__get_validators__()


class CensusPaths(pydantic.BaseModel):
    original: ProjectFilePath
    merged: ProjectFilePath


class ONSPostcodeDirectoryPaths(pydantic.BaseModel):
    full: ProjectFilePath
    reduced: ProjectFilePath
    minified: ProjectFilePath
    reduced_nystest: ProjectFilePath


class FolderPaths(pydantic.BaseModel):
    ons_pd_names_codes: ProjectDirectoryPath  # Folder within the ONS Postcode Directory archive holding names and codes files
    national_statistical: ProjectDirectoryPath  # Folder for national statistical data (age profiles etc)
    boundaries: ProjectDirectoryPath  # Folder with all shapefiles
    output: ProjectDirectoryPath  # Folder for generated files


class CustomBoundaryCodes(BoundaryCodes):
    path: Optional[Path] = None
    key: Optional[str] = None
    key_type: Optional[str] = None  # TODO literal dtypes
    name: Optional[str] = None


class CustomBoundaryShapeFile(BoundaryShapeFile):
    path: Optional[Path] = None
    key: Optional[str] = None
    name: Optional[str] = None


class CustomBoundaryAgeProfile(BoundaryAgeProfile):
    path: Optional[Path] = None
    key: Optional[str] = None
    pivot_key: Optional[str] = None


class CustomBoundary(Boundary):
    name: str
    codes: CustomBoundaryCodes = CustomBoundaryCodes()
    shapefile: CustomBoundaryShapeFile = CustomBoundaryShapeFile()
    age_profile: CustomBoundaryAgeProfile = CustomBoundaryAgeProfile()


class ConfigModel(pydantic.BaseModel):
    census_extract: CensusPaths
    ons_pd: ONSPostcodeDirectoryPaths
    folders: FolderPaths
    custom_boundaries: dict[str, CustomBoundary]


_SETTINGS_TOML = toml.loads((root.PROJECT_ROOT / "incognita-config.toml").read_text())
SETTINGS = ConfigModel(**_SETTINGS_TOML)
