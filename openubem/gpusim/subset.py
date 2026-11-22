from dataclasses import dataclass

S0_ALLOWED_OBJECT_TYPES: frozenset[str] = frozenset(
    {
        "VERSION",
        "SIMULATIONCONTROL",
        "BUILDING",
        "HEATBALANCEALGORITHM",
        "TIMESTEP",
        "SITE:LOCATION",
        "SIZINGPERIOD:WEATHERFILEDAYS",
        "RUNPERIOD",
        "SIZING:ZONE",
        "GLOBALGEOMETRYRULES",
        "ZONE",
        "BUILDINGSURFACE:DETAILED",
        "FENESTRATIONSURFACE:DETAILED",
        "INTERNALMASS",
        "MATERIAL",
        "MATERIAL:NOMASS",
        "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM",
        "CONSTRUCTION",
        "SURFACEPROPERTY:OTHERSIDECOEFFICIENTS",
        "SCHEDULETYPELIMITS",
        "SCHEDULE:CONSTANT",
        "SCHEDULE:COMPACT",
        "SCHEDULE:FILE",
        "OTHEREQUIPMENT",
        "ZONEVENTILATION:DESIGNFLOWRATE",
        "THERMOSTATSETPOINT:DUALSETPOINT",
        "ZONECONTROL:THERMOSTAT",
        "ZONEHVAC:EQUIPMENTCONNECTIONS",
        "ZONEHVAC:EQUIPMENTLIST",
        "ZONEHVAC:IDEALLOADSAIRSYSTEM",
        "OUTPUT:VARIABLE",
        "OUTPUT:SQLITE",
        "OUTPUT:CONSTRUCTIONS",
        "OUTPUT:SURFACES:LIST",
    }
)


@dataclass(frozen=True)
class ParsedIdfObject:
    """Single parsed object from an expanded IDF file.

    Attributes:
        obj_type: Uppercase EnergyPlus object type.
        raw_type: Original-case object type as written in the IDF.
        fields: List of trimmed field strings excluding the object type.
    """

    obj_type: str
    raw_type: str
    fields: list[str]


@dataclass(frozen=True)
class SubsetCheckResult:
    """Result of validating an expanded IDF against the S0 whitelist.

    Attributes:
        passed: True if every object and non-default field fits S0.
        reason: First failing reason when ``passed`` is False, else ``None``.
    """

    passed: bool
    reason: str | None = None


def parse_expidf(idf_text: str) -> list[ParsedIdfObject]:
    """Parse an expanded IDF string into a sequence of objects.

    Args:
        idf_text: Full text of an ``eplusout.expidf`` file.

    Returns:
        List of ``ParsedIdfObject`` instances in file order.
    """
    stripped_lines: list[str] = []
    for line in idf_text.splitlines():
        bang = line.find("!")
        if bang >= 0:
            line = line[:bang]
        stripped_lines.append(line)
    blob = "\n".join(stripped_lines)

    objects: list[ParsedIdfObject] = []
    for chunk in blob.split(";"):
        text = chunk.strip()
        if not text:
            continue
        parts = [part.strip() for part in text.split(",")]
        raw_type = parts[0]
        if not raw_type:
            continue
        objects.append(
            ParsedIdfObject(
                obj_type=raw_type.upper(),
                raw_type=raw_type,
                fields=parts[1:],
            )
        )
    return objects


def _field(obj: ParsedIdfObject, index: int, default: str = "") -> str:
    """Return field at 0-based index or default if missing/blank.

    Args:
        obj: Parsed IDF object.
        index: Zero-based field index (after the object type).
        default: Default string when absent or empty.

    Returns:
        Field string or default.
    """
    if index >= len(obj.fields):
        return default
    val = obj.fields[index].strip()
    return val if val else default


def _float_field(obj: ParsedIdfObject, index: int, default: float = 0.0) -> float:
    """Parse a float field with default fallback for blanks.

    Args:
        obj: Parsed IDF object.
        index: Zero-based field index.
        default: Default numeric value when absent or empty.

    Returns:
        Parsed floating-point value.
    """
    raw = _field(obj, index, "")
    return float(raw) if raw else default


