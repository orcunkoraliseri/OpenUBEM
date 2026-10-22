import importlib.util
from pathlib import Path

from openubem.idf import outputs

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("add_hourly_meters", ROOT / "scripts" / "paper" / "add_hourly_meters.py")
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

US_IDF = ROOT / "tests" / "fixtures" / "viz" / "Restaurant_QuickServiceRestaurant_90.1-2013.idf"


def test_name_tuple_equals_the_package_tuple():
    assert m.HOURLY_METERS == outputs.HOURLY_METERS


def test_real_us_idf_input_is_a_byte_prefix_of_the_output(tmp_path):
    out = tmp_path / "out.idf"
    assert m.main(["x", str(US_IDF), str(out)]) == 0
    raw = US_IDF.read_bytes()
    new = out.read_bytes()
    assert new.startswith(raw)
    tail = new[len(raw):].decode()
    assert tail.count("Output:Meter,") >= 1
    assert all(line.endswith(",Hourly;") for line in tail.strip().splitlines())


def test_second_run_adds_nothing(tmp_path):
    first = tmp_path / "a.idf"
    second = tmp_path / "b.idf"
    m.main(["x", str(US_IDF), str(first)])
    m.main(["x", str(first), str(second)])
    assert second.read_bytes() == first.read_bytes()
    text = second.read_text(encoding="utf-8", errors="surrogateescape")
    for name in m.HOURLY_METERS:
        assert text.lower().count(f"output:meter,{name.lower()},hourly;") == 1


def test_meter_already_hourly_is_not_repeated_and_other_frequencies_do_not_count():
    text = (
        "Output:Meter,\n  Heating:NaturalGas,  !- Key Name\n  Hourly;  !- freq\n"
        "Output:Meter,Cooling:Electricity,RunPeriod;\n"
        "Output:Meter:MeterFileOnly,Electricity:Facility,Hourly;"
    )
    out = m.append_hourly_meters(text)
    assert out.startswith(text)
    assert out.count("Output:Meter,Heating:NaturalGas,Hourly;") == 0
    assert out.count("Output:Meter,Cooling:Electricity,Hourly;") == 1
    assert out.count("Output:Meter,Electricity:Facility,Hourly;") == 1


def test_crlf_text_is_kept():
    text = "Version,23.1;\r\n"
    out = m.append_hourly_meters(text)
    assert out.startswith(text)
