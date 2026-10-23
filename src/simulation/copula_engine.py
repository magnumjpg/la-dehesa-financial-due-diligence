"""
Multivariate Copula Simulation Engine for Tail Risk and Credit Underwriting.

Models joint asymmetric downside risk across macroeconomic and operational drivers:
1. Occupancy rate (calibrated to Segovia rural tourism historical series).
2. Average Daily Rate (ADR rack rate pricing power).
3. Benchmark financing rate (Euribor 12M + Spread).
4. Operating expenses inflation (labor and utilities cost pressure).

Compares three joint dependency structures:
- Gaussian Copula: Benchmark with asymptotic tail independence (lambda_L = lambda_U = 0).
- Student-t Copula (nu=4): Heavy symmetric tail dependence.
- Clayton Copula (theta=1.8): Asymmetric lower-tail Archimedean clustering (lambda_L > 0, lambda_U = 0).

Quantifies how naive Gaussian models underestimate the probability and depth
of debt service insolvency (DSCR < 1.00x and DSCR < 1.25x), providing
rigorous sizing for the Debt Service Reserve Account (DSRA).
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats

from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    LaborStructure,
    FixedOpexStructure,
    RevenueModelConfig,
)
from src.config.ine_weights import SEGOVIA_INE_MONTHLY, get_annual_weighted_occupancy


@dataclass(frozen=True)
class CopulaRiskMetrics:
    """Quantitative risk metrics for a single copula specification."""
    model_name: str
    n_simulations: int
    mean_dscr: float
    median_dscr: float
    std_dscr: float
    var_95: float       # 5th percentile DSCR
    var_99: float       # 1st percentile DSCR
    cvar_95: float      # Expected Shortfall below 5th percentile
    cvar_99: float      # Expected Shortfall below 1st percentile
    prob_covenant_breach: float  # P(DSCR < 1.25x)
    prob_cash_insolvency: float  # P(DSCR < 1.00x)
    tail_deficit_cvar99_eur: float  # Annual cash shortfall under CVaR 99%


@dataclass(frozen=True)
class ComparativeCopulaResults:
    """Structured output comparing Gaussian, Student-t, and Clayton copulas."""
    gaussian: CopulaRiskMetrics
    student_t: CopulaRiskMetrics
    clayton: CopulaRiskMetrics
    correlation_matrix: np.ndarray
    dscr_gaussian: np.ndarray
    dscr_student_t: np.ndarray
    dscr_clayton: np.ndarray
    occ_gaussian: np.ndarray
    occ_clayton: np.ndarray
    dsra_standard_6m: float
    dsra_standard_12m: float
    dsra_recommended_tail: float

    def to_dataframe(self) -> pd.DataFrame:
        """Converts comparative risk metrics into an institutional summary table."""
        data = [
            {
                "Model Specification": self.gaussian.model_name,
                "Tail Dep. (Lower / Upper)": "0.00 / 0.00 (Independent)",
                "Mean DSCR": f"{self.gaussian.mean_dscr:.2f}x",
                "Median DSCR": f"{self.gaussian.median_dscr:.2f}x",
                "VaR 95% (5th pct)": f"{self.gaussian.var_95:.2f}x",
                "VaR 99% (1st pct)": f"{self.gaussian.var_99:.2f}x",
                "CVaR 99% (Worst 1%)": f"{self.gaussian.cvar_99:.2f}x",
                "P(DSCR < 1.25x)": f"{self.gaussian.prob_covenant_breach:.2%}",
                "P(DSCR < 1.00x)": f"{self.gaussian.prob_cash_insolvency:.2%}",
                "CVaR 99% Deficit (€)": f"{self.gaussian.tail_deficit_cvar99_eur:,.0f} €",
            },
            {
                "Model Specification": self.student_t.model_name,
                "Tail Dep. (Lower / Upper)": "0.18 / 0.18 (Symmetric)",
                "Mean DSCR": f"{self.student_t.mean_dscr:.2f}x",
                "Median DSCR": f"{self.student_t.median_dscr:.2f}x",
                "VaR 95% (5th pct)": f"{self.student_t.var_95:.2f}x",
                "VaR 99% (1st pct)": f"{self.student_t.var_99:.2f}x",
                "CVaR 99% (Worst 1%)": f"{self.student_t.cvar_99:.2f}x",
                "P(DSCR < 1.25x)": f"{self.student_t.prob_covenant_breach:.2%}",
                "P(DSCR < 1.00x)": f"{self.student_t.prob_cash_insolvency:.2%}",
                "CVaR 99% Deficit (€)": f"{self.student_t.tail_deficit_cvar99_eur:,.0f} €",
            },
            {
                "Model Specification": self.clayton.model_name,
                "Tail Dep. (Lower / Upper)": "0.68 / 0.00 (Asymmetric Lower)",
                "Mean DSCR": f"{self.clayton.mean_dscr:.2f}x",
                "Median DSCR": f"{self.clayton.median_dscr:.2f}x",
                "VaR 95% (5th pct)": f"{self.clayton.var_95:.2f}x",
                "VaR 99% (1st pct)": f"{self.clayton.var_99:.2f}x",
                "CVaR 99% (Worst 1%)": f"{self.clayton.cvar_99:.2f}x",
                "P(DSCR < 1.25x)": f"{self.clayton.prob_covenant_breach:.2%}",
                "P(DSCR < 1.00x)": f"{self.clayton.prob_cash_insolvency:.2%}",
                "CVaR 99% Deficit (€)": f"{self.clayton.tail_deficit_cvar99_eur:,.0f} €",
            },
        ]
        return pd.DataFrame(data)


class CopulaSimulationEngine:
    """
    High-performance vectorized Monte Carlo engine implementing multivariate copulas.
    Simulates 50,000 to 100,000 iterations in sub-second execution time.
    """

    def __init__(
        self,
        n_simulations: int = 100_000,
        random_seed: int = 42,
        target_dscr: float = 1.25,
        nu_student_t: int = 4,
        theta_clayton: float = 1.8,
        capex: Optional[CapExStructure] = None,
        financing: Optional[FinancingStructure] = None,
        labor: Optional[LaborStructure] = None,
        opex: Optional[FixedOpexStructure] = None,
        rev_cfg: Optional[RevenueModelConfig] = None,
    ):
        self.n_simulations = n_simulations
        self.random_seed = random_seed
        self.target_dscr = target_dscr
        self.nu = nu_student_t
        self.theta = theta_clayton

        self.capex = capex or CapExStructure()
        self.financing = financing or FinancingStructure()
        self.labor = labor or LaborStructure()
        self.opex = opex or FixedOpexStructure()
        self.rev_cfg = rev_cfg or RevenueModelConfig()

        # Calibration parameters
        self.P = self.financing.senior_debt_principal  # 507,500.0 €
        self.n_months = self.financing.loan_tenure_years * 12  # 180 months
        self.base_rate = self.financing.loan_interest_rate  # 0.035 (3.50%)
        self.depreciation = self.capex.annual_depreciation  # 17,950.0 €
        self.tax_rate = 0.25

        # Empirical base revenue and cost parameters for Year 1 ramp-up
        base_occ_rate = get_annual_weighted_occupancy(SEGOVIA_INE_MONTHLY) * 0.90
        days_occ_base = 365.0 * base_occ_rate

        self.room_rev_base = days_occ_base * self.rev_cfg.double_rooms_count * self.rev_cfg.double_room_adr
        self.house_rev_base = days_occ_base * self.rev_cfg.full_house_count * self.rev_cfg.full_house_adr
        diners_base = days_occ_base * (
            self.rev_cfg.double_rooms_count * self.rev_cfg.restaurant_diners_per_double_room
            + self.rev_cfg.full_house_count * self.rev_cfg.restaurant_diners_per_full_house
        )
        self.rest_rev_base = diners_base * self.rev_cfg.restaurant_average_ticket
        self.cogs_ratio = self.rev_cfg.restaurant_cogs_ratio

        self.payroll_base = self.labor.total_annual_payroll
        self.fixed_opex_base = self.opex.total_fixed_opex

        # Calibrated correlation matrix across 4 risk drivers:
        # [Occupancy, ADR, Euribor_Delta, OPEX_Inflation]
        self.corr_matrix = np.array([
            [ 1.00,  0.65, -0.30, -0.20],
            [ 0.65,  1.00, -0.15, -0.10],
            [-0.30, -0.15,  1.00,  0.40],
            [-0.20, -0.10,  0.40,  1.00],
        ])

    def _generate_gaussian_copula(self, rng: np.random.Generator) -> np.ndarray:
        """Draws uniform marginals U in (0, 1)^4 via Gaussian copula."""
        L = np.linalg.cholesky(self.corr_matrix)
        Z = rng.standard_normal((self.n_simulations, 4)) @ L.T
        return stats.norm.cdf(Z)

    def _generate_student_t_copula(self, rng: np.random.Generator) -> np.ndarray:
        """Draws uniform marginals U in (0, 1)^4 via Student-t copula (nu=4)."""
        L = np.linalg.cholesky(self.corr_matrix)
        Z = rng.standard_normal((self.n_simulations, 4)) @ L.T
        chi2_draws = rng.chisquare(df=self.nu, size=(self.n_simulations, 1))
        W = np.sqrt(self.nu / chi2_draws)
        T = Z * W
        return stats.t.cdf(T, df=self.nu)

    def _generate_clayton_copula(self, rng: np.random.Generator) -> np.ndarray:
        """
        Draws uniform marginals U in (0, 1)^4 via Archimedean Clayton copula (theta=1.8).
        Uses Marshall-Olkin frailty algorithm with Gamma generator:
        M ~ Gamma(1/theta, 1), E_j ~ Exp(1) i.i.d.
        U_j = (1 + E_j / M)^(-1/theta)
        """
        M = rng.gamma(shape=1.0 / self.theta, scale=1.0, size=(self.n_simulations, 1))
        E = rng.exponential(scale=1.0, size=(self.n_simulations, 4))
        return (1.0 + E / M) ** (-1.0 / self.theta)

    def _map_to_economic_marginals(
        self, U: np.ndarray, is_clayton: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Inverts uniform marginals U into calibrated financial distributions:
        1. Occupancy Multiplier: Beta(4, 4) scaled between [0.65, 1.35].
        2. ADR Multiplier: Log-Normal(0.0, 0.07).
        3. Euribor Delta: Truncated Normal(0.0, 0.0075).
        4. OPEX Multiplier: Log-Normal(0.0, 0.05).
        
        For Clayton, the lower tail (U near 0) represents systemic economic distress.
        Adverse shocks for interest rates and OPEX inflation correspond to the upper tail
        of their raw values, mapped via (1 - U).
        """
        # 1. Occupancy multiplier
        occ_mult = 0.65 + 0.70 * stats.beta.ppf(np.clip(U[:, 0], 1e-6, 1.0 - 1e-6), 4, 4)

        # 2. ADR multiplier
        adr_mult = stats.lognorm.ppf(np.clip(U[:, 1], 1e-6, 1.0 - 1e-6), s=0.07, scale=1.00)

        # 3. Benchmark interest rate delta & 4. OPEX inflation
        if is_clayton:
            u_rate = np.clip(1.0 - U[:, 2], 1e-6, 1.0 - 1e-6)
            u_opex = np.clip(1.0 - U[:, 3], 1e-6, 1.0 - 1e-6)
        else:
            u_rate = np.clip(U[:, 2], 1e-6, 1.0 - 1e-6)
            u_opex = np.clip(U[:, 3], 1e-6, 1.0 - 1e-6)

        rate_delta = stats.norm.ppf(u_rate, loc=0.0, scale=0.0075)
        opex_mult = stats.lognorm.ppf(u_opex, s=0.05, scale=1.00)

        return occ_mult, adr_mult, rate_delta, opex_mult

    def _evaluate_vectorized_dscr(
        self,
        occ_mult: np.ndarray,
        adr_mult: np.ndarray,
        rate_delta: np.ndarray,
        opex_mult: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Pure NumPy vectorized evaluation of Year 1 3-statement cash flows:
        - Revenue, COGS, Payroll, Fixed OPEX -> EBITDA
        - French monthly amortization schedule -> Debt Service & Interest
        - Corporate Income Tax -> CFADS
        - DSCR = CFADS / Debt Service
        """
        # Operational revenues
        rev_rooms = self.room_rev_base * occ_mult * adr_mult
        rev_house = self.house_rev_base * occ_mult * adr_mult
        rev_rest = self.rest_rev_base * occ_mult * adr_mult
        total_rev = rev_rooms + rev_house + rev_rest
        cogs = rev_rest * self.cogs_ratio
        gross_margin = total_rev - cogs

        # Operational costs
        payroll = self.payroll_base * opex_mult
        fixed_op = self.fixed_opex_base * opex_mult
        ebitda = gross_margin - payroll - fixed_op

        # Senior debt service (French monthly amortization)
        eff_rate = np.maximum(0.01, self.base_rate + rate_delta)
        r_m = eff_rate / 12.0
        pmt = self.P * (r_m * (1.0 + r_m) ** self.n_months) / ((1.0 + r_m) ** self.n_months - 1.0)
        debt_service = pmt * 12.0

        # Exact Year 1 interest expense under French schedule
        principal_y1 = (pmt / r_m - self.P) * ((1.0 + r_m) ** 12 - 1.0)
        interest_y1 = debt_service - principal_y1

        # Corporate Income Tax (25%) with tax shield from depreciation and interest
        ebt = ebitda - self.depreciation - interest_y1
        taxes = np.maximum(0.0, ebt) * self.tax_rate

        # Cash Flow Available for Debt Service (CFADS)
        cfads = ebitda - taxes
        dscr = cfads / debt_service

        return dscr, cfads, debt_service

    def _compute_metrics(
        self,
        model_name: str,
        dscr: np.ndarray,
        cfads: np.ndarray,
        debt_service: np.ndarray,
    ) -> CopulaRiskMetrics:
        """Calculates institutional risk metrics: VaR, CVaR, breach and default probabilities."""
        mean_dscr = float(np.mean(dscr))
        median_dscr = float(np.median(dscr))
        std_dscr = float(np.std(dscr))

        var_95 = float(np.percentile(dscr, 5.0))
        var_99 = float(np.percentile(dscr, 1.0))

        cvar_95 = float(np.mean(dscr[dscr <= var_95]))
        cvar_99 = float(np.mean(dscr[dscr <= var_99]))

        prob_breach = float(np.mean(dscr < self.target_dscr))
        prob_default = float(np.mean(dscr < 1.00))

        # Expected shortfall in euros under the worst 1% tail:
        # Deficit = Debt Service - CFADS for all observations in the 1% tail
        tail_idx = dscr <= var_99
        tail_shortfalls = np.maximum(0.0, debt_service[tail_idx] - cfads[tail_idx])
        tail_deficit_cvar99 = float(np.mean(tail_shortfalls))

        return CopulaRiskMetrics(
            model_name=model_name,
            n_simulations=self.n_simulations,
            mean_dscr=round(mean_dscr, 3),
            median_dscr=round(median_dscr, 3),
            std_dscr=round(std_dscr, 3),
            var_95=round(var_95, 3),
            var_99=round(var_99, 3),
            cvar_95=round(cvar_95, 3),
            cvar_99=round(cvar_99, 3),
            prob_covenant_breach=round(prob_breach, 4),
            prob_cash_insolvency=round(prob_default, 4),
            tail_deficit_cvar99_eur=round(tail_deficit_cvar99, 2),
        )

    def run_comparative_analysis(self) -> ComparativeCopulaResults:
        """
        Executes full comparative quantitative evaluation across
        Gaussian, Student-t (nu=4), and Clayton (theta=1.8) copulas.
        """
        rng = np.random.default_rng(self.random_seed)

        # 1. Gaussian Copula
        u_gauss = self._generate_gaussian_copula(rng)
        occ_g, adr_g, rate_g, op_g = self._map_to_economic_marginals(u_gauss, is_clayton=False)
        dscr_g, cfads_g, ds_g = self._evaluate_vectorized_dscr(occ_g, adr_g, rate_g, op_g)
        metrics_gauss = self._compute_metrics("Gaussian Copula (Benchmark)", dscr_g, cfads_g, ds_g)

        # 2. Student-t Copula (nu=4)
        u_t = self._generate_student_t_copula(rng)
        occ_t, adr_t, rate_t, op_t = self._map_to_economic_marginals(u_t, is_clayton=False)
        dscr_t, cfads_t, ds_t = self._evaluate_vectorized_dscr(occ_t, adr_t, rate_t, op_t)
        metrics_t = self._compute_metrics("Student-t Copula (nu=4)", dscr_t, cfads_t, ds_t)

        # 3. Clayton Copula (theta=1.8)
        u_c = self._generate_clayton_copula(rng)
        occ_c, adr_c, rate_c, op_c = self._map_to_economic_marginals(u_c, is_clayton=True)
        dscr_c, cfads_c, ds_c = self._evaluate_vectorized_dscr(occ_c, adr_c, rate_c, op_c)
        metrics_clayton = self._compute_metrics("Clayton Copula (theta=1.8)", dscr_c, cfads_c, ds_c)

        # Base debt service sizing for Year 1
        base_annual_ds = float(np.mean(ds_g))
        dsra_6m = round(base_annual_ds / 2.0, 2)
        dsra_12m = round(base_annual_ds, 2)

        # Recommended DSRA: sized to cover the 99% CVaR tail deficit under Clayton
        dsra_recommended = round(max(dsra_6m, metrics_clayton.tail_deficit_cvar99_eur), 2)

        return ComparativeCopulaResults(
            gaussian=metrics_gauss,
            student_t=metrics_t,
            clayton=metrics_clayton,
            correlation_matrix=self.corr_matrix,
            dscr_gaussian=dscr_g,
            dscr_student_t=dscr_t,
            dscr_clayton=dscr_c,
            occ_gaussian=occ_g,
            occ_clayton=occ_c,
            dsra_standard_6m=dsra_6m,
            dsra_standard_12m=dsra_12m,
            dsra_recommended_tail=dsra_recommended,
        )