def _extract_constant_schedule_value(obj: ParsedIdfObject) -> float | None:
    """Extract constant numeric value from Schedule:Constant or compact constant.

    Args:
        obj: Parsed ``SCHEDULE:CONSTANT`` or ``SCHEDULE:COMPACT`` object.

    Returns:
        Constant float value if the schedule is constant all year, else ``None``.
    """
    if obj.obj_type == "SCHEDULE:CONSTANT":
        raw = _field(obj, 2, "")
        return float(raw) if raw else None
    if obj.obj_type == "SCHEDULE:COMPACT":
        if len(obj.fields) != 6:
            return None
        f2 = _field(obj, 2).casefold()
        f3 = _field(obj, 3).casefold()
        f4 = _field(obj, 4).casefold()
        if f2 != "through: 12/31" or f3 != "for: alldays" or f4 != "until: 24:00":
            return None
        return float(_field(obj, 5))
    return None


def _fail(reason: str) -> SubsetCheckResult:
    """Construct a failing ``SubsetCheckResult``.

    Args:
        reason: Human-readable explanation of the first unsupported feature.

    Returns:
        Failed ``SubsetCheckResult``.
    """
    return SubsetCheckResult(passed=False, reason=reason)


def check_s0_subset(idf_text: str) -> SubsetCheckResult:
    """Validate an expanded IDF against the S0 rung whitelist.

    Args:
        idf_text: Full text of an expanded IDF (``eplusout.expidf``).

    Returns:
        ``SubsetCheckResult`` indicating pass or the first failing reason.
    """
    objects = parse_expidf(idf_text)
    if not objects:
        return _fail("Empty IDF")

    for obj in objects:
        if obj.obj_type not in S0_ALLOWED_OBJECT_TYPES:
            return _fail(f"Unsupported object type for S0: {obj.raw_type}")

    by_type: dict[str, list[ParsedIdfObject]] = {}
    for obj in objects:
        by_type.setdefault(obj.obj_type, []).append(obj)

    zones = by_type.get("ZONE", [])
    if len(zones) != 1:
        return _fail(f"S0 requires exactly 1 Zone, found {len(zones)}")

    for hb in by_type.get("HEATBALANCEALGORITHM", []):
        algo = _field(hb, 0, "ConductionTransferFunction")
        if algo.casefold() != "conductiontransferfunction":
            return _fail(f"Unsupported HeatBalanceAlgorithm: {algo}")

    const_schedules: dict[str, float] = {}
    for sch in by_type.get("SCHEDULE:CONSTANT", []):
        name = _field(sch, 0).casefold()
        val = _extract_constant_schedule_value(sch)
        if val is None:
            return _fail(f"Schedule:Constant '{_field(sch, 0)}' missing value")
        const_schedules[name] = val

    for sch in by_type.get("SCHEDULE:COMPACT", []):
        name = _field(sch, 0).casefold()
        val = _extract_constant_schedule_value(sch)
        if val is None:
            return _fail(
                f"Non-constant Schedule:Compact '{_field(sch, 0)}' unsupported in S0"
            )
        const_schedules[name] = val

    for sch in by_type.get("SCHEDULE:FILE", []):
        interp = _field(sch, 7, "No")
        if interp.casefold() != "no":
            return _fail(
                f"Schedule:File '{_field(sch, 0)}' has Interpolate={interp}"
            )
        minutes = _float_field(sch, 8, 60.0)
        if abs(minutes - 60.0) > 1.0e-9:
            return _fail(
                f"Schedule:File '{_field(sch, 0)}' Minutes per Item={minutes} != 60"
            )

    nomass_names = {_field(o, 0).casefold() for o in by_type.get("MATERIAL:NOMASS", [])}
    mat_names = {_field(o, 0).casefold() for o in by_type.get("MATERIAL", [])}
    glass_names = {
        _field(o, 0).casefold()
        for o in by_type.get("WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", [])
    }
    constructions: dict[str, list[str]] = {}
    for cons in by_type.get("CONSTRUCTION", []):
        cname = _field(cons, 0).casefold()
        layers = [f.strip().casefold() for f in cons.fields[1:] if f.strip()]
        constructions[cname] = layers

    outdoor_surfaces: set[str] = set()
    for surf in by_type.get("BUILDINGSURFACE:DETAILED", []):
        sname = _field(surf, 0)
        cons_name = _field(surf, 2).casefold()
        bc = _field(surf, 5)
        sun_exp = _field(surf, 7, "SunExposed")
        wind_exp = _field(surf, 8, "WindExposed")
        if bc.casefold() not in ("outdoors", "othersidecoefficients"):
            return _fail(
                f"BuildingSurface:Detailed '{sname}' unsupported Outside Boundary "
                f"Condition='{bc}'"
            )
        if sun_exp.casefold() != "nosun":
            return _fail(
                f"BuildingSurface:Detailed '{sname}' has Sun Exposure='{sun_exp}' "
                f"(S0 requires NoSun)"
            )
        if wind_exp.casefold() != "nowind":
            return _fail(
                f"BuildingSurface:Detailed '{sname}' has Wind Exposure='{wind_exp}' "
                f"(S0 requires NoWind)"
            )
        layers = constructions.get(cons_name, [])
        if len(layers) != 1 or layers[0] not in nomass_names:
            return _fail(
                f"BuildingSurface:Detailed '{sname}' construction '{_field(surf, 2)}' "
                f"is not single-layer Material:NoMass"
            )
        if bc.casefold() == "outdoors":
            outdoor_surfaces.add(sname.casefold())

    for fen in by_type.get("FENESTRATIONSURFACE:DETAILED", []):
        fname = _field(fen, 0)
        ftype = _field(fen, 1)
        cons_name = _field(fen, 2).casefold()
        host_name = _field(fen, 3).casefold()
        frame = _field(fen, 6, "")
        mult = _float_field(fen, 7, 1.0)
        if frame:
            return _fail(
                f"FenestrationSurface:Detailed '{fname}' Frame and Divider='{frame}'"
            )
        if abs(mult - 1.0) > 1.0e-9:
            return _fail(
                f"FenestrationSurface:Detailed '{fname}' Multiplier={mult} != 1"
            )
        layers = constructions.get(cons_name, [])
        if ftype.casefold() == "window":
            if len(layers) != 1 or layers[0] not in glass_names:
                return _fail(
                    f"Window '{fname}' construction is not SimpleGlazingSystem"
                )
        elif ftype.casefold() == "door":
            if len(layers) != 1 or layers[0] not in nomass_names:
                return _fail(f"Door '{fname}' construction is not Material:NoMass")
            if host_name not in outdoor_surfaces:
                return _fail(f"Door '{fname}' host surface is not Outdoors")
        else:
            return _fail(
                f"FenestrationSurface:Detailed '{fname}' unsupported type='{ftype}'"
            )

    int_masses = by_type.get("INTERNALMASS", [])
    if len(int_masses) > 1:
        return _fail(f"S0 supports at most 1 InternalMass, found {len(int_masses)}")
    for im in int_masses:
        cons_name = _field(im, 1).casefold()
        layers = constructions.get(cons_name, [])
        if len(layers) != 1 or layers[0] not in mat_names:
            return _fail(
                f"InternalMass '{_field(im, 0)}' construction is not 1-layer Material"
            )

    for osc in by_type.get("SURFACEPROPERTY:OTHERSIDECOEFFICIENTS", []):
        oname = _field(osc, 0)
        film = _float_field(osc, 1, 0.0)
        if abs(film) > 1.0e-12:
            return _fail(
                f"SurfaceProperty:OtherSideCoefficients '{oname}' film={film} != 0"
            )
        if _field(osc, 8, ""):
            return _fail(
                f"SurfaceProperty:OtherSideCoefficients '{oname}' has schedule"
            )
        if _field(osc, 9, "No").casefold() != "no":
            return _fail(
                f"SurfaceProperty:OtherSideCoefficients '{oname}' sinusoidal active"
            )
        if (
            abs(_float_field(osc, 5, 0.0)) > 1.0e-12
            or abs(_float_field(osc, 6, 0.0)) > 1.0e-12
            or abs(_float_field(osc, 11, 0.0)) > 1.0e-12
        ):
            return _fail(
                f"SurfaceProperty:OtherSideCoefficients '{oname}' unsupported coeff"
            )

    for eq in by_type.get("OTHEREQUIPMENT", []):
        ename = _field(eq, 0)
        if (
            abs(_float_field(eq, 8, 0.0)) > 1.0e-12
            or abs(_float_field(eq, 9, 0.0)) > 1.0e-12
            or abs(_float_field(eq, 10, 0.0)) > 1.0e-12
        ):
            return _fail(f"OtherEquipment '{ename}' is not 100% convective")

    for vent in by_type.get("ZONEVENTILATION:DESIGNFLOWRATE", []):
        vname = _field(vent, 0)
        vtype = _field(vent, 8, "Natural")
        if vtype.casefold() != "natural":
            return _fail(
                f"ZoneVentilation:DesignFlowRate '{vname}' Ventilation Type='{vtype}'"
            )
        if abs(_float_field(vent, 9, 0.0)) > 1.0e-12:
            return _fail(
                f"ZoneVentilation:DesignFlowRate '{vname}' non-zero fan pressure rise"
            )
        if (
            abs(_float_field(vent, 11, 1.0) - 1.0) > 1.0e-12
            or abs(_float_field(vent, 12, 0.0)) > 1.0e-12
            or abs(_float_field(vent, 13, 0.0)) > 1.0e-12
            or abs(_float_field(vent, 14, 0.0)) > 1.0e-12
        ):
            return _fail(
                f"ZoneVentilation:DesignFlowRate '{vname}' non-constant flow coeffs"
            )

    ideals = by_type.get("ZONEHVAC:IDEALLOADSAIRSYSTEM", [])
    if len(ideals) != 1:
        return _fail(
            f"S0 requires exactly 1 ZoneHVAC:IdealLoadsAirSystem, found {len(ideals)}"
        )
    ideal = ideals[0]
    iname = _field(ideal, 0)
    if _field(ideal, 9, "NoLimit").casefold() != "nolimit":
        return _fail(
            f"ZoneHVAC:IdealLoadsAirSystem '{iname}' Heating Limit="
            f"'{_field(ideal, 9)}' != NoLimit"
        )
    if _field(ideal, 12, "NoLimit").casefold() != "nolimit":
        return _fail(
            f"ZoneHVAC:IdealLoadsAirSystem '{iname}' Cooling Limit="
            f"'{_field(ideal, 12)}' != NoLimit"
        )
    cool_avail = _field(ideal, 16, "").casefold()
    if cool_avail not in const_schedules or abs(const_schedules[cool_avail]) > 1.0e-12:
        return _fail(
            f"ZoneHVAC:IdealLoadsAirSystem '{iname}' cooling is not disabled"
        )
    if _field(ideal, 20, "") or _field(ideal, 21, ""):
        return _fail(
            f"ZoneHVAC:IdealLoadsAirSystem '{iname}' has outdoor air enabled"
        )
    if _field(ideal, 22, "None").casefold() != "none":
        return _fail(
            f"ZoneHVAC:IdealLoadsAirSystem '{iname}' has DCV='{_field(ideal, 22)}'"
        )
    if _field(ideal, 23, "NoEconomizer").casefold() != "noeconomizer":
        return _fail(
            f"ZoneHVAC:IdealLoadsAirSystem '{iname}' economizer='{_field(ideal, 23)}'"
        )
    if _field(ideal, 24, "None").casefold() != "none":
        return _fail(
            f"ZoneHVAC:IdealLoadsAirSystem '{iname}' heat recovery="
            f"'{_field(ideal, 24)}'"
        )
    if _field(ideal, 19, "None").casefold() != "none":
        return _fail(
            f"ZoneHVAC:IdealLoadsAirSystem '{iname}' humidification="
            f"'{_field(ideal, 19)}'"
        )

    return SubsetCheckResult(passed=True, reason=None)
