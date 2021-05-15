from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from incognita.data.ons_pd import ONSPostcodeDirectory


def calc_imd_decile(imd_ranks: pd.Series, country_codes: pd.Series, ons_object: ONSPostcodeDirectory) -> pd.Series:
    """Calculate IMD decile from ranks, country codes and ONS metadata.

    Args:
        imd_ranks:
        country_codes:
        ons_object:

    """

    # Map country codes to maximum IMD rank in each country, and broadcast to the array
    code_imd_map = {code: ons_object.IMD_MAX[country] for code, country in ons_object.COUNTRY_CODES.items()}
    imd_max = country_codes.map(code_imd_map).astype("Int32")

    # One of the two series must be of a 'normal' int dtype - excluding the new ones that can deal with NAs
    imd_max = _try_downcast(imd_max)
    imd_ranks = _try_downcast(imd_ranks)

    if not imd_max.empty:
        # upside down floor division to get ceiling
        # https://stackoverflow.com/a/17511341
        return -((-imd_ranks * 10).floordiv(imd_max))
    else:
        raise Exception("No IMD values found to calculate deciles from")


def _try_downcast(series: pd.Series) -> pd.Series:
    try:
        int_series = series.astype("int32")
        if series.eq(int_series).all():
            return int_series
        else:
            return series
    except ValueError:
        return series
