from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING

import pydantic
import pydantic.validators

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
        yield concretise_path
        yield from super().__get_validators__()


class ProjectDirectoryPath(pydantic.DirectoryPath):
    @classmethod
    def __get_validators__(cls) -> pydantic.typing.CallableGenerator:
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
    ons_pd_names_codes: ProjectDirectoryPath
    national_statistical: ProjectDirectoryPath
    boundaries: ProjectDirectoryPath
    output: ProjectDirectoryPath


class CustomBoundaryCodes(pydantic.BaseModel):
    path: Optional[Path] = None
    key: Optional[str] = None
    key_type: Optional[str] = None  # TODO literal dtypes
    name: Optional[str] = None


class CustomBoundaryShapeFile(pydantic.BaseModel):
    path: Optional[Path] = None
    key: Optional[str] = None
    name: Optional[str] = None


class CustomBoundaryAgeProfile(pydantic.BaseModel):
    path: Optional[Path] = None
    key: Optional[str] = None
    pivot_key: Optional[str] = None


class CustomBoundary(pydantic.BaseModel):
    name: str
    codes: CustomBoundaryCodes = CustomBoundaryCodes()
    shapefile: CustomBoundaryShapeFile = CustomBoundaryShapeFile()
    age_profile: CustomBoundaryAgeProfile = CustomBoundaryAgeProfile()


class Config(pydantic.BaseModel):
    census_extract: CensusPaths
    ons_pd: ONSPostcodeDirectoryPaths
    folders: FolderPaths
    custom_boundaries: dict[str, CustomBoundary]
