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
    predicted_result = pd.Series(data=[10, 1], index=['row_1', 'row_2'], name="imd_decile")
    assert(data["imd_decile"].equals(predicted_result))


def test_filter_records_inclusion():
    scout_data_stub = ScoutDataStub()
    ScoutData.filter_records(self=scout_data_stub,
                             field='ctry',
                             value_list=["E92000001"],
                             mask=True,
                             exclusion_analysis=False)
    predicted_data = {'row_2': [2, "W92000004", 1]}
    predicted_answer = pd.DataFrame.from_dict(predicted_data, orient='index', columns=['id', 'ctry', 'imd'])
    answer = scout_data_stub.data.equals(predicted_answer)
    if not answer:
        print(scout_data_stub.data)
        print(predicted_answer)
    assert (scout_data_stub.data.equals(predicted_answer))


def test_filter_records_exclusion():
    scout_data_stub = ScoutDataStub()
    ScoutData.filter_records(self=scout_data_stub,
                             field='ctry',
                             value_list=["E92000001"],
                             mask=False,
                             exclusion_analysis=False)
    predicted_data = {'row_1': [1, "E92000001", 32844]}
    predicted_answer = pd.DataFrame.from_dict(predicted_data, orient='index', columns=['id', 'ctry', 'imd'])
    answer = scout_data_stub.data.equals(predicted_answer)
    if not answer:
        print(scout_data_stub.data)
        print(predicted_answer)
    assert (scout_data_stub.data.equals(predicted_answer))
