from pathlib import Path

from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.ground import GROUND_TEMPERATURE_C, add_ground_temperature

try:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_TEMPLATE = str(
    Path(__file__).resolve().parents[2]
    / "openubem" / "idf" / "templates" / "commercial_base.idf"
)


def _fresh_idf() -> IDF:
    return IDF(_TEMPLATE)


class TestAddGroundTemperature:
    def test_exactly_one_object_after_one_call(self):
        idf = _fresh_idf()
        add_ground_temperature(idf)
        assert len(idf.idfobjects["SITE:GROUNDTEMPERATURE:BUILDINGSURFACE"]) == 1

    def test_exactly_one_object_after_two_calls(self):
        idf = _fresh_idf()
        add_ground_temperature(idf)
        add_ground_temperature(idf)
        assert len(idf.idfobjects["SITE:GROUNDTEMPERATURE:BUILDINGSURFACE"]) == 1

    def test_all_twelve_fields_equal_18(self):
        idf = _fresh_idf()
        add_ground_temperature(idf)
        obj = idf.idfobjects["SITE:GROUNDTEMPERATURE:BUILDINGSURFACE"][0]
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        for month in months:
            assert getattr(obj, f"{month}_Ground_Temperature") == GROUND_TEMPERATURE_C

    def test_existing_object_left_unchanged(self):
        idf = _fresh_idf()
        idf.newidfobject(
            "SITE:GROUNDTEMPERATURE:BUILDINGSURFACE",
            January_Ground_Temperature=5.0,
        )
        add_ground_temperature(idf)
        objs = idf.idfobjects["SITE:GROUNDTEMPERATURE:BUILDINGSURFACE"]
        assert len(objs) == 1
        assert objs[0].January_Ground_Temperature == 5.0
