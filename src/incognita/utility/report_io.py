from __future__ import annotations

from typing import TYPE_CHECKING

from incognita.logger import logger
from incognita.utility import config

if TYPE_CHECKING:
    import pandas as pd


def save_report(report: pd.DataFrame, report_name: str) -> None:
    logger.info(f"Writing to {report_name}")
    report.to_csv(config.SETTINGS.folders.output / f"{report_name}.csv", index=False, encoding="utf-8-sig")
