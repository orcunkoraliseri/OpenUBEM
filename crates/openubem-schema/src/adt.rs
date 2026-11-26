//! Exhaustive algebraic data types and double-count-proof `EndUseLedger` typestate.

use std::collections::BTreeMap;
use std::marker::PhantomData;

use serde::{Deserialize, Serialize};

use crate::error::SchemaError;
use crate::units::{EnergyKwh, GwpKgCo2M2, PositiveAreaM2};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ledger_defolds_elevators_without_double_counting() {
        let area = PositiveAreaM2::try_new(100.0).unwrap();
        let mut ledger = EndUseLedger::new(ResolvedFloorArea {
            area_m2: area,
            provenance: FloorAreaProvenance::EioSimulated,
        });
        ledger.set_core_gas_elec(EndUse::InteriorEquipment, 0.0, 1000.0);
        ledger.set_core_gas_elec(EndUse::Elevators, 0.0, 200.0);
        ledger.set_abups_district(AbupsDistrictRow::WaterSystems, 300.0);
        ledger.set_abups_district(AbupsDistrictRow::Generators, 50.0);
        let rec = ledger.reconcile().unwrap();
        let eui = rec.to_eui_columns();
        assert!((eui["equipment_eui_kwh_m2"] - 8.0).abs() < 1e-12);
        assert!((eui["elevators_eui_kwh_m2"] - 2.0).abs() < 1e-12);
        assert!((eui["dhw_district_eui_kwh_m2"] - 3.0).abs() < 1e-12);
        assert!((eui["generators_eui_kwh_m2"] - 0.5).abs() < 1e-12);
        assert!((eui["total_eui_kwh_m2"] - 13.5).abs() < 1e-12);
    }
}

/// Exhaustive 10 core OpenUBEM end-uses (matching `parser.py` & `OPEN-46`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[repr(usize)]
pub enum EndUse {
    Heating = 0,
    Cooling = 1,
    InteriorLighting = 2,
    InteriorEquipment = 3,
    Fans = 4,
    Pumps = 5,
    WaterSystems = 6,
    Cooking = 7,
    Refrigeration = 8,
    Elevators = 9,
}

impl EndUse {
    /// All 10 core end-uses in fixed array order.
    pub const ALL: [EndUse; 10] = [
        EndUse::Heating,
        EndUse::Cooling,
        EndUse::InteriorLighting,
        EndUse::InteriorEquipment,
        EndUse::Fans,
        EndUse::Pumps,
        EndUse::WaterSystems,
        EndUse::Cooking,
        EndUse::Refrigeration,
        EndUse::Elevators,
    ];
}

/// The 6 pure-district ABUPS rows added in `OPEN-64 T03` (`carbon.py:114-122`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[repr(usize)]
pub enum PureDistrictEndUse {
    ExteriorLighting = 0,
    ExteriorEquipment = 1,
    HeatRejection = 2,
    Humidification = 3,
    HeatRecovery = 4,
    Generators = 5,
}

impl PureDistrictEndUse {
    /// All 6 pure-district end-uses in fixed array order.
    pub const ALL: [PureDistrictEndUse; 6] = [
        PureDistrictEndUse::ExteriorLighting,
        PureDistrictEndUse::ExteriorEquipment,
        PureDistrictEndUse::HeatRejection,
        PureDistrictEndUse::Humidification,
        PureDistrictEndUse::HeatRecovery,
        PureDistrictEndUse::Generators,
    ];
}

/// Exhaustive mapping of all 14 EnergyPlus ABUPS "End Uses" District Heating rows (`OPEN-64`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum AbupsDistrictRow {
    Heating,
    Cooling,
    InteriorLighting,
    ExteriorLighting,
    InteriorEquipment,
    ExteriorEquipment,
    Fans,
    Pumps,
    HeatRejection,
    Humidification,
    HeatRecovery,
    WaterSystems,
    Refrigeration,
    Generators,
}

