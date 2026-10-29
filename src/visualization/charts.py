"""
Institutional charting and visualization engine for investment memoranda.

UNIFIED INSTITUTIONAL PALETTE:
- Primary Brand / Solvency: Deep Navy (#1E3A8A)
- Secondary Accent: Royal Blue (#2563EB)
- Positive / Inflows / Median: Muted Pine Teal (#0D9488)
- Negative / Outflows / Breach: Muted Rose Crimson (#BE123C)
- Warning / VaR 95%: Warm Amber (#D97706)
- Neutral Benchmark: Slate Gray (#94A3B8)
- Structural Grid & Card: Slate 200/50 (#E2E8F0 / #F8FAFC)

Generates:
1. figure_1_seasonality_ine.png: Empirical INE Segovia rural tourism curve vs. project baseline.
2. figure_2_dscr_sensitivity_heatmap.png: 2D stress matrix of Year-2 DSCR vs. interest rates and occupancy.
3. figure_3_monte_carlo_distribution.png: Monte Carlo probability density of the minimum DSCR and VaR 95%.
4. figure_4_cash_flow_waterfall.png: Cash sources & uses at close, which only balance with a
   €521k cash-equity plug (49.6% of CapEx) - the net position is exactly zero.
5. figure_5_copula_tail_risk.png: Gaussian vs. Clayton tail dependence on the Year-2 DSCR.
6. figure_6_monthly_cash_runway.png: 24-month cash runway, revolver draw and solvency bridge.
7. figure_7_reform_value_bridge.png: R2 mature-EBITDA value bridge and the CapEx x
   external-cover value frontier for the separate reform / resize case.
8. figure_8_occupancy_bridge.png: management vs INE occupancy by segment and the
   decomposition of the 10.1 pp gap.
9. figure_9_five_act_timeline.png: the five-act narrative arc, from the promoter's
   pitch to the cabin turnaround, with the verdict at each act.
10. figure_10_three_case_comparison.png: promoter vs audited vs T8 on capital,
    cash equity, minimum DSCR and equity IRR.
11. figure_11_t8_dscr_cash.png: T8 DSCR against the 1.25x covenant and the cash
    build over the five-year horizon.
12. figure_12_t8_irr_tornado.png: equity IRR sensitivity to exit cap, ADR,
    occupancy, leverage and scope (lodge included or not).
"""

from pathlib import Path
from typing import Optional
import sys
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import seaborn as sns
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.ine_weights import SEGOVIA_INE_MONTHLY
from src.scenarios.scenario_analysis import ScenarioEngine
from src.simulation.monte_carlo import MonteCarloSimulator


# SINGLE UNIFIED INSTITUTIONAL PALETTE
PALETTE = {
    "navy_primary": "#1E3A8A",      # Deep Navy (main brand, mature target, net solvency)
    "navy_light": "#2563EB",        # Royal Blue fill / highlights
    "teal_positive": "#0D9488",     # Muted Pine Teal (inflows, positive margins, median)
    "rose_negative": "#BE123C",     # Muted Rose Crimson (outflows, OPEX, covenant breach)
    "amber_warning": "#D97706",     # Warm Amber (covenant floor, VaR 95% threshold)
    "slate_benchmark": "#94A3B8",   # Neutral Slate (INE regional benchmark, secondary bars)
    "slate_dark": "#334155",        # Slate 700 (typography, insolvency baseline)
    "slate_grid": "#E2E8F0",        # Slate 200 (subtle gridlines)
    "slate_border": "#CBD5E1",      # Slate 300 (structural borders)
    "background_card": "#FFFFFF",   # Clean white plot canvas
}


