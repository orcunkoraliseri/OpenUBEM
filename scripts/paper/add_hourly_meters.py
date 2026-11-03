import re
import sys
from pathlib import Path

HOURLY_METERS = (
    "Electricity:Facility",
    "NaturalGas:Facility",
    "Cooling:Electricity",
    "Heating:Electricity",
    "Heating:NaturalGas",
    "Fans:Electricity",
    "Pumps:Electricity",
    "WaterSystems:NaturalGas",
    "WaterSystems:Electricity",
    "Refrigeration:Electricity",
    "InteriorEquipment:NaturalGas",
    "Cooking:InteriorEquipment:Electricity",
    "Refrigeration:InteriorEquipment:Electricity",
    "InteriorLights:Electricity",
    "InteriorEquipment:Electricity",
    "Elevators:InteriorEquipment:Electricity",
    "WaterSystems:DistrictHeating",
)

_COMMENT = re.compile(r"!.*")


def hourly_meter_names(text):
    present = set()
    body = "\n".join(_COMMENT.sub("", line) for line in text.splitlines())
    for obj in body.split(";"):
        fields = [f.strip() for f in obj.split(",")]
        if len(fields) >= 3 and fields[0].lower() == "output:meter" and fields[2].lower() == "hourly":
            present.add(fields[1].lower())
    return present


def append_hourly_meters(text):
    present = hourly_meter_names(text)
    missing = [m for m in HOURLY_METERS if m.lower() not in present]
    if not missing:
        return text
    tail = "" if text.endswith("\n") else "\n"
    return text + tail + "".join(f"Output:Meter,{m},Hourly;\n" for m in missing)


def main(argv):
    if len(argv) != 3:
        print("usage: add_hourly_meters.py <in.idf> <out.idf>", file=sys.stderr)
        return 2
    raw = Path(argv[1]).read_bytes().decode("utf-8", errors="surrogateescape")
    out = append_hourly_meters(raw)
    Path(argv[2]).write_bytes(out.encode("utf-8", errors="surrogateescape"))
    print(f"appended {len(out) - len(raw)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
