from src.data.scout_data import ScoutData
from src.base import Base
import src.utility as utility
import pandas as pd

class ONSPdStub():
    def __init__(self):
        self.IMD_MAX = {"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890}
        self.COUNTRY_CODES = {"E92000001": "England", "W92000004": "Wales", "S92000003": "Scotland", "N92000002": "Northern Ireland", }


class ScoutDataStub(Base):
    def __init__(self):
        super().__init__(settings=True, log_path=str(utility.LOGS_ROOT.joinpath('geo_mapping.log')))
        self.ons_pd = ONSPdStub()
        data = {'row_1': [1, "E92000001", 32844],
                'row_2': [2, "W92000004", 1]}
        self.data = pd.DataFrame.from_dict(data, orient='index', columns=['id', 'ctry', 'imd'])


def test_add_imd_decile():
    data = ScoutData.add_imd_decile(ScoutDataStub())
    predicted_answer = pd.Series(data=[10, 1], index=['row_1', 'row_2'], name="imd_decile")
    assert(data["imd_decile"].equals(predicted_answer))