/// Target slot in [`EndUseLedger`] for an ABUPS District Heating row.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AbupsSlot {
    /// Attaches `.district` kWh to one of the 10 core end-uses (splitting fuel provenance).
    Core(EndUse),
    /// Attaches `.district` kWh to one of the 6 pure-district columns.
    PureDistrict(PureDistrictEndUse),
}

impl AbupsDistrictRow {
    /// All 14 canonical ABUPS District Heating rows.
    pub const ALL: [AbupsDistrictRow; 14] = [
        AbupsDistrictRow::Heating,
        AbupsDistrictRow::Cooling,
        AbupsDistrictRow::InteriorLighting,
        AbupsDistrictRow::ExteriorLighting,
        AbupsDistrictRow::InteriorEquipment,
        AbupsDistrictRow::ExteriorEquipment,
        AbupsDistrictRow::Fans,
        AbupsDistrictRow::Pumps,
        AbupsDistrictRow::HeatRejection,
        AbupsDistrictRow::Humidification,
        AbupsDistrictRow::HeatRecovery,
        AbupsDistrictRow::WaterSystems,
        AbupsDistrictRow::Refrigeration,
        AbupsDistrictRow::Generators,
    ];

    /// Parse exact EnergyPlus ABUPS `RowName`.
    pub fn from_abups_row_name(name: &str) -> Option<Self> {
        match name.trim() {
            "Heating" => Some(Self::Heating),
            "Cooling" => Some(Self::Cooling),
            "Interior Lighting" => Some(Self::InteriorLighting),
            "Exterior Lighting" => Some(Self::ExteriorLighting),
            "Interior Equipment" => Some(Self::InteriorEquipment),
            "Exterior Equipment" => Some(Self::ExteriorEquipment),
            "Fans" => Some(Self::Fans),
            "Pumps" => Some(Self::Pumps),
            "Heat Rejection" => Some(Self::HeatRejection),
            "Humidification" => Some(Self::Humidification),
            "Heat Recovery" => Some(Self::HeatRecovery),
            "Water Systems" => Some(Self::WaterSystems),
            "Refrigeration" => Some(Self::Refrigeration),
            "Generators" => Some(Self::Generators),
            _ => None,
        }
    }

    /// Exact EnergyPlus ABUPS `RowName`.
    pub const fn as_abups_row_name(self) -> &'static str {
        match self {
            Self::Heating => "Heating",
            Self::Cooling => "Cooling",
            Self::InteriorLighting => "Interior Lighting",
            Self::ExteriorLighting => "Exterior Lighting",
            Self::InteriorEquipment => "Interior Equipment",
            Self::ExteriorEquipment => "Exterior Equipment",
            Self::Fans => "Fans",
            Self::Pumps => "Pumps",
            Self::HeatRejection => "Heat Rejection",
            Self::Humidification => "Humidification",
            Self::HeatRecovery => "Heat Recovery",
            Self::WaterSystems => "Water Systems",
            Self::Refrigeration => "Refrigeration",
            Self::Generators => "Generators",
        }
    }

    /// OpenUBEM pseudo-meter key used in `parser.py::_DISTRICT_HEATING_ROWS`.
    pub const fn pseudo_meter_key(self) -> &'static str {
        match self {
            Self::Heating => "Heating:DistrictHeating",
            Self::Cooling => "Cooling:DistrictHeating",
            Self::InteriorLighting => "InteriorLighting:DistrictHeating",
            Self::ExteriorLighting => "ExteriorLighting:DistrictHeating",
            Self::InteriorEquipment => "InteriorEquipment:DistrictHeating",
            Self::ExteriorEquipment => "ExteriorEquipment:DistrictHeating",
            Self::Fans => "Fans:DistrictHeating",
            Self::Pumps => "Pumps:DistrictHeating",
            Self::HeatRejection => "HeatRejection:DistrictHeating",
            Self::Humidification => "Humidification:DistrictHeating",
            Self::HeatRecovery => "HeatRecovery:DistrictHeating",
            Self::WaterSystems => "WaterSystems:DistrictHeating",
            Self::Refrigeration => "Refrigeration:DistrictHeating",
            Self::Generators => "Generators:DistrictHeating",
        }
    }

    /// Exhaustive slot assignment guaranteeing no ABUPS row is double-counted or dropped.
    pub const fn slot(self) -> AbupsSlot {
        match self {
            Self::Heating => AbupsSlot::Core(EndUse::Heating),
            Self::Cooling => AbupsSlot::Core(EndUse::Cooling),
            Self::InteriorLighting => AbupsSlot::Core(EndUse::InteriorLighting),
            Self::InteriorEquipment => AbupsSlot::Core(EndUse::InteriorEquipment),
            Self::Fans => AbupsSlot::Core(EndUse::Fans),
            Self::Pumps => AbupsSlot::Core(EndUse::Pumps),
            Self::WaterSystems => AbupsSlot::Core(EndUse::WaterSystems),
            Self::Refrigeration => AbupsSlot::Core(EndUse::Refrigeration),
            Self::ExteriorLighting => AbupsSlot::PureDistrict(PureDistrictEndUse::ExteriorLighting),
            Self::ExteriorEquipment => AbupsSlot::PureDistrict(PureDistrictEndUse::ExteriorEquipment),
            Self::HeatRejection => AbupsSlot::PureDistrict(PureDistrictEndUse::HeatRejection),
            Self::Humidification => AbupsSlot::PureDistrict(PureDistrictEndUse::Humidification),
            Self::HeatRecovery => AbupsSlot::PureDistrict(PureDistrictEndUse::HeatRecovery),
            Self::Generators => AbupsSlot::PureDistrict(PureDistrictEndUse::Generators),
        }
    }
}

