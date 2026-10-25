"""
Empirical monthly seasonality and occupancy weights calibrated with INE data.

Source: Instituto Nacional de Estadistica (INE) - Encuesta de Ocupacion en Alojamientos
de Turismo Rural (EOTR) para la Provincia de Segovia.

The monthly series below is calibrated so that the day-weighted annual average
equals the official INE Segovia room-occupancy rate for 2025 (21.24%, 77.5
occupied days per available room). The seasonal shape reproduces the observed
winter trough (January ~9.6%) and summer peak (August ~36.8%).

Three occupancy anchors are used across the model:

1. PROMOTER_OCCUPANCY = 19.2%  -> implied by the 491 / 72 night volumes in the
   promoter case (491 / 7 / 365 = 19.22%). It is not a cell in either workbook:
   the `Plan de Negocio` formula sheet uses 66.325 occupied days (18.17%).
   (491 room-nights / 2,555 available room-nights). This is the "as-promoted"
   case and the most conservative anchor.
2. MARKET_OCCUPANCY = 21.24%   -> official INE Segovia 2025. This is the
   independent market benchmark.
3. MANAGEMENT_OCCUPANCY = 31.36% -> the management/upside case used by the
   Python engine (weekend-weighted boutique positioning). It is 1.48x the
   official market average and must be labelled as an upside case, not as
   "INE calibrated".

Provides:
1. Historical monthly occupancy benchmarks for Segovia rural lodging.
2. Weekend vs. weekday structural asymmetry factors.
3. Monthly ADR index adjustments.
"""

from dataclasses import dataclass
from typing import Dict, List


# Official INE EOTR Segovia annual room occupancy (2025: 21.24%, 77.5 days).
MARKET_OCCUPANCY: float = 0.2124
PROMOTER_OCCUPANCY: float = 0.1920
MANAGEMENT_OCCUPANCY: float = 0.3136438356164383  # 114.48 occupied days / 365


@dataclass(frozen=True)
class MonthlySeasonality:
    month_index: int
    month_name: str
    days_in_month: int
    # Official INE Segovia rural lodging benchmark occupancy (market case).
    ine_rural_occupancy: float
    # Management/upside target occupancy (boutique weekend positioning).
    base_occupancy: float
    # ADR seasonal premium multiplier (1.0 = baseline ADR)
    adr_seasonal_factor: float


# Calibration based on INE EOTR series for Segovia:
# Winter trough (Jan-Feb), Spring lift (Mar-Apr-May), Summer peak (Jul-Aug),
# Autumn trekking/harvest season (Sep-Oct), and Holiday bridges (Nov-Dec).
#
# The `ine_rural_occupancy` column is calibrated to the official 21.24% annual
# average (2025). January (9.58%) and August (36.78%) are the observed monthly
# anchors; the remaining months preserve the original seasonal shape and are
# scaled so that the day-weighted total equals 77.526 occupied days.
SEGOVIA_INE_MONTHLY: List[MonthlySeasonality] = [
    MonthlySeasonality(1, "Enero", 31, ine_rural_occupancy=0.0958, base_occupancy=0.150, adr_seasonal_factor=0.90),
    MonthlySeasonality(2, "Febrero", 28, ine_rural_occupancy=0.1173, base_occupancy=0.170, adr_seasonal_factor=0.90),
    MonthlySeasonality(3, "Marzo", 31, ine_rural_occupancy=0.1620, base_occupancy=0.240, adr_seasonal_factor=0.95),
    MonthlySeasonality(4, "Abril", 30, ine_rural_occupancy=0.2096, base_occupancy=0.310, adr_seasonal_factor=1.05),
    MonthlySeasonality(5, "Mayo", 31, ine_rural_occupancy=0.2217, base_occupancy=0.330, adr_seasonal_factor=1.00),
    MonthlySeasonality(6, "Junio", 30, ine_rural_occupancy=0.2516, base_occupancy=0.370, adr_seasonal_factor=1.05),
    MonthlySeasonality(7, "Julio", 31, ine_rural_occupancy=0.3326, base_occupancy=0.480, adr_seasonal_factor=1.15),
    MonthlySeasonality(8, "Agosto", 31, ine_rural_occupancy=0.3678, base_occupancy=0.540, adr_seasonal_factor=1.20),
    MonthlySeasonality(9, "Septiembre", 30, ine_rural_occupancy=0.2416, base_occupancy=0.360, adr_seasonal_factor=1.05),
    MonthlySeasonality(10, "Octubre", 31, ine_rural_occupancy=0.2025, base_occupancy=0.300, adr_seasonal_factor=1.00),
    MonthlySeasonality(11, "Noviembre", 30, ine_rural_occupancy=0.1492, base_occupancy=0.220, adr_seasonal_factor=0.95),
    MonthlySeasonality(12, "Diciembre", 31, ine_rural_occupancy=0.1877, base_occupancy=0.280, adr_seasonal_factor=1.10),
]


def get_annual_weighted_occupancy(series: List[MonthlySeasonality] = SEGOVIA_INE_MONTHLY) -> float:
    """Computes the day-weighted annual average of the management target occupancy."""
    total_occupied_days = sum(m.days_in_month * m.base_occupancy for m in series)
    total_days = sum(m.days_in_month for m in series)
    return total_occupied_days / total_days


def get_market_occupancy(series: List[MonthlySeasonality] = SEGOVIA_INE_MONTHLY) -> float:
    """Computes the day-weighted annual average of the official INE market series."""
    total_occupied_days = sum(m.days_in_month * m.ine_rural_occupancy for m in series)
    total_days = sum(m.days_in_month for m in series)
    return total_occupied_days / total_days


def get_excel_original_seasonality() -> Dict[str, float]:
    """
    Returns the original 3-tier structure from La_Dehesa_de_Castrillo_Proyecto.xlsx:
    - High season: 90 days @ 42%
    - Weekends: 80 days @ 32%
    - Midweek: 195 days @ 1.5%
    """
    days = {"high": 90, "weekend": 80, "midweek": 195}
    rates = {"high": 0.42, "weekend": 0.32, "midweek": 0.015}
    occupied_days = sum(days[k] * rates[k] for k in days)
    total_days = sum(days.values())
    return {
        "days": days,
        "rates": rates,
        "total_occupied_days": occupied_days,  # 66.325 days
        "weighted_occupancy": occupied_days / total_days,  # 18.17%
    }
