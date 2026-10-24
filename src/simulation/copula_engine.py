"""
Multivariate Copula Simulation Engine for Tail Risk and Credit Underwriting.

Models joint asymmetric downside risk across four operational and financial
drivers of La Dehesa del Castrillo:

1. Occupancy (calibrated to the Segovia rural tourism series).
2. Average Daily Rate (pricing power).
3. Senior financing rate (Euribor 12M + spread).
4. Operating-cost inflation (payroll, utilities, supplies).

The dependency structure is compared across three copulas:

- Gaussian: benchmark with asymptotic tail independence (lambda_L = lambda_U = 0).
- Student-t (nu = 4): heavy, symmetric tail dependence.
- Clayton (theta = 1.8): asymmetric lower-tail clustering (lambda_L > 0).

Each draw is evaluated against the *actual* Phase I capital structure:

* Senior debt of EUR 367,535 at 4.0% over 20 years, with a 12-month
  interest-only construction/grace period. The amortising payment is therefore
  computed over the remaining 228 months, and Year 2 - the first amortising year
  and the binding covenant year - is the metric reported.
* The full USALI variable-cost stack: F&B COGS, 9% blended OTA commission,
  EUR 35 per occupied day of amenities, EUR 5 per guest-day of breakfast.
* The 3% FF&E reserve, which ranks ahead of debt service.
* Spanish corporate tax with the Year-1 tax loss carried forward (BINs).
* CFADS = EBITDA - FF&E reserve - cash tax, so the coverage ratio tests the
  cash that is actually available to the lender.

The output quantifies how a naive Gaussian model understates the probability and
depth of debt-service insolvency (DSCR < 1.00x) and covenant breach (DSCR <
1.25x), and sizes the Debt Service Reserve Account against the contractual
six-month standard and the Clayton CVaR 99% tail deficit.
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
    SCENARIOS,
)
from src.core.statements import FinancialModelEngine


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
    cvar_95: float      # Expected Shortfall below the 5th percentile
    cvar_99: float      # Expected Shortfall below the 1st percentile
    prob_covenant_breach: float  # P(DSCR < 1.25x)
    prob_cash_insolvency: float  # P(DSCR < 1.00x)
    tail_deficit_cvar99_eur: float  # Annual CFADS shortfall under CVaR 99%


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
    annual_debt_service_y2: float
    case: str = "management"

    def to_dataframe(self) -> pd.DataFrame:
        """Converts comparative risk metrics into an institutional summary table."""
        buckets = (
            ("Model Specification", lambda m: m.model_name),
            ("Tail Dep. (Lower / Upper)", None),
            ("Mean DSCR (Year 2)", lambda m: f"{m.mean_dscr:.2f}x"),
            ("Median DSCR (Year 2)", lambda m: f"{m.median_dscr:.2f}x"),
            ("VaR 95% (5th pct)", lambda m: f"{m.var_95:.2f}x"),
            ("VaR 99% (1st pct)", lambda m: f"{m.var_99:.2f}x"),
            ("CVaR 99% (Worst 1%)", lambda m: f"{m.cvar_99:.2f}x"),
            ("P(DSCR < 1.25x)", lambda m: f"{m.prob_covenant_breach:.2%}"),
            ("P(DSCR < 1.00x)", lambda m: f"{m.prob_cash_insolvency:.2%}"),
            ("CVaR 99% Deficit (EUR)", lambda m: f"{m.tail_deficit_cvar99_eur:,.0f}"),
        )
        data = []
        for metrics, tail in zip(
            (self.gaussian, self.student_t, self.clayton),
            (
                "0.00 / 0.00 (Independent)",
                "0.18 / 0.18 (Symmetric)",
                "0.68 / 0.00 (Asymmetric Lower)",
            ),
        ):
            row = {}
            for label, getter in buckets:
                row[label] = tail if getter is None else getter(metrics)
            data.append(row)
        return pd.DataFrame(data)


class CopulaSimulationEngine:
    """
    Vectorised Monte Carlo engine implementing multivariate copulas.

    The revenue, cost, FF&E and tax lines are scaled linearly from the
    deterministic Year-1 and Year-2 statements of ``FinancialModelEngine``, so
    every draw is consistent with the published model rather than a separate
    simplified P&L.
    """

    def __init__(
        self,
        n_simulations: int = 100_000,
        random_seed: int = 42,
        target_dscr: float = 1.25,
        nu_student_t: int = 4,
        theta_clayton: float = 1.8,
        case: str = "management",
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
        self.case = case

        # Reference deterministic projection. It supplies the base revenue,
        # cost, depreciation and debt parameters for the vectorised engine.
        self.engine = FinancialModelEngine(
            capex=capex,
            financing=financing,
            labor=labor,
            opex=opex,
            revenue_cfg=rev_cfg,
            scenario=SCENARIOS["base"],
            case=case,
        )
        self.financing = self.engine.financing
        self.capex = self.engine.capex
        self.rev_cfg = self.engine.rev_cfg

        # Capital structure: 20 years, 12-month interest-only period, 4.0%.
        self.P = float(self.financing.senior_debt_principal)
        self.tenure_months = int(self.financing.loan_tenure_years * 12)
        self.grace_months = int(self.financing.grace_months)
        self.base_rate = float(self.financing.loan_interest_rate)
        self.tax_rate = 0.25
        self.input_vat = float(self.capex.total_input_vat)
        self.bridge_rate = float(self.financing.credit_line_interest)

        # Deterministic base lines for Years 1 and 2.
        self._base = {
            year: self.engine.run_projection(projection_years=2)
            .set_index("year")
            .loc[year]
            for year in (1, 2)
        }
        self._y1 = self._base[1]
        self._y2 = self._base[2]

        # Contractual DSRA: six months of the maximum annual debt service.
        self.dsra_contractual = float(self.engine.dsra_amount)
        self.annual_debt_service_y2 = float(self._y2["debt_service"])
        self.ffe_rate = (
            float(self.rev_cfg.ffe_reserve_rate)
            if self.rev_cfg.apply_full_cost_stack
            else 0.0
        )

        # Calibrated correlation matrix across 4 risk drivers:
        # [Occupancy, ADR, Euribor_Delta, OPEX_Inflation]
        self.corr_matrix = np.array([
            [1.00, 0.65, -0.30, -0.20],
            [0.65, 1.00, -0.15, -0.10],
            [-0.30, -0.15, 1.00, 0.40],
            [-0.20, -0.10, 0.40, 1.00],
        ])

    # ------------------------------------------------------------------
    # Copula draws
    # ------------------------------------------------------------------
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
        Draws uniform marginals U in (0, 1)^4 via an Archimedean Clayton copula
        (theta = 1.8) using the Marshall-Olkin frailty algorithm:

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
        Inverts uniform marginals into calibrated financial distributions:

        1. Occupancy multiplier: Beta(4, 4) scaled to [0.65, 1.35].
        2. ADR multiplier: Log-Normal(0.0, 0.07).
        3. Rate delta: Normal(0.0, 0.0075), vectorised.
        4. OPEX multiplier: Log-Normal(0.0, 0.05).

        For Clayton, U near zero is systemic distress. Because higher rates and
        higher costs are the adverse direction, those two marginals are mapped
        through (1 - U).
        """
        u_occ = np.clip(U[:, 0], 1e-6, 1.0 - 1e-6)
        u_adr = np.clip(U[:, 1], 1e-6, 1.0 - 1e-6)
        occ_mult = 0.65 + 0.70 * stats.beta.ppf(u_occ, 4, 4)
        adr_mult = stats.lognorm.ppf(u_adr, s=0.07, scale=1.00)

        if is_clayton:
            u_rate = np.clip(1.0 - U[:, 2], 1e-6, 1.0 - 1e-6)
            u_opex = np.clip(1.0 - U[:, 3], 1e-6, 1.0 - 1e-6)
        else:
            u_rate = np.clip(U[:, 2], 1e-6, 1.0 - 1e-6)
            u_opex = np.clip(U[:, 3], 1e-6, 1.0 - 1e-6)

        rate_delta = stats.norm.ppf(u_rate, loc=0.0, scale=0.0075)
        opex_mult = stats.lognorm.ppf(u_opex, s=0.05, scale=1.00)

        return occ_mult, adr_mult, rate_delta, opex_mult

    # ------------------------------------------------------------------
    # Vectorised credit evaluation
    # ------------------------------------------------------------------
    @staticmethod
    def _annuity(principal: np.ndarray, r_m: np.ndarray, months: int) -> np.ndarray:
        """French-system constant payment over ``months`` periods."""
        return principal * (r_m * (1.0 + r_m) ** months) / (
            (1.0 + r_m) ** months - 1.0
        )

    def _debt_year_two(
        self, eff_rate: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns (Year-2 interest, Year-2 debt service, Year-1 interest) under the
        contractual 12-month grace. Year 2 is the first amortising year, so the
        payment is computed over the 228 months that remain after the grace.
        """
        r_m = eff_rate / 12.0

        if self.grace_months >= 12:
            interest_y1 = self.P * eff_rate
            amort_months = max(1, self.tenure_months - self.grace_months)
            pmt = self._annuity(self.P, r_m, amort_months)
            principal_y2 = (pmt / r_m - self.P) * ((1.0 + r_m) ** 12 - 1.0)
            interest_y2 = 12.0 * pmt - principal_y2
            return interest_y2, 12.0 * pmt, interest_y1

        # No grace: the loan amortises from Month 1.
        pmt = self._annuity(self.P, r_m, self.tenure_months)
        principal_y1 = (pmt / r_m - self.P) * ((1.0 + r_m) ** 12 - 1.0)
        interest_y1 = 12.0 * pmt - principal_y1
        balance_y1 = self.P - principal_y1
        principal_y2 = (pmt / r_m - balance_y1) * ((1.0 + r_m) ** 12 - 1.0)
        interest_y2 = 12.0 * pmt - principal_y2
        return interest_y2, 12.0 * pmt, interest_y1

    def _operating_lines(
        self, row: pd.Series, occ_mult: np.ndarray, adr_mult: np.ndarray,
        opex_mult: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        """
        Scales a deterministic annual statement by the shocks.

        Revenue and revenue-linked costs (F&B COGS, OTA commission) move with
        occupancy *and* ADR; per-occupied-day costs (amenities) move with
        occupancy only; per-guest-day breakfast moves with occupancy (guests are
        proportional to occupied days); payroll and fixed OPEX move with the
        cost-inflation multiplier.
        """
        revenue_scale = occ_mult * adr_mult
        out = {}
        out["revenue_rooms"] = float(row["revenue_rooms"]) * revenue_scale
        out["revenue_full_house"] = float(row["revenue_full_house"]) * revenue_scale
        out["revenue_restaurant"] = float(row["revenue_restaurant"]) * revenue_scale
        out["total_revenue"] = (
            out["revenue_rooms"] + out["revenue_full_house"] + out["revenue_restaurant"]
        )
        out["cogs_restaurant"] = float(row["cogs_restaurant"]) * revenue_scale
        out["ota_commission"] = float(row["ota_commission"]) * revenue_scale
        out["amenities"] = float(row["amenities"]) * occ_mult
        out["breakfast_cost"] = float(row["breakfast_cost"]) * occ_mult
        out["variable_costs"] = (
            out["cogs_restaurant"]
            + out["ota_commission"]
            + out["amenities"]
            + out["breakfast_cost"]
        )
        out["labor_expense"] = float(row["labor_expense"]) * opex_mult
        out["fixed_opex"] = float(row["fixed_opex"]) * opex_mult
        out["ebitda"] = (
            out["total_revenue"]
            - out["variable_costs"]
            - out["labor_expense"]
            - out["fixed_opex"]
        )
        out["ffe_reserve"] = out["total_revenue"] * self.ffe_rate
        return out

    def _evaluate_vectorized_dscr(
        self,
        occ_mult: np.ndarray,
        adr_mult: np.ndarray,
        rate_delta: np.ndarray,
        opex_mult: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Vectorised Year-2 credit test:

            1. Full USALI P&L (COGS, OTA, amenities, breakfast, payroll, OPEX).
            2. FF&E reserve deducted before debt service.
            3. Spanish tax with the Year-1 BIN carried forward.
            4. DSCR = (EBITDA - FF&E - tax) / Year-2 debt service.
        """
        eff_rate = np.maximum(0.01, self.base_rate + rate_delta)
        interest_y2, ds_y2, interest_y1 = self._debt_year_two(eff_rate)

        y1 = self._operating_lines(self._y1, occ_mult, adr_mult, opex_mult)
        y2 = self._operating_lines(self._y2, occ_mult, adr_mult, opex_mult)

        depreciation_y1 = float(self._y1["depreciation"])
        depreciation_y2 = float(self._y2["depreciation"])
        bridge_interest_y1 = self.input_vat * self.bridge_rate
        bridge_interest_y2 = bridge_interest_y1 * 0.5

        # Year-1 taxable loss (BIN) available to shield Year-2 profit.
        ebt_y1 = y1["ebitda"] - depreciation_y1 - interest_y1 - bridge_interest_y1
        bines_opening = np.maximum(0.0, -ebt_y1)

        ebt_y2 = y2["ebitda"] - depreciation_y2 - interest_y2 - bridge_interest_y2
        taxable_base = np.maximum(0.0, ebt_y2 - bines_opening)
        tax_y2 = taxable_base * self.tax_rate

        cfads = y2["ebitda"] - y2["ffe_reserve"] - tax_y2
        dscr = cfads / ds_y2

        return dscr, cfads, ds_y2

    def _compute_metrics(
        self,
        model_name: str,
        dscr: np.ndarray,
        cfads: np.ndarray,
        debt_service: np.ndarray,
    ) -> CopulaRiskMetrics:
        """Calculates VaR, CVaR, breach and default probabilities."""
        var_95 = float(np.percentile(dscr, 5.0))
        var_99 = float(np.percentile(dscr, 1.0))
        cvar_95 = float(np.mean(dscr[dscr <= var_95]))
        cvar_99 = float(np.mean(dscr[dscr <= var_99]))

        prob_breach = float(np.mean(dscr < self.target_dscr))
        prob_default = float(np.mean(dscr < 1.00))

        # Annual cash shortfall in the worst 1% tail.
        tail_idx = dscr <= var_99
        tail_shortfalls = np.maximum(0.0, debt_service[tail_idx] - cfads[tail_idx])
        tail_deficit_cvar99 = float(np.mean(tail_shortfalls))

        return CopulaRiskMetrics(
            model_name=model_name,
            n_simulations=self.n_simulations,
            mean_dscr=round(float(np.mean(dscr)), 3),
            median_dscr=round(float(np.median(dscr)), 3),
            std_dscr=round(float(np.std(dscr)), 3),
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
        Executes the comparative evaluation across the Gaussian, Student-t
        (nu = 4) and Clayton (theta = 1.8) copulas.
        """
        rng = np.random.default_rng(self.random_seed)

        u_gauss = self._generate_gaussian_copula(rng)
        occ_g, adr_g, rate_g, op_g = self._map_to_economic_marginals(u_gauss)
        dscr_g, cfads_g, ds_g = self._evaluate_vectorized_dscr(
            occ_g, adr_g, rate_g, op_g
        )
        metrics_gauss = self._compute_metrics(
            "Gaussian Copula (Benchmark)", dscr_g, cfads_g, ds_g
        )

        u_t = self._generate_student_t_copula(rng)
        occ_t, adr_t, rate_t, op_t = self._map_to_economic_marginals(u_t)
        dscr_t, cfads_t, ds_t = self._evaluate_vectorized_dscr(
            occ_t, adr_t, rate_t, op_t
        )
        metrics_t = self._compute_metrics(
            "Student-t Copula (nu=4)", dscr_t, cfads_t, ds_t
        )

        u_c = self._generate_clayton_copula(rng)
        occ_c, adr_c, rate_c, op_c = self._map_to_economic_marginals(
            u_c, is_clayton=True
        )
        dscr_c, cfads_c, ds_c = self._evaluate_vectorized_dscr(
            occ_c, adr_c, rate_c, op_c
        )
        metrics_clayton = self._compute_metrics(
            "Clayton Copula (theta=1.8)", dscr_c, cfads_c, ds_c
        )

        # Contractual DSRA: six months of the base-rate annual debt service.
        # The reserve is a closing-day covenant, so it is sized on the 4.0%
        # schedule rather than on the mean of the rate-shocked distribution.
        base_annual_ds = self.annual_debt_service_y2
        dsra_6m = round(self.dsra_contractual, 2)
        dsra_12m = round(base_annual_ds, 2)

        # Recommended DSRA covers the contractual six-month standard and, if the
        # Clayton tail is deeper, the full annual CFADS shortfall in the worst 1%.
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
            annual_debt_service_y2=round(base_annual_ds, 2),
            case=self.case,
        )