/// Exhaustive simulation/parse outcome vocabulary across Step 4 and Step 5.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SimulationStatus {
    Success,
    SuccessCached,
    SuccessCsvFallback,
    FailedParse,
    FailedZoneMismatch,
    FailedEnergyplus,
    FailedFatal,
    FailedCrash,
    FailedTimeout,
    NotAttemptedInvalidIdf,
    NotSimulated,
}

impl SimulationStatus {
    /// Parse a canonical simulation status token.
    pub fn from_token(token: &str) -> Result<Self, SchemaError> {
        match token.trim() {
            "success" => Ok(Self::Success),
            "success_cached" => Ok(Self::SuccessCached),
            "success_csv_fallback" => Ok(Self::SuccessCsvFallback),
            "failed_parse" => Ok(Self::FailedParse),
            "failed_zone_mismatch" => Ok(Self::FailedZoneMismatch),
            "failed_energyplus" => Ok(Self::FailedEnergyplus),
            "failed_fatal" => Ok(Self::FailedFatal),
            "failed_crash" => Ok(Self::FailedCrash),
            "failed_timeout" => Ok(Self::FailedTimeout),
            "not_attempted_invalid_idf" => Ok(Self::NotAttemptedInvalidIdf),
            "not_simulated" => Ok(Self::NotSimulated),
            other => Err(SchemaError::InvalidSimulationStatus(other.to_owned())),
        }
    }

    /// Canonical snake_case string matching OpenUBEM manifests.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Success => "success",
            Self::SuccessCached => "success_cached",
            Self::SuccessCsvFallback => "success_csv_fallback",
            Self::FailedParse => "failed_parse",
            Self::FailedZoneMismatch => "failed_zone_mismatch",
            Self::FailedEnergyplus => "failed_energyplus",
            Self::FailedFatal => "failed_fatal",
            Self::FailedCrash => "failed_crash",
            Self::FailedTimeout => "failed_timeout",
            Self::NotAttemptedInvalidIdf => "not_attempted_invalid_idf",
            Self::NotSimulated => "not_simulated",
        }
    }

    /// Single source of truth replacing four duplicated `_SUCCESS_STATUSES` Python sets.
    pub const fn is_success(self) -> bool {
        matches!(
            self,
            Self::Success | Self::SuccessCached | Self::SuccessCsvFallback
        )
    }

    /// True if simulation attempted EnergyPlus and finished cleanly before Step 5 harvest.
    pub const fn is_sim_complete(self) -> bool {
        matches!(self, Self::Success | Self::SuccessCached)
    }
}

