"""
Occupancy bridge: reconciles the management case with the INE average.

The management case is often read as "31.36% occupancy versus an INE average of
21.24%", which sounds like a flat 48% uplift on every night. It is not. The
management case is a weekend-weighted boutique mix: high weekend and holiday
occupancy, very low midweek. This module makes that mix explicit and shows how
much of the gap comes from each segment.

The bridge is deliberately an annual average, not a month-by-month model. The
monthly seasonality already lives in ``src.config.ine_weights``; this module
answers a narrower question: if the hotel sells 72% of its weekend nights and
65% of its holiday nights, what midweek occupancy is implied by the annual
target, and how does that compare with the INE market?

The answer matters for two reasons:

1. It shows that the management case is a premium weekend story, not a
   "we fill every day" story. That is more defensible for a boutique with a
   restaurant, but it is still an upside assumption.
2. It exposes the midweek hole. The reform case's external F&B covers are an
   attempt to fill exactly that hole, which is why the Phase 0 demand test is
   the gating item.
"""

from dataclasses import dataclass
from typing import Dict, List

from src.config.ine_weights import MANAGEMENT_OCCUPANCY, MARKET_OCCUPANCY


# Calendar split used by the bridge. 52 weekends give 104 Friday/Saturday
# nights; 24 holiday-bridge nights cover the main Spanish long weekends; the
# remaining 237 nights are midweek. The counts are assumptions, not data, but
# they are stable and easy to audit.
WEEKEND_NIGHTS = 104
PEAK_NIGHTS = 24
MIDWEEK_NIGHTS = 237
TOTAL_NIGHTS = WEEKEND_NIGHTS + PEAK_NIGHTS + MIDWEEK_NIGHTS
UNITS = 8


@dataclass(frozen=True)
class OccupancySegment:
    key: str
    label: str
    nights: int
    occupancy: float

    @property
    def occupied_nights(self) -> float:
        """Occupied nights per available room."""
        return self.nights * self.occupancy

    @property
    def occupied_room_nights(self) -> float:
        """Occupied room-nights across the whole property."""
        return self.occupied_nights * UNITS


@dataclass(frozen=True)
class OccupancyMix:
    name: str
    target_occupancy: float
    weekend_occupancy: float
    peak_occupancy: float
    midweek_occupancy: float

    @property
    def segments(self) -> List[OccupancySegment]:
        return [
            OccupancySegment(
                key="weekend",
                label="Fri-Sat weekends",
                nights=WEEKEND_NIGHTS,
                occupancy=self.weekend_occupancy,
            ),
            OccupancySegment(
                key="peak",
                label="Holiday bridges",
                nights=PEAK_NIGHTS,
                occupancy=self.peak_occupancy,
            ),
            OccupancySegment(
                key="midweek",
                label="Midweek",
                nights=MIDWEEK_NIGHTS,
                occupancy=self.midweek_occupancy,
            ),
        ]

    @property
    def occupied_nights(self) -> float:
        """Occupied nights per available room, annual."""
        return sum(segment.occupied_nights for segment in self.segments)

    @property
    def occupancy(self) -> float:
        return self.occupied_nights / TOTAL_NIGHTS

    @property
    def occupied_room_nights(self) -> float:
        return self.occupied_nights * UNITS

    def as_dict(self) -> Dict[str, float]:
        return {
            "name": self.name,
            "target_occupancy": self.target_occupancy,
            "modelled_occupancy": self.occupancy,
            "occupied_nights": self.occupied_nights,
            "occupied_room_nights": self.occupied_room_nights,
            "weekend_occupancy": self.weekend_occupancy,
            "peak_occupancy": self.peak_occupancy,
            "midweek_occupancy": self.midweek_occupancy,
        }


def solve_midweek_occupancy(
    target_occupancy: float,
    weekend_occupancy: float,
    peak_occupancy: float,
) -> float:
    """
    Solves the midweek occupancy that makes the three-segment mix hit the
    annual target. Raises if the weekend and holiday anchors already exceed the
    target, because that would imply negative midweek demand.
    """
    target_nights = target_occupancy * TOTAL_NIGHTS
    anchored = (
        WEEKEND_NIGHTS * weekend_occupancy + PEAK_NIGHTS * peak_occupancy
    )
    remaining = target_nights - anchored
    if remaining < 0:
        raise ValueError(
            "Weekend and peak occupancy already exceed the annual target; "
            "lower the anchors or raise the target."
        )
    midweek = remaining / MIDWEEK_NIGHTS
    if midweek > 1.0:
        raise ValueError("Implied midweek occupancy exceeds 100%.")
    return midweek


