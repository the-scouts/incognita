import src.utility as utility
import pandas as pd


class ONSPDStub:
    def __init__(self):
        self.IMD_MAX = {"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890}
        self.COUNTRY_CODES = {"E92000001": "England", "W92000004": "Wales", "S92000003": "Scotland", "N92000002": "Northern Ireland"}


def test_calc_imd_decile():
    data = {"row_1": [1, "E92000001", 32844], "row_2": [2, "W92000004", 1]}
    frame = pd.DataFrame.from_dict(data, orient="index", columns=["id", "ctry", "imd"])

    imd_decile_data: pd.Series = utility.calc_imd_decile(frame["imd"], frame["ctry"], ONSPDStub())
    predicted_result = pd.Series(data=[10, 1], index=["row_1", "row_2"], name="imd_decile")

    assert isinstance(imd_decile_data, pd.Series)
    assert imd_decile_data.equals(predicted_result)