/// Floor-area denominator resolution lineage (`OPEN-01` ruling 6 & `FLEET-06c-FIX`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FloorAreaProvenance {
    EioSimulated,
    SqlSimulated,
    FootprintFallback,
}

impl FloorAreaProvenance {
    /// Exact Python string emitted by `resolve_simulated_floor_area`.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::EioSimulated => "eio_simulated",
            Self::SqlSimulated => "sql_simulated",
            Self::FootprintFallback => "footprint_fallback",
        }
    }
}

/// Single locked denominator bound to an [`EndUseLedger`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResolvedFloorArea {
    pub area_m2: PositiveAreaM2,
    pub provenance: FloorAreaProvenance,
}

/// Simulation engine provenance attached to every reported energy result (`CLAUDE.md` hard rule).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EngineProvenance {
    EnergyPlus { version: String },
    GpuSim { kernel: String },
    RustSim { conformance_sha256: String },
}

/// Fuel breakdown in kilowatt-hours (`kWh`) for one core end-use slot.
#[derive(Debug, Clone, Copy, Default, PartialEq, Serialize, Deserialize)]
pub struct FuelSplitKwh {
    pub gas: f64,
    pub elec: f64,
    pub district: f64,
}

impl FuelSplitKwh {
    /// Total kWh across all fuels for this slot.
    #[inline]
    pub fn total(self) -> EnergyKwh {
        EnergyKwh(self.gas + self.elec + self.district)
    }

    /// Validate all fuel components are finite and non-negative.
    pub fn validate_non_negative(&self, field: &str) -> Result<(), SchemaError> {
        for (sub, val) in [
            ("gas", self.gas),
            ("elec", self.elec),
            ("district", self.district),
        ] {
            if !val.is_finite() || val < 0.0 {
                return Err(SchemaError::InvalidEnergyValue {
                    field: format!("{field}.{sub}"),
                    value: val,
                });
            }
        }
        Ok(())
    }
}

/// Typestate marker: un-reconciled raw meters before `OPEN-46` elevator de-folding.
pub struct RawMeters;

/// Typestate marker: validated, reconciled ledger safe for EUI/GWP computation.
pub struct ReconciledLedger;

/// Double-count-proof building end-use energy ledger.
#[derive(Debug, Clone)]
pub struct EndUseLedger<State> {
    floor_area: ResolvedFloorArea,
    core: [FuelSplitKwh; 10],
    pure_district: [f64; 6],
    raw_elevators_elec_kwh: f64,
    _state: PhantomData<State>,
}

impl EndUseLedger<RawMeters> {
    /// Construct a new raw ledger bound to a strictly positive [`ResolvedFloorArea`].
    pub fn new(floor_area: ResolvedFloorArea) -> Self {
        Self {
            floor_area,
            core: [FuelSplitKwh::default(); 10],
            pure_district: [0.0; 6],
            raw_elevators_elec_kwh: 0.0,
            _state: PhantomData,
        }
    }

    /// Populate electricity/gas inputs mirroring `parser.py::_compute_eui`.
    pub fn set_core_gas_elec(&mut self, end_use: EndUse, gas_kwh: f64, elec_kwh: f64) {
        if end_use == EndUse::Elevators {
            self.raw_elevators_elec_kwh = elec_kwh;
        } else {
            self.core[end_use as usize].gas = gas_kwh;
            self.core[end_use as usize].elec = elec_kwh;
        }
    }

    /// Populate one of the 14 ABUPS District Heating rows exhaustively without double-counting.
    pub fn set_abups_district(&mut self, row: AbupsDistrictRow, kwh: f64) {
        match row.slot() {
            AbupsSlot::Core(end_use) => {
                self.core[end_use as usize].district = kwh;
            }
            AbupsSlot::PureDistrict(pure) => {
                self.pure_district[pure as usize] = kwh;
            }
        }
    }

