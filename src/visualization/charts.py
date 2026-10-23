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
2. figure_2_dscr_sensitivity_heatmap.png: 2D stress matrix of DSCR vs. interest rates and occupancy.
3. figure_3_monte_carlo_distribution.png: Monte Carlo probability density of DSCR and VaR 95%.
4. figure_4_cash_flow_waterfall.png: Due diligence cash flow waterfall showing the VAT correction and solvency bridge.
"""

from pathlib import Path
from typing import Optional
import sys
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
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
    rects2 = ax.bar(x + width / 2, base_rates, width, label="La Dehesa Target Occupancy Baseline", color=PALETTE["navy_primary"])

    ax.set_ylabel("Occupancy Rate (%)", color=PALETTE["slate_dark"])
    ax.set_title("Figure 1: Empirical Monthly Seasonality Curve (INE Segovia vs. Asset Baseline)", pad=14, fontweight="bold", color=PALETTE["slate_dark"])
    ax.set_xticks(x)
    ax.set_xticklabels(months, color=PALETTE["slate_dark"])
    ax.set_ylim(0, 65)
    ax.legend(frameon=True, facecolor=PALETTE["background_card"], edgecolor=PALETTE["slate_border"])

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

    ax.set_title("Figure 2: DSCR Underwriting Sensitivity Matrix (Year 1 Stress Test)", pad=14, fontweight="bold", color=PALETTE["slate_dark"])
    ax.set_xlabel("Senior Mortgage Interest Rate (Euribor + Margin)", color=PALETTE["slate_dark"])
    ax.set_ylabel("Occupancy Demand Multiplier", color=PALETTE["slate_dark"])

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_monte_carlo_distribution(save_path: Optional[Path] = None) -> Path:
    """Figure 3: Monte Carlo probability density of Year 1 DSCR across 1,000 iterations."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_3_monte_carlo_distribution.png")

    sim = MonteCarloSimulator(iterations=1000, random_seed=42)
    df_sim, summary = sim.run_simulation()

    fig, ax = plt.subplots(figsize=(10, 5.0), dpi=300)

    # Histogram and KDE strictly styled with unified palette
    sns.histplot(
        df_sim["dscr_y1"],
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
               label=f"Bank Covenant Floor (1.25x) [P(Breach) = {summary.prob_covenant_breach_y1*100:.1f}%]")
    ax.axvline(1.00, color=PALETTE["slate_dark"], linestyle=":", linewidth=1.8,
               label=f"Insolvency Floor (1.00x) [P(Default) = {summary.prob_cash_insolvency_y1*100:.1f}%]")
    ax.axvline(summary.median_dscr_y1, color=PALETTE["teal_positive"], linestyle="-", linewidth=2.0,
               label=f"Median DSCR ({summary.median_dscr_y1:.2f}x)")
    ax.axvline(summary.p5_dscr_y1, color=PALETTE["amber_warning"], linestyle="-.", linewidth=1.6,
               label=f"VaR 95% 5th Percentile ({summary.p5_dscr_y1:.2f}x)")

    ax.set_title("Figure 3: Monte Carlo Simulation (N=1,000) - Year 1 DSCR Probability Distribution", pad=14, fontweight="bold", color=PALETTE["slate_dark"])
    ax.set_xlabel("Year 1 Debt Service Coverage Ratio (DSCR)", color=PALETTE["slate_dark"])
    ax.set_ylabel("Probability Density", color=PALETTE["slate_dark"])
    ax.legend(loc="upper right", frameon=True, facecolor=PALETTE["background_card"], edgecolor=PALETTE["slate_border"])

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_cash_flow_waterfall(save_path: Optional[Path] = None) -> Path:
    """Figure 4: Year 1 cash flow waterfall showing the VAT correction and solvency bridge."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_4_cash_flow_waterfall.png")

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    steps = [
        "Gross Revenue (Y1)",
        "COGS (F&B)",
        "Labor (Segovia)",
        "Fixed OPEX",
        "EBITDA",
        "Debt Service",
        "VAT Error (-21%)",
        "VAT Correction & Bridge",
        "Net Cash (Solvency)",
    ]

    amounts = [96.6, -10.1, -60.1, -11.0, 15.4, -43.5, -152.3, 213.0, 60.8]

    # Bar colors strictly assigned from the unified palette:
    # Teal for inflows / positive margin, Rose for costs / debt / errors, Navy for final solvency
    colors = [
        PALETTE["teal_positive"] if a > 0 else PALETTE["rose_negative"]
        for a in amounts
    ]
    colors[-1] = PALETTE["navy_primary"]    # Final Net Solvency Bar (Deep Navy)
    colors[-3] = PALETTE["rose_negative"]   # Flawed 21% VAT impact
    colors[-2] = PALETTE["teal_positive"]   # Statutory VAT correction and bridge

    y_pos = np.arange(len(steps))
    bars = ax.barh(y_pos, amounts, color=colors, height=0.55, edgecolor=PALETTE["slate_border"], linewidth=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(steps, color=PALETTE["slate_dark"], fontweight="bold")
    ax.set_xlabel("Cash Flow Impact (€k)", color=PALETTE["slate_dark"])
    ax.set_title("Figure 4: Due Diligence Waterfall - Statutory VAT Restructuring & Year 1 Solvency Bridge", pad=14, fontweight="bold", color=PALETTE["slate_dark"])
    ax.axvline(0, color=PALETTE["slate_dark"], linewidth=0.8)

    for bar, val in zip(bars, amounts):
        sign = "+" if val > 0 else ""
        x_text = val + (3 if val >= 0 else -18)
        ax.text(x_text, bar.get_y() + bar.get_height() / 2, f"{sign}{val:.1f}k €",
                va="center", fontsize=8.5, fontweight="bold", color=PALETTE["slate_dark"])

    ax.set_xlim(-180, 245)
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_all_figures():
    """Generates all 4 institutional figures using the unified palette."""
    p1 = generate_seasonality_chart()
    p2 = generate_dscr_sensitivity_heatmap()
    p3 = generate_monte_carlo_distribution()
    p4 = generate_cash_flow_waterfall()
    return [p1, p2, p3, p4]


if __name__ == "__main__":
    figs = generate_all_figures()
    for f in figs:
        print(f"Generated unified figure: {f.name} ({f.stat().st_size / 1024:.1f} KB)")
