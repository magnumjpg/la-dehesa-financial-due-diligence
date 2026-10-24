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


def generate_all_figures():
    """Generates all 6 institutional figures using the unified palette."""
    p1 = generate_seasonality_chart()
    p2 = generate_dscr_sensitivity_heatmap()
    p3 = generate_monte_carlo_distribution()
    p4 = generate_cash_flow_waterfall()
    p5 = generate_copula_tail_risk_chart()
    p6 = generate_monthly_cash_runway_chart()
    return [p1, p2, p3, p4, p5, p6]


if __name__ == "__main__":
    figs = generate_all_figures()
    for f in figs:
        print(f"Generated unified figure: {f.name} ({f.stat().st_size / 1024:.1f} KB)")

