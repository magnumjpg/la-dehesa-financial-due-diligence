"""
Empirical monthly seasonality and occupancy weights calibrated with INE data.

Source: Instituto Nacional de Estadistica (INE) - Encuesta de Ocupacion en Alojamientos
de Turismo Rural (EOTR) para la Provincia de Segovia.

Provides:
1. Historical monthly occupancy benchmarks for Segovia rural lodging.
2. Weekend vs. weekday structural asymmetry factors.
3. Monthly ADR index adjustments.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class MonthlySeasonality:
    month_index: int
    month_name: str
    days_in_month: int
    # Official INE Segovia rural lodging benchmark occupancy
    ine_rural_occupancy: float
    # Project target occupancy baseline (calibrated for high-end boutique asset)
    base_occupancy: float
    # ADR seasonal premium multiplier (1.0 = baseline ADR)
    adr_seasonal_factor: float


# Calibration based on INE EOTR series for Segovia:
# Winter trough (Jan-Feb), Spring lift (Mar-Apr-May), Summer peak (Jul-Aug),
# Autumn trekking/harvest season (Sep-Oct), and Holiday bridges (Nov-Dec).
SEGOVIA_INE_MONTHLY: List[MonthlySeasonality] = [
    MonthlySeasonality(1, "Enero", 31, ine_rural_occupancy=0.142, base_occupancy=0.150, adr_seasonal_factor=0.90),
    MonthlySeasonality(2, "Febrero", 28, ine_rural_occupancy=0.165, base_occupancy=0.170, adr_seasonal_factor=0.90),
    MonthlySeasonality(3, "Marzo", 31, ine_rural_occupancy=0.228, base_occupancy=0.240, adr_seasonal_factor=0.95),
    MonthlySeasonality(4, "Abril", 30, ine_rural_occupancy=0.295, base_occupancy=0.310, adr_seasonal_factor=1.05),
    MonthlySeasonality(5, "Mayo", 31, ine_rural_occupancy=0.312, base_occupancy=0.330, adr_seasonal_factor=1.00),
    MonthlySeasonality(6, "Junio", 30, ine_rural_occupancy=0.354, base_occupancy=0.370, adr_seasonal_factor=1.05),
    MonthlySeasonality(7, "Julio", 31, ine_rural_occupancy=0.468, base_occupancy=0.480, adr_seasonal_factor=1.15),
    MonthlySeasonality(8, "Agosto", 31, ine_rural_occupancy=0.521, base_occupancy=0.540, adr_seasonal_factor=1.20),
    MonthlySeasonality(9, "Septiembre", 30, ine_rural_occupancy=0.340, base_occupancy=0.360, adr_seasonal_factor=1.05),
    MonthlySeasonality(10, "Octubre", 31, ine_rural_occupancy=0.285, base_occupancy=0.300, adr_seasonal_factor=1.00),
    MonthlySeasonality(11, "Noviembre", 30, ine_rural_occupancy=0.210, base_occupancy=0.220, adr_seasonal_factor=0.95),
    MonthlySeasonality(12, "Diciembre", 31, ine_rural_occupancy=0.264, base_occupancy=0.280, adr_seasonal_factor=1.10),
]


def get_annual_weighted_occupancy(series: List[MonthlySeasonality] = SEGOVIA_INE_MONTHLY) -> float:
    """Computes day-weighted annual average occupancy."""
    total_occupied_days = sum(m.days_in_month * m.base_occupancy for m in series)
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
