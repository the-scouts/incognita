from src.data.scout_data import ScoutData
from src.base import Base
import src.utility as utility
import pandas as pd


class ScoutDataStub(Base):
    def __init__(self):
        super().__init__(settings=True, log_path=str(utility.LOGS_ROOT.joinpath("geo_mapping.log")))
        data = {"row_1": [1, "E92000001", 32844], "row_2": [2, "W92000004", 1]}
        self.data = pd.DataFrame.from_dict(data, orient="index", columns=["id", "ctry", "imd"])


def test_filter_records_inclusion():
    scout_data_stub = ScoutDataStub()
    ScoutData.filter_records(self=scout_data_stub, field="ctry", value_list=["E92000001"], mask=True, exclusion_analysis=False)
    predicted_data = {"row_2": [2, "W92000004", 1]}
    predicted_result = pd.DataFrame.from_dict(predicted_data, orient="index", columns=["id", "ctry", "imd"])
    answer = scout_data_stub.data.equals(predicted_result)
    if not answer:
        print(scout_data_stub.data)
        print(predicted_result)
    assert scout_data_stub.data.equals(predicted_result)


def test_filter_records_exclusion():
    scout_data_stub = ScoutDataStub()
    ScoutData.filter_records(self=scout_data_stub, field="ctry", value_list=["E92000001"], mask=False, exclusion_analysis=False)
    predicted_data = {"row_1": [1, "E92000001", 32844]}
    predicted_result = pd.DataFrame.from_dict(predicted_data, orient="index", columns=["id", "ctry", "imd"])
    answer = scout_data_stub.data.equals(predicted_result)
    if not answer:
        print(scout_data_stub.data)
        print(predicted_result)
    assert scout_data_stub.data.equals(predicted_result)
