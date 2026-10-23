"""
Institutional charting and visualization engine for investment memoranda.

Generates high-resolution publication-quality figures:
1. figure_1_seasonality_ine.png: Empirical INE Segovia rural tourism curve vs. project baseline.
2. figure_2_dscr_sensitivity_heatmap.png: 2D stress matrix of DSCR vs. interest rates and occupancy.
3. figure_3_monte_carlo_distribution.png: Monte Carlo probability density of DSCR and VaR 95%.
4. figure_4_cash_flow_bridge.png: Year 1 cash flow waterfall showing the VAT correction and solvency bridge.
"""

from pathlib import Path
from typing import Optional
import sys
import matplotlib.pyplot as plt
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


def get_assets_dir() -> Path:
    assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def set_institutional_style():
    """Sets a clean, modern financial research aesthetic."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams.update(
        {
            "figure.titlesize": 14,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.autolayout": True,
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#D1D5DB",
            "axes.linewidth": 0.8,
            "grid.color": "#E5E7EB",
            "grid.linestyle": "--",
            "grid.alpha": 0.7,
        }
    )


def generate_seasonality_chart(save_path: Optional[Path] = None) -> Path:
    """Plots INE Segovia monthly seasonality curve vs. asset baseline."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_1_seasonality_ine.png")

    months = [m.month_name[:3] for m in SEGOVIA_INE_MONTHLY]
    ine_rates = [m.ine_rural_occupancy * 100 for m in SEGOVIA_INE_MONTHLY]
    base_rates = [m.base_occupancy * 100 for m in SEGOVIA_INE_MONTHLY]

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)

    x = np.arange(len(months))
    width = 0.38

    rects1 = ax.bar(x - width / 2, ine_rates, width, label="INE Segovia Rural Tourism Benchmark", color="#94A3B8")
    rects2 = ax.bar(x + width / 2, base_rates, width, label="La Dehesa Target Occupancy Baseline", color="#1E3A8A")

    ax.set_ylabel("Occupancy Rate (%)")
    ax.set_title("Figure 1: Empirical Monthly Seasonality Curve (INE Segovia vs. Asset Baseline)", pad=15, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.set_ylim(0, 65)
    ax.legend(frameon=True, facecolor="white", edgecolor="#E5E7EB")

    # Annotate peak months
    ax.annotate("Summer Peak\n(Jul-Aug: ~50-54%)", xy=(7, 54), xytext=(6.5, 59),
                arrowprops=dict(facecolor="#1E3A8A", shrink=0.05, width=1, headwidth=6),
                ha="center", fontsize=8, fontweight="bold", color="#1E3A8A")

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_dscr_sensitivity_heatmap(save_path: Optional[Path] = None) -> Path:
    """Plots 2D heatmap of DSCR across occupancy and interest rate stress."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_2_dscr_sensitivity_heatmap.png")

    engine = ScenarioEngine(target_dscr=1.25)
    df_matrix = engine.generate_sensitivity_matrix_dscr()

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

    # Custom colormap centered at 1.25 (covenant)
    cmap = sns.diverging_palette(10, 130, s=80, l=55, as_cmap=True)

    sns.heatmap(
        df_matrix,
        annot=True,
        fmt=".2f",
        cmap=cmap,
        center=1.25,
        cbar_kws={"label": "Debt Service Coverage Ratio (DSCR)"},
        linewidths=0.5,
        ax=ax,
    )

    ax.set_title("Figure 2: DSCR Underwriting Sensitivity Matrix (Year 1 Stress Test)", pad=15, fontweight="bold")
    ax.set_xlabel("Senior Mortgage Interest Rate (Euribor + Margin)")
    ax.set_ylabel("Occupancy Demand Multiplier")

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_monte_carlo_distribution(save_path: Optional[Path] = None) -> Path:
    """Plots Monte Carlo probability density of Year 1 DSCR."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_3_monte_carlo_distribution.png")

    sim = MonteCarloSimulator(iterations=1000, random_seed=42)
    df_sim, summary = sim.run_simulation()

    fig, ax = plt.subplots(figsize=(10, 5.0), dpi=300)

    # Histogram with KDE
    sns.histplot(df_sim["dscr_y1"], kde=True, color="#0284C7", bins=35, stat="density", ax=ax, alpha=0.45)

    # Key threshold vertical lines
    ax.axvline(1.25, color="#DC2626", linestyle="--", linewidth=1.8, label=f"Bank Covenant Floor (1.25x) [P(Breach) = {summary.prob_covenant_breach_y1*100:.1f}%]")
    ax.axvline(1.00, color="#7F1D1D", linestyle=":", linewidth=1.8, label=f"Insolvency Floor (1.00x) [P(Default) = {summary.prob_cash_insolvency_y1*100:.1f}%]")
    ax.axvline(summary.median_dscr_y1, color="#0F766E", linestyle="-", linewidth=2.0, label=f"Median DSCR ({summary.median_dscr_y1:.2f}x)")
    ax.axvline(summary.p5_dscr_y1, color="#D97706", linestyle="-.", linewidth=1.5, label=f"VaR 95% 5th Percentile ({summary.p5_dscr_y1:.2f}x)")

    ax.set_title("Figure 3: Monte Carlo Simulation (N=1,000) - Year 1 DSCR Probability Distribution", pad=15, fontweight="bold")
    ax.set_xlabel("Year 1 Debt Service Coverage Ratio (DSCR)")
    ax.set_ylabel("Probability Density")
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#E5E7EB")

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_cash_flow_waterfall(save_path: Optional[Path] = None) -> Path:
    """Plots Year 1 cash flow waterfall showing the impact of the VAT credit correction."""
    set_institutional_style()
    save_path = save_path or (get_assets_dir() / "figure_4_cash_flow_waterfall.png")

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    steps = [
        "Gross Revenue",
        "COGS (F&B)",
        "Labor (Segovia)",
        "Fixed OPEX",
        "EBITDA",
        "Debt Service",
        "VAT Error (-21%)",
        "VAT Correction & Bridge",
        "Net Cash (Solvency)",
    ]

    # Cumulative waterfall logic
    # Initial without VAT bridge vs. with corrected tax credit
    amounts = [154.5, -15.5, -60.1, -12.8, 66.1, -43.5, -152.3, 213.0, 60.8]

    # Calculate bars
    y_pos = np.arange(len(steps))
    colors = [
        "#10B981" if a > 0 else "#EF4444" for a in amounts
    ]
    colors[-1] = "#1E3A8A"  # Final net solvency bar in deep blue
    colors[-3] = "#DC2626"  # Highlight the flawed 21% VAT impact
    colors[-2] = "#059669"  # Highlight the correction

    bars = ax.barh(y_pos, amounts, color=colors, height=0.55, edgecolor="#D1D5DB")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(steps)
    ax.set_xlabel("Cash Flow Impact (€k)")
    ax.set_title("Figure 4: Due Diligence Waterfall - The Critical VAT Correction & Year 1 Solvency Bridge", pad=15, fontweight="bold")
    ax.axvline(0, color="#6B7280", linewidth=0.8)

    for bar, val in zip(bars, amounts):
        sign = "+" if val > 0 else ""
        x_text = val + (3 if val >= 0 else -18)
        ax.text(x_text, bar.get_y() + bar.get_height() / 2, f"{sign}{val:.1f}k €",
                va="center", fontsize=8.5, fontweight="bold")

    ax.set_xlim(-180, 240)
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_all_figures():
    """Generates all 4 institutional figures in /assets."""
    p1 = generate_seasonality_chart()
    p2 = generate_dscr_sensitivity_heatmap()
    p3 = generate_monte_carlo_distribution()
    p4 = generate_cash_flow_waterfall()
    return [p1, p2, p3, p4]


if __name__ == "__main__":
    figs = generate_all_figures()
    for f in figs:
        print(f"Generated figure: {f.name} ({f.stat().st_size / 1024:.1f} KB)")
