from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import pydantic
import pydantic.validators
import toml

from incognita.data.ons_pd import Boundary
from incognita.data.ons_pd import BoundaryAgeProfile
from incognita.data.ons_pd import BoundaryCodes
from incognita.data.ons_pd import BoundaryShapeFile
from incognita.utility import root

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


class ConfigModel(pydantic.BaseModel):
    census_extract: CensusPaths
    ons_pd: ONSPostcodeDirectoryPaths
    folders: FolderPaths
    ons2019: dict[str, Boundary]
    custom_boundaries: dict[str, Boundary]


def _create_settings(toml_string: dict) -> ConfigModel:
    settings = ConfigModel(**toml_string)

    for boundary in settings.custom_boundaries.values():
        if boundary.shapefile is not None and boundary.shapefile.path is not None:
            boundary.shapefile.path = settings.folders.boundaries / boundary.shapefile.path
    for boundary in settings.ons2019.values():
        boundary.codes.path = settings.folders.ons_pd_names_codes / boundary.codes.path
        if boundary.shapefile is not None and boundary.shapefile.path is not None:
            boundary.shapefile.path = settings.folders.boundaries / boundary.shapefile.path
    return ConfigModel(**settings.__dict__)


_SETTINGS_TOML = toml.loads((root.PROJECT_ROOT / "incognita-config.toml").read_text())
SETTINGS = _create_settings(_SETTINGS_TOML)