    /// Transition `RawMeters -> ReconciledLedger` once by value.
    ///
    /// Performs the `OPEN-46` guarded elevator de-folding exactly once: when the
    /// elevator subcategory meter is non-zero, it subtracts `elevator_kwh / area`
    /// after computing `equipment_kwh / area` identically to Python `parser.py:732-736`,
    /// preserving bit-exact behavior and preventing double de-folding at compile time.
    pub fn reconcile(mut self) -> Result<EndUseLedger<ReconciledLedger>, SchemaError> {
        let elev = self.raw_elevators_elec_kwh;
        if !elev.is_finite() || elev < 0.0 {
            return Err(SchemaError::InvalidEnergyValue {
                field: "elevators.elec".to_owned(),
                value: elev,
            });
        }
        if elev != 0.0 {
            self.core[EndUse::Elevators as usize].elec = elev;
        }
        for (idx, split) in self.core.iter().enumerate() {
            split.validate_non_negative(&format!("{:?}", EndUse::ALL[idx]))?;
        }
        for (idx, &val) in self.pure_district.iter().enumerate() {
            if !val.is_finite() || val < 0.0 {
                return Err(SchemaError::InvalidEnergyValue {
                    field: format!("{:?}", PureDistrictEndUse::ALL[idx]),
                    value: val,
                });
            }
        }
        Ok(EndUseLedger {
            floor_area: self.floor_area,
            core: self.core,
            pure_district: self.pure_district,
            raw_elevators_elec_kwh: elev,
            _state: PhantomData,
        })
    }
}

impl EndUseLedger<ReconciledLedger> {
    /// Bound floor-area denominator.
    pub const fn floor_area(&self) -> ResolvedFloorArea {
        self.floor_area
    }

    /// Compute the exact Step-5 EUI column dictionary matching `openubem/results/parser.py::_compute_eui`.
    pub fn to_eui_columns(&self) -> BTreeMap<&'static str, f64> {
        let a = self.floor_area.area_m2.into_inner();
        let c = &self.core;
        let p = &self.pure_district;

        let cooling_eui = c[EndUse::Cooling as usize].total().0 / a;
        let heating_eui = c[EndUse::Heating as usize].total().0 / a;
        let lighting_eui = (c[EndUse::InteriorLighting as usize].elec / a)
            + (c[EndUse::InteriorLighting as usize].district / a);

        let equip_base = c[EndUse::InteriorEquipment as usize].elec / a;
        let mut equipment_eui = equip_base + (c[EndUse::InteriorEquipment as usize].district / a);

        let fans_eui = c[EndUse::Fans as usize].total().0 / a;
        let pumps_eui = c[EndUse::Pumps as usize].total().0 / a;
        let dhw_gas_eui = c[EndUse::WaterSystems as usize].gas / a;
        let dhw_elec_eui = c[EndUse::WaterSystems as usize].elec / a;
        let dhw_district_eui = c[EndUse::WaterSystems as usize].district / a;
        let dhw_eui = c[EndUse::WaterSystems as usize].total().0 / a;
        let cooking_eui = c[EndUse::Cooking as usize].gas / a;
        let refrigeration_eui = c[EndUse::Refrigeration as usize].total().0 / a;

        let cooling_district_eui = c[EndUse::Cooling as usize].district / a;
        let heating_district_eui = c[EndUse::Heating as usize].district / a;
        let fans_district_eui = c[EndUse::Fans as usize].district / a;
        let pumps_district_eui = c[EndUse::Pumps as usize].district / a;
        let refrigeration_district_eui = c[EndUse::Refrigeration as usize].district / a;
        let lighting_district_eui = c[EndUse::InteriorLighting as usize].district / a;
        let equipment_district_eui = c[EndUse::InteriorEquipment as usize].district / a;

        let exterior_lighting_eui = p[PureDistrictEndUse::ExteriorLighting as usize] / a;
        let exterior_equipment_eui = p[PureDistrictEndUse::ExteriorEquipment as usize] / a;
        let heat_rejection_eui = p[PureDistrictEndUse::HeatRejection as usize] / a;
        let humidification_eui = p[PureDistrictEndUse::Humidification as usize] / a;
        let heat_recovery_eui = p[PureDistrictEndUse::HeatRecovery as usize] / a;
        let generators_eui = p[PureDistrictEndUse::Generators as usize] / a;

