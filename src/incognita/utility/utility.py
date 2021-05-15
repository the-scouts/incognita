from __future__ import annotations

from functools import wraps
import time
from typing import TYPE_CHECKING

from incognita.data import scout_census
from incognita.logger import logger
from incognita.utility import config

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

sections_model = scout_census.column_labels.sections
section_types = {section_model.type: section_name for section_name, section_model in sections_model}

# EPSG values for the co-ordinate reference systems that we use
WGS_84 = 4326  # World Geodetic System 1984 (Used in GPS)
BNG = 27700  # British National Grid




def save_report(report: pd.DataFrame, report_name: str) -> None:
    logger.info(f"Writing to {report_name}")
    report.to_csv(config.SETTINGS.folders.output / f"{report_name}.csv", index=False, encoding="utf-8-sig")