def get_assets_dir() -> Path:
    assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def set_institutional_style():
    """Sets a unified, publication-grade financial research aesthetic."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams.update(
        {
            "figure.titlesize": 13,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8.5,
            "figure.autolayout": True,
            "font.family": "DejaVu Sans",
            "axes.edgecolor": PALETTE["slate_border"],
            "axes.linewidth": 0.8,
            "grid.color": PALETTE["slate_grid"],
            "grid.linestyle": "--",
            "grid.alpha": 0.75,
            "figure.facecolor": "#FFFFFF",
            "axes.facecolor": "#FFFFFF",
        }
    )


def generate_seasonality_chart(save_path: Optional[Path] = None) -> Path:
    """Figure 1: Empirical monthly seasonality curve (INE Segovia vs. asset baseline)."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_1_seasonality_ine.png")

    months = [m.month_name[:3] for m in SEGOVIA_INE_MONTHLY]
    ine_rates = [m.ine_rural_occupancy * 100 for m in SEGOVIA_INE_MONTHLY]
    base_rates = [m.base_occupancy * 100 for m in SEGOVIA_INE_MONTHLY]

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)

    x = np.arange(len(months))
    width = 0.36

    rects1 = ax.bar(x - width / 2, ine_rates, width, label="INE Segovia Rural Tourism Benchmark", color=PALETTE["slate_benchmark"])
    rects2 = ax.bar(x + width / 2, base_rates, width, label="La Dehesa Mature Target (31.36%, Year 2+)", color=PALETTE["navy_primary"])

    ax.set_ylabel("Occupancy Rate (%)", color=PALETTE["slate_dark"])
    ax.set_title("Figure 1: Empirical Monthly Seasonality Curve (INE Segovia vs. Asset Baseline)", pad=14, fontweight="bold", color=PALETTE["slate_dark"])
    ax.set_xticks(x)
    ax.set_xticklabels(months, color=PALETTE["slate_dark"])
    ax.set_ylim(0, 65)
    ax.legend(frameon=True, facecolor=PALETTE["background_card"], edgecolor=PALETTE["slate_border"])

    ax.annotate(
        "Year 1 runs at 0.90x this curve\n(28.2% weighted average)",
        xy=(0.5, 60.5),
        ha="left",
        fontsize=8.5,
        color=PALETTE["slate_dark"],
    )

    ax.annotate(
        "Summer Leisure Peak\n(Jul-Aug: ~48-54%)",
        xy=(7, 54),
        xytext=(6.5, 59),
        arrowprops=dict(facecolor=PALETTE["navy_primary"], shrink=0.05, width=1, headwidth=5),
        ha="center",
        fontsize=8.5,
        fontweight="bold",
        color=PALETTE["navy_primary"],
    )

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_dscr_sensitivity_heatmap(save_path: Optional[Path] = None) -> Path:
    """Figure 2: 2D Underwriting Sensitivity Matrix of DSCR under interest rate and demand stress."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_2_dscr_sensitivity_heatmap.png")

    engine = ScenarioEngine(target_dscr=1.25)
    df_matrix = engine.generate_sensitivity_matrix_dscr()

    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=300)

    # Unified corporate colormap: Rose (breach) -> Slate light (transition) -> Teal (compliant)
    custom_cmap = LinearSegmentedColormap.from_list(
        "unified_corporate_dscr",
        [PALETTE["rose_negative"], "#F8FAFC", PALETTE["teal_positive"]],
        N=256,
    )

    sns.heatmap(
        df_matrix,
        annot=True,
        fmt=".2f",
        cmap=custom_cmap,
        center=1.25,
        cbar_kws={"label": "Debt Service Coverage Ratio (DSCR)"},
        linewidths=0.6,
        linecolor=PALETTE["slate_border"],
        annot_kws={"size": 9, "fontweight": "bold"},
        ax=ax,
    )

    ax.set_title("Figure 2: Year-2 DSCR Sensitivity Matrix (First Amortising Year, 12-Month Grace)", pad=30, fontweight="bold", color=PALETTE["slate_dark"])
    ax.set_xlabel("Senior Mortgage Interest Rate (Fixed, 20-Year Tenure)", color=PALETTE["slate_dark"])
    ax.set_ylabel("Occupancy Demand Multiplier (vs. 31.36% Mature)", color=PALETTE["slate_dark"])

    # Box the base case so the 1.15x underwriting point is unmistakable.
    row_idx = list(df_matrix.index).index("100% Occ Factor")
    col_idx = list(df_matrix.columns).index("4.0% Rate")
    ax.add_patch(
        Rectangle(
            (col_idx, row_idx), 1, 1,
            fill=False, edgecolor=PALETTE["navy_primary"], linewidth=2.8,
        )
    )
    base_dscr = float(df_matrix.loc["100% Occ Factor", "4.0% Rate"])
    ax.text(
        0.5, 1.012,
        f"Boxed cell = base case (100% demand, 4.0% rate): {base_dscr:.2f}x, below the 1.25x covenant",
        transform=ax.transAxes, ha="center", va="bottom",
        fontsize=8.5, fontweight="bold", color=PALETTE["rose_negative"],
    )

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_monte_carlo_distribution(save_path: Optional[Path] = None) -> Path:
    """Figure 3: Monte Carlo probability density of the minimum DSCR across 1,000 iterations."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_3_monte_carlo_distribution.png")

    sim = MonteCarloSimulator(iterations=1000, random_seed=42)
    df_sim, summary = sim.run_simulation()

    fig, ax = plt.subplots(figsize=(10, 5.0), dpi=300)

    # Histogram and KDE strictly styled with unified palette
    sns.histplot(
        df_sim["min_dscr"],
        kde=True,
        color=PALETTE["navy_primary"],
        bins=35,
        stat="density",
        ax=ax,
        alpha=0.35,
        edgecolor=PALETTE["navy_primary"],
    )

    # Strategic threshold markers
    ax.axvline(1.25, color=PALETTE["rose_negative"], linestyle="--", linewidth=1.8,
               label=f"Bank Covenant Floor (1.25x) [P(Breach) = {summary.prob_covenant_breach*100:.1f}%]")
    ax.axvline(1.00, color=PALETTE["slate_dark"], linestyle=":", linewidth=1.8,
               label=f"Insolvency Floor (1.00x) [P(Default) = {summary.prob_cash_insolvency*100:.1f}%]")
    ax.axvline(summary.median_min_dscr, color=PALETTE["teal_positive"], linestyle="-", linewidth=2.0,
               label=f"Median Minimum DSCR ({summary.median_min_dscr:.2f}x)")
    ax.axvline(summary.p5_min_dscr, color=PALETTE["amber_warning"], linestyle="-.", linewidth=1.6,
               label=f"VaR 95% 5th Percentile ({summary.p5_min_dscr:.2f}x)")

    ax.set_title("Figure 3: Monte Carlo Simulation (N=1,000) - Minimum DSCR (Years 1-3) Probability Distribution", pad=14, fontweight="bold", color=PALETTE["slate_dark"])
    ax.set_xlabel("Minimum Debt Service Coverage Ratio, Years 1-3 (DSCR)", color=PALETTE["slate_dark"])
    ax.set_ylabel("Probability Density", color=PALETTE["slate_dark"])
    ax.legend(loc="upper right", frameon=True, facecolor=PALETTE["background_card"], edgecolor=PALETTE["slate_border"])

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_cash_flow_waterfall(save_path: Optional[Path] = None) -> Path:
    """Figure 4: Cash sources & uses at close (management case).

    The structure only closes because the cash equity is a plug of EUR 521k
    (49.6% of CapEx), not the 30% in the business plan. The net position is zero
    by construction, so the chart shows the cumulative funding bridge rather than
    a fictional gap.
    """
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_4_cash_flow_waterfall.png")

    from src.core.funding import SourcesUsesEngine

    funding = SourcesUsesEngine(case="management").compute()

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    steps = [
        ("Senior debt (35% LTV)", funding.senior_debt),
        ("VAT bridge", funding.vat_bridge),
        ("Cash equity plug", funding.cash_equity_required),
        ("Cash CapEx", -funding.cash_capex),
        ("Interest during construction", -funding.idc),
        ("Input VAT (bridge-funded)", -funding.input_vat),
        ("Pre-opening costs", -funding.pre_opening_costs),
        ("Working capital", -funding.initial_working_capital),
        ("DSRA (6 months)", -funding.dsra),
    ]

    labels = [s[0] for s in steps] + ["Net position at close"]
    deltas = [s[1] / 1000.0 for s in steps]
    cumulative = np.cumsum(deltas).tolist() + [0.0]
    starts = [0.0] + cumulative[:-2] + [0.0]
    # For a waterfall the final bar spans from 0 to the net position (0 here);
    # draw it as a flat marker at zero.
    bottoms = []
    heights = []
    for i, d in enumerate(deltas):
        bottom = min(starts[i], starts[i] + d)
        bottoms.append(bottom)
        heights.append(abs(d))
    bottoms.append(0.0)
    heights.append(0.0)

    colors = [
        PALETTE["teal_positive"] if d > 0 else PALETTE["rose_negative"]
        for d in deltas
    ] + [PALETTE["navy_primary"]]

    y_pos = np.arange(len(labels))
    bars = ax.barh(
        y_pos, heights, left=bottoms, color=colors, height=0.55,
        edgecolor=PALETTE["slate_border"], linewidth=0.8,
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=PALETTE["slate_dark"], fontweight="bold")
    ax.set_xlabel("EUR thousands (EURk)", color=PALETTE["slate_dark"])
    ax.set_title(
        "Figure 4: Cash Sources & Uses at Close - The EUR 521k Equity Plug (49.6% of CapEx)",
        pad=14, fontweight="bold", color=PALETTE["slate_dark"],
    )
    ax.axvline(0, color=PALETTE["slate_dark"], linewidth=0.8)
    ax.invert_yaxis()

    for i, (bar, d) in enumerate(zip(bars, deltas)):
        sign = "+" if d > 0 else ""
        x_text = cumulative[i] + (12 if d >= 0 else -12)
        ha = "left" if d >= 0 else "right"
        ax.text(
            x_text, bar.get_y() + bar.get_height() / 2,
            f"{sign}{d:,.1f}k",
            va="center", ha=ha, fontsize=8.5, fontweight="bold",
            color=PALETTE["slate_dark"],
        )

    ax.text(
        0, len(labels) - 1,
        "EUR 0.00 gap\n(sources = uses)",
        va="center", ha="left", fontsize=8.5, fontweight="bold",
        color=PALETTE["navy_primary"],
    )

    ax.set_xlim(-120, 1180)
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_copula_tail_risk_chart(output_path: Optional[Path] = None) -> Path:
    """
    Figure 5: Institutional 2-panel chart demonstrating multivariate copula tail risk.
    Panel A: Scatter comparison of Gaussian vs. Clayton lower-tail clustering.
    Panel B: Empirical tail probability density of DSCR with VaR 99% and CVaR 99% shortfall.
    Uses strictly the unified institutional palette.
    """
    set_institutional_style()
    save_path = output_path or (get_assets_dir() / "figure_5_copula_tail_risk.png")

    from src.simulation.copula_engine import CopulaSimulationEngine
    from src.config.ine_weights import get_annual_weighted_occupancy

    engine = CopulaSimulationEngine(n_simulations=50_000, random_seed=42)
    results = engine.run_comparative_analysis()

    # The copula shocks occupancy relative to the Year-2 management base
    # (mature 31.36%, no ramp discount in Year 2).
    base_occ_pct = get_annual_weighted_occupancy() * 100.0

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.2))

    # --- Panel A: Joint Tail Dependency Scatter ---
    # Subsample 2,500 points for clarity and high visual definition
    idx = np.random.default_rng(42).choice(50_000, size=2500, replace=False)
    occ_g_sub = results.occ_gaussian[idx] * base_occ_pct  # Occupancy %
    dscr_g_sub = results.dscr_gaussian[idx]

    occ_c_sub = results.occ_clayton[idx] * base_occ_pct
    dscr_c_sub = results.dscr_clayton[idx]

    ax1.scatter(
        occ_g_sub,
        dscr_g_sub,
        color=PALETTE["slate_benchmark"],
        alpha=0.35,
        s=16,
        label="Gaussian Copula (Thin Tail, lambda_L=0)",
        edgecolors="none",
    )
    ax1.scatter(
        occ_c_sub,
        dscr_c_sub,
        color=PALETTE["rose_negative"],
        alpha=0.45,
        s=18,
        label="Clayton Copula (Asymmetric Tail, lambda_L=0.68)",
        edgecolors="none",
    )

    # Threshold lines
    ax1.axhline(1.25, color=PALETTE["amber_warning"], linestyle="--", linewidth=1.4, label="Target Covenant (DSCR 1.25x)")
    ax1.axhline(1.00, color=PALETTE["slate_dark"], linestyle="-", linewidth=1.5, label="Default Threshold (DSCR 1.00x)")

    # Distress zone annotation
    ax1.axhspan(-0.5, 1.0, color=PALETTE["rose_negative"], alpha=0.06)
    ax1.text(
        15.5,
        0.10,
        "Systemic Distress Zone\n(Clayton lower-tail clustering)",
        color=PALETTE["rose_negative"],
        fontsize=8.5,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=PALETTE["rose_negative"], alpha=0.9),
    )

    ax1.set_xlim(12, 45)
    ax1.set_ylim(-0.3, 2.7)
    ax1.set_xlabel("Year 2 Effective Occupancy Rate (%)", color=PALETTE["slate_dark"])
    ax1.set_ylabel("Year 2 Debt Service Coverage Ratio (DSCR)", color=PALETTE["slate_dark"])
    ax1.set_title("(A) Joint Tail Dependency: Clayton Clustering vs. Gaussian Model", pad=12, fontweight="bold", color=PALETTE["slate_dark"])
    ax1.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.95, edgecolor=PALETTE["slate_border"], fontsize=8)

    # --- Panel B: Empirical Tail Density & CVaR ---
    # Kernel Density Estimation of Year 1 DSCR
    bins = np.linspace(-0.5, 2.8, 120)
    sns.kdeplot(
        results.dscr_gaussian,
        ax=ax2,
        color=PALETTE["slate_benchmark"],
        linestyle="--",
        linewidth=1.8,
        label=f"Gaussian (VaR 99%: {results.gaussian.var_99:.2f}x, CVaR: {results.gaussian.cvar_99:.2f}x)",
    )
    sns.kdeplot(
        results.dscr_student_t,
        ax=ax2,
        color=PALETTE["navy_primary"],
        linestyle="-",
        linewidth=1.6,
        label=f"Student-t nu=4 (VaR 99%: {results.student_t.var_99:.2f}x, CVaR: {results.student_t.cvar_99:.2f}x)",
    )
    sns.kdeplot(
        results.dscr_clayton,
        ax=ax2,
        color=PALETTE["rose_negative"],
        linestyle="-",
        linewidth=2.2,
        label=f"Clayton theta=1.8 (VaR 99%: {results.clayton.var_99:.2f}x, CVaR: {results.clayton.cvar_99:.2f}x)",
    )

    # Shaded CVaR 99% area for Clayton
    var_99_clayton = results.clayton.var_99
    kde_line = ax2.get_lines()[-1]
    x_kde, y_kde = kde_line.get_data()
    mask_cvar = x_kde <= var_99_clayton
    ax2.fill_between(
        x_kde[mask_cvar],
        y_kde[mask_cvar],
        color=PALETTE["rose_negative"],
        alpha=0.25,
        label=f"Clayton CVaR 99% Shortfall ({results.clayton.tail_deficit_cvar99_eur:,.0f} €)",
    )

    ax2.axvline(1.25, color=PALETTE["amber_warning"], linestyle="--", linewidth=1.4)
    ax2.axvline(1.00, color=PALETTE["slate_dark"], linestyle="-", linewidth=1.5)
    ax2.axvline(var_99_clayton, color=PALETTE["rose_negative"], linestyle=":", linewidth=1.6)

    ax2.text(
        var_99_clayton + 0.05,
        0.55,
        f"VaR 99% ({var_99_clayton:.2f}x)\nCVaR 99% ({results.clayton.cvar_99:.2f}x)",
        color=PALETTE["rose_negative"],
        fontsize=8.2,
        fontweight="bold",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=PALETTE["rose_negative"], alpha=0.9),
    )

    ax2.set_xlim(-0.4, 2.7)
    ax2.set_xlabel("Year 2 Debt Service Coverage Ratio (DSCR)", color=PALETTE["slate_dark"])
    ax2.set_ylabel("Empirical Probability Density", color=PALETTE["slate_dark"])
    ax2.set_title("(B) Downside Tail Distribution & Expected Shortfall (CVaR 99%)", pad=12, fontweight="bold", color=PALETTE["slate_dark"])
    ax2.legend(loc="upper right", frameon=True, facecolor="white", framealpha=0.95, edgecolor=PALETTE["slate_border"], fontsize=8)

    plt.suptitle("Figure 5: Multivariate Copula Tail Risk on the Year-2 DSCR - Asymmetric Lower Tail Clustering vs. Naive Gaussian Model",
                 fontsize=12, fontweight="bold", color=PALETTE["slate_dark"], y=0.99)
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_monthly_cash_runway_chart(save_path: Optional[Path] = None) -> Path:
    """Figure 6: 24-Month Cash Runway, Cash Trough & Liquidity Safety Buffer."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_6_monthly_cash_runway.png")

    from src.core.monthly_cash import MonthlyCashEngine

    mc = MonthlyCashEngine()
    df_monthly = mc.run_monthly_schedule(horizon_months=24)
    summary = mc.get_runway_summary(df_monthly)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Panel A: Year 1 Monthly Operating Cash Flows
    df_y1 = df_monthly[df_monthly["year"] == 1]
    months_y1 = [m[:3] for m in df_y1["month_name"]]
    x_y1 = np.arange(len(months_y1))

    colors_cf = [PALETTE["teal_positive"] if v >= 0 else PALETTE["rose_negative"] for v in df_y1["operating_cash_flow"]]
    ax1.bar(x_y1, df_y1["operating_cash_flow"] / 1000, color=colors_cf, width=0.55, edgecolor=PALETTE["slate_border"], label="Operating Cash Flow")
    ax1.plot(x_y1, df_y1["gross_revenue"] / 1000, color=PALETTE["navy_primary"], marker="o", markersize=4, linewidth=1.8, label="Gross Revenue (kEUR)")
    fixed_burden_k = (df_y1["fixed_payroll"].iloc[0] + df_y1["fixed_opex"].iloc[0] + df_y1["senior_debt_service"].iloc[0]) / 1000
    ax1.axhline(fixed_burden_k, color=PALETTE["amber_warning"], linestyle="--", linewidth=1.4, label=f"Fixed Burden ({fixed_burden_k:.1f}kEUR/mo)")
    ax1.axhline(0, color=PALETTE["slate_dark"], linestyle="-", linewidth=0.8)

    ax1.set_xticks(x_y1)
    ax1.set_xticklabels(months_y1)
    ax1.set_ylabel("Thousand EUR (EURk)", color=PALETTE["slate_dark"])
    ax1.set_title("(A) Year 1 Monthly Operating Cash Flow & Seasonality", pad=12, fontweight="bold", color=PALETTE["slate_dark"])
    ax1.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.95, edgecolor=PALETTE["slate_border"], fontsize=8)

    trough_idx = int(summary.year1_trough_month_index) - 1
    trough_val = df_y1.iloc[trough_idx]["operating_cash_flow"] / 1000
    ax1.annotate(f"Winter Trough\n({trough_val:.1f}kEUR burn)", xy=(trough_idx, trough_val), xytext=(trough_idx, trough_val - 4),
                 arrowprops=dict(arrowstyle="->", color=PALETTE["rose_negative"]),
                 fontsize=8, fontweight="bold", ha="center", color=PALETTE["rose_negative"])

    peak_idx = 7
    peak_val = df_y1.iloc[peak_idx]["operating_cash_flow"] / 1000
    ax1.annotate(f"Summer Peak\n(+{peak_val:.1f}kEUR surplus)", xy=(peak_idx, peak_val), xytext=(peak_idx, peak_val + 3),
                 arrowprops=dict(arrowstyle="->", color=PALETTE["teal_positive"]),
                 fontsize=8, fontweight="bold", ha="center", color=PALETTE["teal_positive"])

    # Panel B: 24-Month Cumulative Cash & Liquidity Buffer
    m_indices = df_monthly["month_index"].values
    cash_k = df_monthly["ending_cash_balance"].values / 1000
    total_liq_k = df_monthly["liquidity_buffer_total"].values / 1000

    ax2.plot(m_indices, cash_k, color=PALETTE["navy_primary"], marker="s", markersize=3.5, linewidth=2.0, label="Ending Cash Balance (kEUR)")
    ax2.fill_between(m_indices, cash_k, color=PALETTE["navy_light"], alpha=0.15)
    ax2.plot(m_indices, total_liq_k, color=PALETTE["teal_positive"], linestyle=":", linewidth=1.8, label="Total Available Liquidity (Cash + Undrawn Revolver)")

    ax2.axvline(summary.year1_trough_month_index, color=PALETTE["rose_negative"], linestyle="--", linewidth=1.2)
    ax2.annotate(
        f"Cash Trough: {summary.year1_trough_month}\n"
        f"(EUR {summary.year1_trough_cash_balance:,.0f} pre-revolver, "
        f"EUR {summary.year1_max_credit_line_draw:,.0f} drawn)",
        xy=(summary.year1_trough_month_index, summary.year1_trough_actual_cash / 1000),
        xytext=(summary.year1_trough_month_index + 1.2, summary.year1_trough_actual_cash / 1000 - 12),
        arrowprops=dict(arrowstyle="->", color=PALETTE["rose_negative"]),
        fontsize=8, fontweight="bold", color=PALETTE["rose_negative"],
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=PALETTE["rose_negative"], alpha=0.9),
    )

    ax2.axvline(14, color=PALETTE["amber_warning"], linestyle="--", linewidth=1.2)
    ax2.annotate("LEADER Grant\n(+EUR 163k, Month 14)", xy=(14, cash_k[13]), xytext=(9.5, cash_k[13] + 20),
                 arrowprops=dict(arrowstyle="->", color=PALETTE["amber_warning"]),
                 fontsize=8, fontweight="bold", color=PALETTE["amber_warning"])

    ax2.axvline(18, color=PALETTE["teal_positive"], linestyle="--", linewidth=1.2)
    ax2.annotate("AEAT VAT Refund\n(+EUR 168k, Month 18)\nrepays the bridge", xy=(18, cash_k[17]), xytext=(15.0, cash_k[17] + 25),
                 arrowprops=dict(arrowstyle="->", color=PALETTE["teal_positive"]),
                 fontsize=8, fontweight="bold", color=PALETTE["teal_positive"])

    ax2.set_xlabel("Operational Month (1 to 24)", color=PALETTE["slate_dark"])
    ax2.set_ylabel("Liquidity Cushion (EURk)", color=PALETTE["slate_dark"])
    ax2.set_title("(B) 24-Month Cumulative Cash Runway & Solvency Bridge", pad=12, fontweight="bold", color=PALETTE["slate_dark"])
    ax2.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.95, edgecolor=PALETTE["slate_border"], fontsize=8)

    plt.suptitle("Figure 6: Monthly Cash Runway, Winter Cash Trough & Working Capital Bridge",
                 fontsize=12, fontweight="bold", color=PALETTE["slate_dark"], y=0.99)
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_reform_value_bridge(save_path: Optional[Path] = None) -> Path:
    """Figure 7: R2 value bridge and the CapEx / external-cover value frontier."""
    from src.config.reform import get_reform_preset
    from src.core.reform import ReformAnalysisEngine

    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_7_reform_value_bridge.png")

    engine = ReformAnalysisEngine()
    bridge = engine.value_bridge(get_reform_preset("revenue_reform"))
    frontier = engine.frontier(
        capex_levels=[1_050_100, 950_000, 850_000, 770_000, 700_000],
        cover_levels=[0, 3, 6, 8, 10],
        base_config=get_reform_preset("revenue_reform"),
    )

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(15.5, 6.4), gridspec_kw={"width_ratios": [1.0, 1.05]}
    )

    # --- (A) Mature-EBITDA value bridge ---------------------------------
    base = bridge["base_ebitda"]
    components = bridge["components_ebitda"]
    labels = ["Base\nEBITDA", "+5% ADR", "External\nF&B", "Experiences", "Cost\nsavings", "Reform\nEBITDA"]
    values = [
        base,
        components["adr_uplift"],
        components["external_fnb"],
        components["experiences"],
        components["cost_savings"],
        bridge["reform_ebitda"],
    ]

    bottoms = [0.0]
    tops = [base]
    cumulative = base
    for value in values[1:-1]:
        bottoms.append(cumulative)
        cumulative += value
        tops.append(cumulative)
    bottoms.append(0.0)
    tops.append(bridge["reform_ebitda"])

    colors = [
        PALETTE["navy_primary"],
        PALETTE["teal_positive"],
        PALETTE["teal_positive"],
        PALETTE["teal_positive"],
        PALETTE["teal_positive"],
        PALETTE["navy_light"],
    ]
    heights = [tops[i] - bottoms[i] for i in range(len(values))]
    x = np.arange(len(values))
    ax1.bar(x, heights, bottom=bottoms, color=colors, width=0.62, edgecolor="white", linewidth=0.8)

    for xi, (top, value) in enumerate(zip(tops, values)):
        ax1.annotate(
            f"{value:,.0f}",
            xy=(xi, top),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color=PALETTE["slate_dark"],
        )

    # Connector lines between the cumulative steps.
    for xi in range(len(values) - 1):
        ax1.plot(
            [xi + 0.31, xi + 1 - 0.31],
            [tops[xi], tops[xi]],
            color=PALETTE["slate_benchmark"],
            linewidth=0.8,
            linestyle=":",
        )

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=8.5)
    ax1.set_ylabel("Mature annual EBITDA (EUR)", color=PALETTE["slate_dark"])
    ax1.set_title(
        "(A) R2 Value Bridge: Where the EBITDA Comes From",
        pad=10,
        fontweight="bold",
        color=PALETTE["slate_dark"],
    )

    gap_capex = bridge["value_gap_capex"]
    gap_invest = bridge["value_gap_total_investment"]
    ax1.text(
        0.02,
        0.96,
        (
            f"Cap-rate EV @ 8.5%: EUR {bridge['reform_ev']:,.0f}\n"
            f"CapEx: EUR {bridge['capex']:,.0f}  ->  gap {gap_capex:,.0f}\n"
            f"Total investment: EUR {bridge['total_project_investment']:,.0f}\n"
            f"-> gap {gap_invest:,.0f} (bank test)"
        ),
        transform=ax1.transAxes,
        va="top",
        ha="left",
        fontsize=8.3,
        color=PALETTE["slate_dark"],
        bbox=dict(
            boxstyle="round,pad=0.5",
            facecolor="#F8FAFC",
            edgecolor=PALETTE["slate_border"],
            alpha=0.95,
        ),
    )
    ax1.set_ylim(0, bridge["reform_ebitda"] * 1.18)

    # --- (B) Value frontier: CapEx x external covers ---------------------
    grid = frontier.to_numpy(dtype=float) / 1000.0
    cmap = LinearSegmentedColormap.from_list(
        "reform_gap",
        [PALETTE["rose_negative"], "#F8FAFC", PALETTE["teal_positive"]],
    )
    vmax = max(abs(float(np.nanmin(grid))), abs(float(np.nanmax(grid))), 1.0)
    im = ax2.imshow(
        grid,
        cmap=cmap,
        aspect="auto",
        vmin=-vmax,
        vmax=vmax,
        interpolation="nearest",
    )

    ax2.set_xticks(np.arange(len(frontier.columns)))
    ax2.set_xticklabels([f"{c:.0f}" for c in frontier.columns], fontsize=9)
    ax2.set_yticks(np.arange(len(frontier.index)))
    ax2.set_yticklabels([f"{c/1000:,.0f}k" for c in frontier.index], fontsize=9)
    ax2.set_xlabel("External F&B covers per day", color=PALETTE["slate_dark"])
    ax2.set_ylabel("Reform CapEx (EUR)", color=PALETTE["slate_dark"])

    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            value = grid[i, j]
            ax2.text(
                j,
                i,
                f"{value:,.0f}",
                ha="center",
                va="center",
                fontsize=8.2,
                fontweight="bold",
                color="white" if abs(value) > vmax * 0.55 else PALETTE["slate_dark"],
            )

    cbar = fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.03)
    cbar.set_label("EV - total investment (EURk); >0 is value-creating", fontsize=8.5)
    cbar.ax.tick_params(labelsize=8)

    ax2.set_title(
        "(B) Value Frontier: Negative Cells Destroy Value",
        pad=10,
        fontweight="bold",
        color=PALETTE["slate_dark"],
    )

    fig.suptitle(
        "Figure 7: Reform / Resize Case - Revenue Bridge and Capital Frontier",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["slate_dark"],
        y=1.01,
    )
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def generate_occupancy_bridge_chart(save_path: Optional[Path] = None) -> Path:
    """Figure 8: management vs INE occupancy by segment and the gap waterfall."""
    from src.core.demand_bridge import INE_MIX, MANAGEMENT_MIX, build_bridge

    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_8_occupancy_bridge.png")
    bridge = build_bridge()

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(15.2, 6.2), gridspec_kw={"width_ratios": [1.0, 1.0]}
    )

    # --- (A) Segment occupancy ------------------------------------------
    labels = [segment.label for segment in MANAGEMENT_MIX.segments]
    management = [segment.occupancy * 100 for segment in MANAGEMENT_MIX.segments]
    market = [segment.occupancy * 100 for segment in INE_MIX.segments]
    x = np.arange(len(labels))
    width = 0.34

    bars_mgmt = ax1.bar(
        x - width / 2,
        management,
        width,
        label="Management case",
        color=PALETTE["navy_primary"],
        edgecolor="white",
        linewidth=0.8,
    )
    bars_market = ax1.bar(
        x + width / 2,
        market,
        width,
        label="INE Segovia",
        color=PALETTE["slate_benchmark"],
        edgecolor="white",
        linewidth=0.8,
    )

    for bars in (bars_mgmt, bars_market):
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(
                f"{height:.1f}%",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                fontsize=8.5,
                fontweight="bold",
                color=PALETTE["slate_dark"],
            )

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel("Occupancy (%)", color=PALETTE["slate_dark"])
    ax1.set_ylim(0, 85)
    ax1.legend(frameon=False, loc="upper right", fontsize=9)
    ax1.set_title(
        "(A) The gap is weekend capture, not seven-day demand",
        pad=10,
        fontweight="bold",
        color=PALETTE["slate_dark"],
    )

    # --- (B) Gap waterfall ----------------------------------------------
    contributions = bridge["gap_contributions_pp"]
    steps = [
        ("Weekend", contributions["weekend"]),
        ("Holiday", contributions["peak"]),
        ("Midweek", contributions["midweek"]),
        ("Total gap", bridge["gap_pp"]),
    ]
    bottoms = [0.0, 0.0, 0.0, 0.0]
    cumulative = 0.0
    for i, (_, value) in enumerate(steps[:-1]):
        bottoms[i] = cumulative
        cumulative += value
    bottoms[-1] = 0.0
    heights = [value for _, value in steps]
    colors = [
        PALETTE["teal_positive"],
        PALETTE["teal_positive"],
        PALETTE["teal_positive"],
        PALETTE["navy_primary"],
    ]
    bars = ax2.bar(
        np.arange(len(steps)),
        heights,
        bottom=bottoms,
        color=colors,
        width=0.62,
        edgecolor="white",
        linewidth=0.8,
    )
    for i, bar in enumerate(bars):
        value = steps[i][1]
        y = bottoms[i] + heights[i]
        ax2.annotate(
            f"+{value:.2f} pp" if i < len(steps) - 1 else f"{value:.2f} pp",
            xy=(bar.get_x() + bar.get_width() / 2, y),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold",
            color=PALETTE["slate_dark"],
        )

    for i in range(len(steps) - 1):
        ax2.plot(
            [i + 0.31, i + 1 - 0.31],
            [bottoms[i] + heights[i], bottoms[i] + heights[i]],
            color=PALETTE["slate_benchmark"],
            linewidth=0.8,
            linestyle=":",
        )

    ax2.set_xticks(np.arange(len(steps)))
    ax2.set_xticklabels([label for label, _ in steps], fontsize=9)
    ax2.set_ylabel("Percentage points of occupancy", color=PALETTE["slate_dark"])
    ax2.set_ylim(0, bridge["gap_pp"] * 1.25)
    ax2.set_title(
        f"(B) {bridge['gap_shares']['weekend']*100:.0f}% of the gap is weekend capture",
        pad=10,
        fontweight="bold",
        color=PALETTE["slate_dark"],
    )

    fig.text(
        0.5,
        -0.02,
        (
            "Management 31.36% vs INE 21.24%. Calendar: 104 weekend, 24 holiday-bridge and "
            "237 midweek nights. The mix is an annual average; the monthly seasonality lives in Figure 1."
        ),
        ha="center",
        fontsize=8.5,
        color=PALETTE["slate_dark"],
    )
    fig.suptitle(
        "Figure 8: Occupancy Bridge - Management Case vs INE Segovia",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["slate_dark"],
        y=1.01,
    )
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def generate_five_act_timeline(save_path: Optional[Path] = None) -> Path:
    """Figure 9: the five-act narrative arc and the verdict at each act."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_9_five_act_timeline.png")

    acts = [
        (
            "ACT 1",
            "The promoter's pitch",
            "8 keys + 21-cover restaurant\nEUR 725k all-in, 30% equity",
            "PITCH",
            PALETTE["slate_benchmark"],
        ),
        (
            "ACT 2",
            "Institutional audit",
            "Full cost stack: EUR 1.05M all-in\nCash equity plug EUR 521k (49.6%)",
            "AUDIT",
            PALETTE["navy_light"],
        ),
        (
            "ACT 3",
            "Credit committee",
            "Y2 DSCR 1.15x vs 1.25x\nPhase II gap EUR 252k; fixed-cost trap",
            "DECLINE",
            PALETTE["rose_negative"],
        ),
        (
            "ACT 4",
            "Cabin turnaround",
            "6 cabins + caseron lodge\nEUR 621.6k cash, no restaurant",
            "RESET",
            PALETTE["teal_positive"],
        ),
        (
            "ACT 5",
            "Executive comparison",
            "Min DSCR 2.31x, equity IRR 39.7% cash\nNet exit EUR 1.26M",
            "PROCEED",
            PALETTE["navy_primary"],
        ),
    ]

    fig, ax = plt.subplots(figsize=(15.5, 6.6), dpi=300)
    ax.set_xlim(-0.6, len(acts) - 0.4)
    ax.set_ylim(-1.55, 1.55)
    ax.axis("off")

    ax.annotate(
        "",
        xy=(len(acts) - 0.55, 0),
        xytext=(-0.45, 0),
        arrowprops=dict(
            arrowstyle="-|>", color=PALETTE["slate_border"], lw=3.0,
            shrinkA=0, shrinkB=0, mutation_scale=22,
        ),
    )

    for i, (act, title, detail, verdict, color) in enumerate(acts):
        above = i % 2 == 0
        y_box = 0.62 if above else -0.62
        y_text = 1.12 if above else -1.12

        ax.plot([i, i], [0, y_box - 0.22 if above else y_box + 0.22],
                color=color, lw=1.2, linestyle=":", zorder=1)
        ax.scatter([i], [0], s=640, color=color, edgecolor="white",
                   linewidth=2.4, zorder=3)
        ax.text(i, 0, str(i + 1), ha="center", va="center", color="white",
                fontsize=13, fontweight="bold", zorder=4)

        box = Rectangle(
            (i - 0.44, y_box - 0.30), 0.88, 0.60,
            facecolor=PALETTE["background_card"], edgecolor=color,
            linewidth=1.4, zorder=2,
        )
        ax.add_patch(box)
        ax.text(i, y_box + 0.18, act, ha="center", va="center",
                color=color, fontsize=8.5, fontweight="bold", zorder=5)
        ax.text(i, y_box + 0.02, title, ha="center", va="center",
                color=PALETTE["slate_dark"], fontsize=9.5, fontweight="bold", zorder=5)
        ax.text(i, y_box - 0.17, detail, ha="center", va="center",
                color=PALETTE["slate_dark"], fontsize=7.6, zorder=5)

        badge_color = PALETTE["teal_positive"] if verdict == "PROCEED" else (
            PALETTE["rose_negative"] if verdict in ("DECLINE", "UNFUNDABLE") else color
        )
        ax.text(i, y_text, verdict, ha="center", va="center", color="white",
                fontsize=8.5, fontweight="bold", zorder=5,
                bbox=dict(boxstyle="round,pad=0.32", facecolor=badge_color,
                          edgecolor="none"))

    ax.text(
        -0.55, 1.43,
        "Figure 9: Five-Act Narrative - From Credit Committee Decline to a High-Margin Nature Retreat",
        ha="left", va="center", fontsize=13, fontweight="bold",
        color=PALETTE["slate_dark"],
    )
    ax.text(
        -0.55, -1.44,
        "Same land, same promoter, same bank. The decline is not the end of the story: it is the "
        "constraint that forces the product to change.",
        ha="left", va="center", fontsize=8.6, style="italic",
        color=PALETTE["slate_dark"],
    )

    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def generate_three_case_comparison(save_path: Optional[Path] = None) -> Path:
    """Figure 10: promoter vs audited vs T8 on the four decisive metrics."""
    from src.core.investment_case import InvestmentCase

    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_10_three_case_comparison.png")

    snapshots = InvestmentCase().snapshots()
    labels = ["Promoter\npitch", "Audited\ncase", "Cabin\nturnaround"]
    colors = [
        PALETTE["slate_benchmark"],
        PALETTE["rose_negative"],
        PALETTE["teal_positive"],
    ]

    panels = [
        ("(A) All-in capital (EURk)", [s.all_in_capex / 1000 for s in snapshots], "{:,.0f}k"),
        ("(B) Cash equity required (EURk)", [s.cash_equity / 1000 for s in snapshots], "{:,.0f}k"),
        ("(C) Minimum DSCR (x)", [s.dscr_min for s in snapshots], "{:.2f}x"),
        ("(D) Equity IRR, all-in (%)", [s.equity_irr_allin * 100 for s in snapshots], "{:.1f}%"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13.6, 8.4), dpi=300)
    for ax, (title, values, fmt) in zip(axes.flat, panels):
        bars = ax.bar(np.arange(3), values, color=colors, width=0.58,
                      edgecolor="white", linewidth=0.9)
        ax.set_xticks(np.arange(3))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_title(title, pad=10, fontweight="bold", color=PALETTE["slate_dark"])
        ax.axhline(0, color=PALETTE["slate_dark"], linewidth=0.9)
        for bar, value in zip(bars, values):
            offset = 3 if value >= 0 else -12
            ax.annotate(
                fmt.format(value),
                xy=(bar.get_x() + bar.get_width() / 2, value),
                xytext=(0, offset), textcoords="offset points",
                ha="center", fontsize=9.5, fontweight="bold",
                color=PALETTE["slate_dark"],
            )
        if title.startswith("(C)"):
            ax.axhline(1.25, color=PALETTE["amber_warning"], linewidth=1.3,
                       linestyle="--", label="1.25x covenant")
            ax.set_ylim(0, 2.7)
            ax.legend(frameon=False, fontsize=8, loc="upper right")
        pad = 0.20 * max(abs(v) for v in values) if values else 1.0
        if title.startswith("(D)"):
            ax.set_ylim(min(0, min(values) - 6), max(values) + 8)
        else:
            ax.set_ylim(0, max(values) * 1.22 + pad * 0.1)

    fig.suptitle(
        "Figure 10: Promoter vs Audited vs Cabin Turnaround - The Same Asset, Three Answers",
        fontsize=13.5, fontweight="bold", color=PALETTE["slate_dark"], y=1.02,
    )
    fig.text(
        0.5, -0.01,
        "All three columns exit at an 8.5% cap rate and deduct 3% selling costs. "
        "The audited equity IRR is shown net of those costs (-24.4%); gross it is -23.16%.",
        ha="center", fontsize=8.4, color=PALETTE["slate_dark"],
    )
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def generate_t8_dscr_cash(save_path: Optional[Path] = None) -> Path:
    """Figure 11: T8 DSCR against the covenant and the cash build."""
    from src.core.turnaround import TurnaroundEngine

    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_11_t8_dscr_cash.png")

    engine = TurnaroundEngine()
    kpis = engine.kpis
    proj = engine.projection
    years = [f"Y{int(y)}" for y in kpis["year"]]
    dscr = kpis["dscr"].astype(float).tolist()
    cash = (proj["ending_cash"].astype(float) / 1000).tolist()
    x = np.arange(len(years))

    fig, ax = plt.subplots(figsize=(11.2, 5.6), dpi=300)
    bars = ax.bar(x, dscr, width=0.52, color=PALETTE["navy_primary"],
                  edgecolor="white", linewidth=0.9, label="DSCR (x)")
    ax.axhline(1.25, color=PALETTE["amber_warning"], linewidth=1.5,
               linestyle="--", label="1.25x covenant")
    ax.axhline(1.00, color=PALETTE["rose_negative"], linewidth=1.1,
               linestyle=":", label="1.00x debt-service floor")
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_ylabel("DSCR (x)", color=PALETTE["slate_dark"])
    ax.set_ylim(0, max(dscr) * 1.28)
    for bar, value in zip(bars, dscr):
        ax.annotate(
            f"{value:.2f}x",
            xy=(bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 5), textcoords="offset points",
            ha="center", fontsize=9.5, fontweight="bold",
            color=PALETTE["slate_dark"],
        )

    ax2 = ax.twinx()
    ax2.plot(x, cash, color=PALETTE["teal_positive"], marker="o", linewidth=2.2,
             label="Ending cash (EURk)")
    ax2.set_ylabel("Ending cash (EURk)", color=PALETTE["teal_positive"])
    ax2.set_ylim(0, max(cash) * 1.30)
    for xi, value in zip(x, cash):
        ax2.annotate(
            f"{value:,.0f}k", xy=(xi, value), xytext=(0, 9),
            textcoords="offset points", ha="center", fontsize=8.5,
            color=PALETTE["teal_positive"], fontweight="bold",
        )

    handles_1, labels_1 = ax.get_legend_handles_labels()
    handles_2, labels_2 = ax2.get_legend_handles_labels()
    ax.legend(handles_1 + handles_2, labels_1 + labels_2, loc="upper left",
              frameon=True, facecolor=PALETTE["background_card"],
              edgecolor=PALETTE["slate_border"], fontsize=8.5)

    ax.set_title(
        "Figure 11: T8 Credit Profile - 2.31x Minimum DSCR and a Cash Build to EUR 241k",
        pad=12, fontweight="bold", color=PALETTE["slate_dark"],
    )
    fig.text(
        0.5, -0.02,
        "The binding year is Year 2 (2.31x). Year 1 carries interest only (3.35x). "
        "Cash is after debt service, FF&E reserve, DSRA and the VAT bridge repayment.",
        ha="center", fontsize=8.5, color=PALETTE["slate_dark"],
    )
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def generate_t8_irr_tornado(save_path: Optional[Path] = None) -> Path:
    """Figure 12: T8 equity IRR sensitivity tornado (all-in basis)."""
    from src.core.turnaround import TurnaroundEngine

    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_12_t8_irr_tornado.png")

    engine = TurnaroundEngine()
    sens = engine.sensitivities()
    base_row = sens[sens["scenario"] == "Base"].iloc[0]
    base = float(base_row["equity_irr_allin"]) * 100

    rows = sens[sens["scenario"] != "Base"].copy()
    rows["delta"] = rows["equity_irr_allin"].astype(float) * 100 - base
    rows = rows.sort_values("delta")

    fig, ax = plt.subplots(figsize=(11.6, 6.6), dpi=300)
    y = np.arange(len(rows))
    colors = [
        PALETTE["teal_positive"] if d >= 0 else PALETTE["rose_negative"]
        for d in rows["delta"]
    ]
    bars = ax.barh(y, rows["delta"], color=colors, edgecolor="white", linewidth=0.8)
    ax.axvline(0, color=PALETTE["slate_dark"], linewidth=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(rows["scenario"], fontsize=9)
    ax.set_xlabel("Change in all-in equity IRR vs base (percentage points)",
                  color=PALETTE["slate_dark"])
    ax.set_title(
        f"Figure 12: T8 Equity IRR Tornado - Base {base:.1f}% (All-In, 8.5% Exit Cap)",
        pad=12, fontweight="bold", color=PALETTE["slate_dark"],
    )
    ax.set_xlim(min(rows["delta"]) * 1.35 - 1.0, max(rows["delta"]) * 1.35 + 1.0)
    for bar, delta, irr in zip(bars, rows["delta"], rows["equity_irr_allin"]):
        x_text = delta + (0.35 if delta >= 0 else -0.35)
        ax.annotate(
            f"{irr*100:.1f}%  ({delta:+.1f} pp)",
            xy=(x_text, bar.get_y() + bar.get_height() / 2),
            xytext=(0, 0), textcoords="offset points",
            ha="left" if delta >= 0 else "right", va="center",
            fontsize=8.6, fontweight="bold", color=PALETTE["slate_dark"],
        )

    ax.text(
        0.01, -0.16,
        "Downside is real: a 45% cabin occupancy still passes the 1.25x covenant but cuts the "
        "all-in equity IRR to 5.5%. The lodge adds about 11 pp of IRR.",
        transform=ax.transAxes, fontsize=8.4, color=PALETTE["slate_dark"],
    )
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def generate_all_figures():
    """Generates all 12 institutional figures using the unified palette."""
    p1 = generate_seasonality_chart()
    p2 = generate_dscr_sensitivity_heatmap()
    p3 = generate_monte_carlo_distribution()
    p4 = generate_cash_flow_waterfall()
    p5 = generate_copula_tail_risk_chart()
    p6 = generate_monthly_cash_runway_chart()
    p7 = generate_reform_value_bridge()
    p8 = generate_occupancy_bridge_chart()
    p9 = generate_five_act_timeline()
    p10 = generate_three_case_comparison()
    p11 = generate_t8_dscr_cash()
    p12 = generate_t8_irr_tornado()
    return [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12]


if __name__ == "__main__":
    figs = generate_all_figures()
    for f in figs:
        print(f"Generated unified figure: {f.name} ({f.stat().st_size / 1024:.1f} KB)")

