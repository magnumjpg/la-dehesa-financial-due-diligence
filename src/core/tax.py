"""
Tax and fiscal mechanics for La Dehesa del Castrillo S.L.

Models:
1. VAT (Impuesto sobre el Valor Anadido - Ley 37/1992):
   - 10% output VAT on accommodation and restaurant services (art. 91.Uno.2.2º).
   - 21% input VAT on CapEx and operating supplies (art. 90).
   - Quarterly Modelo 303 liquidation and tax credit refund mechanics (Modelo 390).
2. Corporate Income Tax (Impuesto sobre Sociedades - Ley 27/2014):
   - 25% general corporate tax rate.
   - Tax-deductible depreciation schedules (Tablas oficiales de amortizacion).
   - Tax loss carryforwards (Bases Imponibles Negativas - BINs, art. 26 LIS).
   - Deferred Tax Assets (Activos por impuesto diferido).
"""

from dataclasses import dataclass
from typing import Dict, List
import pandas as pd


@dataclass
class VATPeriod:
    period_id: str
    year: int
    quarter: int
    output_vat_lodging: float     # 10% on room & house revenue
    output_vat_restaurant: float  # 10% on restaurant revenue
    total_output_vat: float       # IVA Repercutido
    input_vat_capex: float        # 21% on CapEx
    input_vat_opex: float         # 21% on supplies, utilities, maintenance
    total_input_vat: float        # IVA Soportado
    net_vat_balance: float        # Output - Input
    accumulated_credit: float     # Saldo a compensar / a devolver (AEAT)
    refund_collected: float       # Cash refunded by tax agency


class VATEngine:
    """Manages quarterly/annual VAT settlements and fiscal cash flow timing."""

    def __init__(self, vat_hospitality_rate: float = 0.10, vat_general_rate: float = 0.21):
        self.vat_hospitality = vat_hospitality_rate
        self.vat_general = vat_general_rate

    def calculate_annual_vat_settlement(
        self,
        year: int,
        revenue_lodging: float,
        revenue_restaurant: float,
        capex_expenditure: float,
        taxable_opex: float,
        opening_vat_credit: float = 0.0,
        request_annual_refund: bool = True,
    ) -> Dict[str, float]:
        """
        Calculates annual consolidated VAT settlement.
        If request_annual_refund is True, any accumulated negative balance is requested
        for refund at year-end (paid by AEAT in subsequent period).
        """
        output_lodging = round(revenue_lodging * self.vat_hospitality, 2)
        output_restaurant = round(revenue_restaurant * self.vat_hospitality, 2)
        total_output = round(output_lodging + output_restaurant, 2)

        input_capex = round(capex_expenditure * self.vat_general, 2)
        input_opex = round(taxable_opex * self.vat_general, 2)
        total_input = round(input_capex + input_opex, 2)

        current_period_net = round(total_output - total_input, 2)

        # Apply previous credit if current net is positive (tax payable)
        # If current net is negative, credit increases
        effective_balance = round(current_period_net - opening_vat_credit, 2)

        if effective_balance > 0:
            vat_payable = effective_balance
            closing_credit = 0.0
            refund_due = 0.0
        else:
            vat_payable = 0.0
            if request_annual_refund:
                refund_due = abs(effective_balance)
                closing_credit = 0.0
            else:
                refund_due = 0.0
                closing_credit = abs(effective_balance)

        return {
            "year": year,
            "total_output_vat": total_output,
            "input_vat_capex": input_capex,
            "input_vat_opex": input_opex,
            "total_input_vat": total_input,
            "current_period_net": current_period_net,
            "vat_payable": vat_payable,
            "refund_due": refund_due,
            "closing_credit": closing_credit,
        }


class CorporateTaxEngine:
    """
    Computes Corporate Income Tax (Impuesto sobre Sociedades).
    Includes tracking of tax loss carryforwards (Bases Imponibles Negativas - BINs).
    """

    def __init__(self, cit_rate: float = 0.25):
        self.cit_rate = cit_rate
        self.accumulated_bins = 0.0

    def calculate_tax(self, year: int, ebt: float) -> Dict[str, float]:
        """
        Computes tax expense, applied BINs, and ending BIN balance.
        Under Spanish LIS, SMEs can compensate 100% of negative tax bases up to 1M€.
        """
        opening_bins = self.accumulated_bins

        if ebt <= 0:
            # Tax loss: increases BINs, zero tax payable
            applied_bins = 0.0
            taxable_base = 0.0
            tax_expense = 0.0
            closing_bins = round(opening_bins + abs(ebt), 2)
        else:
            # Positive profit: apply available BINs
            applied_bins = min(opening_bins, ebt)
            taxable_base = round(ebt - applied_bins, 2)
            tax_expense = round(taxable_base * self.cit_rate, 2)
            closing_bins = round(opening_bins - applied_bins, 2)

        self.accumulated_bins = closing_bins

        # Deferred tax asset recognized on balance sheet
        deferred_tax_asset = round(closing_bins * self.cit_rate, 2)

        return {
            "year": year,
            "ebt": round(ebt, 2),
            "opening_bins": opening_bins,
            "applied_bins": applied_bins,
            "taxable_base": taxable_base,
            "tax_expense": tax_expense,
            "closing_bins": closing_bins,
            "deferred_tax_asset": deferred_tax_asset,
        }