        let elevators_eui = self.raw_elevators_elec_kwh / a;
        if self.raw_elevators_elec_kwh != 0.0 {
            equipment_eui -= elevators_eui;
        }

        let total_eui = cooling_eui
            + heating_eui
            + lighting_eui
            + equipment_eui
            + fans_eui
            + pumps_eui
            + dhw_eui
            + cooking_eui
            + refrigeration_eui
            + elevators_eui
            + exterior_lighting_eui
            + exterior_equipment_eui
            + heat_rejection_eui
            + humidification_eui
            + heat_recovery_eui
            + generators_eui;

        let mut map = BTreeMap::new();
        map.insert("cooling_eui_kwh_m2", cooling_eui);
        map.insert("heating_eui_kwh_m2", heating_eui);
        map.insert("lighting_eui_kwh_m2", lighting_eui);
        map.insert("equipment_eui_kwh_m2", equipment_eui);
        map.insert("fans_eui_kwh_m2", fans_eui);
        map.insert("pumps_eui_kwh_m2", pumps_eui);
        map.insert("dhw_gas_eui_kwh_m2", dhw_gas_eui);
        map.insert("dhw_elec_eui_kwh_m2", dhw_elec_eui);
        map.insert("dhw_district_eui_kwh_m2", dhw_district_eui);
        map.insert("dhw_eui_kwh_m2", dhw_eui);
        map.insert("cooking_eui_kwh_m2", cooking_eui);
        map.insert("refrigeration_eui_kwh_m2", refrigeration_eui);
        map.insert("cooling_district_eui_kwh_m2", cooling_district_eui);
        map.insert("heating_district_eui_kwh_m2", heating_district_eui);
        map.insert("fans_district_eui_kwh_m2", fans_district_eui);
        map.insert("pumps_district_eui_kwh_m2", pumps_district_eui);
        map.insert("refrigeration_district_eui_kwh_m2", refrigeration_district_eui);
        map.insert("lighting_district_eui_kwh_m2", lighting_district_eui);
        map.insert("equipment_district_eui_kwh_m2", equipment_district_eui);
        map.insert("exterior_lighting_eui_kwh_m2", exterior_lighting_eui);
        map.insert("exterior_equipment_eui_kwh_m2", exterior_equipment_eui);
        map.insert("heat_rejection_eui_kwh_m2", heat_rejection_eui);
        map.insert("humidification_eui_kwh_m2", humidification_eui);
        map.insert("heat_recovery_eui_kwh_m2", heat_recovery_eui);
        map.insert("generators_eui_kwh_m2", generators_eui);
        map.insert("elevators_eui_kwh_m2", elevators_eui);
        map.insert("total_eui_kwh_m2", total_eui);
        map
    }

    /// Compute GWP intensities (`kg CO2e / m^2`) matching `openubem/results/carbon.py::compute_gwp`.
    pub fn to_gwp_columns(
        &self,
        f_gas: f64,
        f_elec: f64,
        f_dh: f64,
    ) -> Result<BTreeMap<&'static str, GwpKgCo2M2>, SchemaError> {
        for (name, val) in [("gas", f_gas), ("elec", f_elec), ("district", f_dh)] {
            if !val.is_finite() || val < 0.0 {
                return Err(SchemaError::InvalidCarbonFactor {
                    fuel: name.to_owned(),
                    value: val,
                });
            }
        }
        let eui = self.to_eui_columns();
        let gwp_h = (eui["heating_eui_kwh_m2"] - eui["heating_district_eui_kwh_m2"]) * f_gas
            + eui["heating_district_eui_kwh_m2"] * f_dh;
        let gwp_c = (eui["cooling_eui_kwh_m2"] - eui["cooling_district_eui_kwh_m2"]) * f_elec
            + eui["cooling_district_eui_kwh_m2"] * f_dh;
        let gwp_l = (eui["lighting_eui_kwh_m2"] - eui["lighting_district_eui_kwh_m2"]) * f_elec
            + eui["lighting_district_eui_kwh_m2"] * f_dh;
        let gwp_e = (eui["equipment_eui_kwh_m2"] - eui["equipment_district_eui_kwh_m2"]) * f_elec
            + eui["equipment_district_eui_kwh_m2"] * f_dh;
        let gwp_fans = (eui["fans_eui_kwh_m2"] - eui["fans_district_eui_kwh_m2"]) * f_elec
            + eui["fans_district_eui_kwh_m2"] * f_dh;
        let gwp_pumps = (eui["pumps_eui_kwh_m2"] - eui["pumps_district_eui_kwh_m2"]) * f_elec
            + eui["pumps_district_eui_kwh_m2"] * f_dh;
        let gwp_dhw = eui["dhw_gas_eui_kwh_m2"] * f_gas
            + eui["dhw_elec_eui_kwh_m2"] * f_elec
            + eui["dhw_district_eui_kwh_m2"] * f_dh;
        let gwp_cooking = eui["cooking_eui_kwh_m2"] * f_gas;
        let gwp_refrig = (eui["refrigeration_eui_kwh_m2"]
            - eui["refrigeration_district_eui_kwh_m2"])
            * f_elec
            + eui["refrigeration_district_eui_kwh_m2"] * f_dh;
        let gwp_elevators = eui["elevators_eui_kwh_m2"] * f_elec;

        let gwp_ext_l = eui["exterior_lighting_eui_kwh_m2"] * f_dh;
        let gwp_ext_e = eui["exterior_equipment_eui_kwh_m2"] * f_dh;
        let gwp_hr = eui["heat_rejection_eui_kwh_m2"] * f_dh;
        let gwp_hum = eui["humidification_eui_kwh_m2"] * f_dh;
        let gwp_hrec = eui["heat_recovery_eui_kwh_m2"] * f_dh;
        let gwp_gen = eui["generators_eui_kwh_m2"] * f_dh;

        let total = gwp_h
            + gwp_c
            + gwp_l
            + gwp_e
            + gwp_fans
            + gwp_pumps
            + gwp_dhw
            + gwp_cooking
            + gwp_refrig
            + gwp_elevators
            + gwp_ext_l
            + gwp_ext_e
            + gwp_hr
            + gwp_hum
            + gwp_hrec
            + gwp_gen;

        let mut map = BTreeMap::new();
        map.insert("gwp_heating_kgco2_m2", GwpKgCo2M2(gwp_h));
        map.insert("gwp_cooling_kgco2_m2", GwpKgCo2M2(gwp_c));
        map.insert("gwp_lighting_kgco2_m2", GwpKgCo2M2(gwp_l));
        map.insert("gwp_equipment_kgco2_m2", GwpKgCo2M2(gwp_e));
        map.insert("gwp_fans_kgco2_m2", GwpKgCo2M2(gwp_fans));
        map.insert("gwp_pumps_kgco2_m2", GwpKgCo2M2(gwp_pumps));
        map.insert("gwp_dhw_kgco2_m2", GwpKgCo2M2(gwp_dhw));
        map.insert("gwp_cooking_kgco2_m2", GwpKgCo2M2(gwp_cooking));
        map.insert("gwp_refrigeration_kgco2_m2", GwpKgCo2M2(gwp_refrig));
        map.insert("gwp_elevators_kgco2_m2", GwpKgCo2M2(gwp_elevators));
        map.insert("gwp_exterior_lighting_kgco2_m2", GwpKgCo2M2(gwp_ext_l));
        map.insert("gwp_exterior_equipment_kgco2_m2", GwpKgCo2M2(gwp_ext_e));
        map.insert("gwp_heat_rejection_kgco2_m2", GwpKgCo2M2(gwp_hr));
        map.insert("gwp_humidification_kgco2_m2", GwpKgCo2M2(gwp_hum));
        map.insert("gwp_heat_recovery_kgco2_m2", GwpKgCo2M2(gwp_hrec));
        map.insert("gwp_generators_kgco2_m2", GwpKgCo2M2(gwp_gen));
        map.insert("gwp_total_kgco2_m2", GwpKgCo2M2(total));
        Ok(map)
    }
}