def build_mix(
    name: str,
    target_occupancy: float,
    weekend_occupancy: float,
    peak_occupancy: float,
) -> OccupancyMix:
    midweek = solve_midweek_occupancy(
        target_occupancy, weekend_occupancy, peak_occupancy
    )
    return OccupancyMix(
        name=name,
        target_occupancy=target_occupancy,
        weekend_occupancy=weekend_occupancy,
        peak_occupancy=peak_occupancy,
        midweek_occupancy=midweek,
    )


# Management case: premium weekend capture, holiday bridges and a very thin
# midweek. The 72% weekend and 65% holiday anchors are judgement calls; the
# midweek is solved so the mix reconciles to the model's 31.36%.
MANAGEMENT_MIX = build_mix(
    name="Management case (upside)",
    target_occupancy=MANAGEMENT_OCCUPANCY,
    weekend_occupancy=0.72,
    peak_occupancy=0.65,
)

# INE market: the same calendar, weaker weekend and holiday capture. The
# implied midweek is solved so the mix reconciles to 21.24%.
INE_MIX = build_mix(
    name="INE Segovia market",
    target_occupancy=MARKET_OCCUPANCY,
    weekend_occupancy=0.48,
    peak_occupancy=0.45,
)


def build_bridge() -> Dict[str, object]:
    """Returns the management-vs-INE occupancy bridge and its decomposition."""
    management = MANAGEMENT_MIX
    market = INE_MIX
    gap_pp = (management.occupancy - market.occupancy) * 100.0

    contributions = {}
    for mgmt_segment, mkt_segment in zip(management.segments, market.segments):
        contributions[mgmt_segment.key] = round(
            mgmt_segment.nights
            * (mgmt_segment.occupancy - mkt_segment.occupancy)
            / TOTAL_NIGHTS
            * 100.0,
            2,
        )

    total_gap = sum(contributions.values())
    shares = {
        key: round(value / total_gap, 4) if total_gap else 0.0
        for key, value in contributions.items()
    }

    return {
        "management": management.as_dict(),
        "market": market.as_dict(),
        "gap_pp": round(gap_pp, 2),
        "gap_contributions_pp": contributions,
        "gap_shares": shares,
        "calendar": {
            "weekend_nights": WEEKEND_NIGHTS,
            "peak_nights": PEAK_NIGHTS,
            "midweek_nights": MIDWEEK_NIGHTS,
            "units": UNITS,
        },
        "headline": (
            f"{shares['weekend'] * 100:.0f}% of the {gap_pp:.1f} pp occupancy "
            "gap is weekend capture, not midweek demand. The midweek is thin in "
            "both cases; the reform's external F&B covers are an attempt to "
            "fill it."
        ),
    }


if __name__ == "__main__":
    bridge = build_bridge()
    print("OCCUPANCY BRIDGE - MANAGEMENT vs INE SEGOVIA")
    print("-" * 88)
    print(f"Calendar: {WEEKEND_NIGHTS} weekend, {PEAK_NIGHTS} holiday, {MIDWEEK_NIGHTS} midweek nights")
    print()
    print(f"{'Segment':<20}{'Nights':>8}{'Management':>14}{'INE':>10}{'Gap (pp)':>12}")
    for mgmt_segment, mkt_segment in zip(MANAGEMENT_MIX.segments, INE_MIX.segments):
        print(
            f"{mgmt_segment.label:<20}{mgmt_segment.nights:>8}"
            f"{mgmt_segment.occupancy*100:>13.1f}%"
            f"{mkt_segment.occupancy*100:>9.1f}%"
            f"{bridge['gap_contributions_pp'][mgmt_segment.key]:>12.2f}"
        )
    print("-" * 88)
    print(f"{'Annual':<20}{TOTAL_NIGHTS:>8}{MANAGEMENT_MIX.occupancy*100:>13.2f}%{INE_MIX.occupancy*100:>9.2f}%{bridge['gap_pp']:>12.2f}")
    print()
    print(bridge["headline"])
