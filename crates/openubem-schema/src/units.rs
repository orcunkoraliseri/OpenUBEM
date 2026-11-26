//! Physical unit newtypes (`#[repr(transparent)]`) and `nutype` domain scalars.

use crate::error::SchemaError;
use nutype::nutype;
use serde::{Deserialize, Serialize};

/// Non-negative finite floor or footprint area in square meters (`m^2`).
#[nutype(
    validate(finite, greater_or_equal = 0.0),
    derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)
)]
pub struct AreaM2(f64);

/// Strictly positive finite denominator area in square meters (`m^2`).
#[nutype(
    validate(finite, greater = 0.0),
    derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)
)]
pub struct PositiveAreaM2(f64);

/// Finite confidence weight in `[0.0, 1.0]`.
#[nutype(
    validate(finite, greater_or_equal = 0.0, less_or_equal = 1.0),
    derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)
)]
pub struct ConfidenceWeight(f64);

/// Energy quantity in Joules (`J`).
#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Default, Serialize, Deserialize)]
pub struct EnergyJ(pub f64);

/// Energy quantity in kilowatt-hours (`kWh`).
#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Default, Serialize, Deserialize)]
pub struct EnergyKwh(pub f64);

/// Energy use intensity in `kWh / m^2`.
#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Default, Serialize, Deserialize)]
pub struct EuiKwhM2(pub f64);

/// Operational global warming potential intensity in `kg CO2e / m^2`.
#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Default, Serialize, Deserialize)]
pub struct GwpKgCo2M2(pub f64);

/// Thermal transmittance U-value in `W / (m^2 * K)`.
#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Default, Serialize, Deserialize)]
pub struct UValueWm2K(pub f64);

/// Temperature in degrees Celsius (`degC`).
#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Default, Serialize, Deserialize)]
pub struct TempCelsius(pub f64);

/// Thermodynamic temperature in Kelvin (`K`).
#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Default, Serialize, Deserialize)]
pub struct TempKelvin(pub f64);

/// Length or height in meters (`m`).
#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Default, Serialize, Deserialize)]
pub struct HeightM(pub f64);

/// Floor count (`>= 1`).
#[nutype(
    validate(greater_or_equal = 1),
    derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)
)]
pub struct FloorCount(i64);

/// Conversion constant from Joules to kWh (`1 / 3.6e6`).
pub const J_TO_KWH: f64 = 1.0 / 3_600_000.0;

/// Conversion constant from Gigajoules (EnergyPlus ABUPS table) to kWh (`1e6 / 3600`).
pub const GJ_TO_KWH: f64 = 1_000_000.0 / 3_600.0;

impl EnergyJ {
    /// Convert Joules to kilowatt-hours using the canonical OpenUBEM boundary factor.
    #[inline]
    pub const fn to_kwh(self) -> EnergyKwh {
        EnergyKwh(self.0 * J_TO_KWH)
    }
}

impl EnergyKwh {
    /// Divide annual `EnergyKwh` by `area_m2` to produce `EuiKwhM2`.
    #[inline]
    pub fn per_area(self, area: AreaM2) -> Result<EuiKwhM2, SchemaError> {
        let a = area.into_inner();
        if !a.is_finite() || a <= 0.0 {
            return Err(SchemaError::NonPositiveFloorArea(a));
        }
        Ok(EuiKwhM2(self.0 / a))
    }

    /// Convert to intensity using a pre-validated strictly positive area.
    #[inline]
    pub fn per_positive_area(self, area: PositiveAreaM2) -> EuiKwhM2 {
        EuiKwhM2(self.0 / area.into_inner())
    }
}

impl TempCelsius {
    /// Convert Celsius to Kelvin.
    #[inline]
    pub const fn to_kelvin(self) -> TempKelvin {
        TempKelvin(self.0 + 273.15)
    }
}

impl TempKelvin {
    /// Convert Kelvin to Celsius.
    #[inline]
    pub const fn to_celsius(self) -> TempCelsius {
        TempCelsius(self.0 - 273.15)
    }
}
