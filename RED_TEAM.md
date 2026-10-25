# Red team: seventeen attacks on the Dehesa del Castrillo model

**Purpose.** This memo is the adversarial counterpart to the investment case. It assumes the reader is paid to find the weakest point in the model, not to approve it. Each attack is followed by what the workbook actually says, what I would concede, and what is still unresolved.

**Bottom line.** The red team does not rescue the project. Six attacks make the decline stronger, three expose genuine weaknesses in the reform (external covers, labour and the exit cap), and one is a presentation issue. The three genuine weaknesses are exactly why the recommendation is a low-cost Phase 0 demand test rather than a construction budget.

**Consistency note.** Figures below are the ones produced by the current pipeline (`python main.py`) and locked by the test suite. R6 is pinned to INE 21.24% occupancy and its enterprise value is floored at zero; the operating losses remain in the NPV.

---

## Attack 1: "31.36% occupancy is 48% above the INE. You invented the demand."

**Why it bites.** The official INE Segovia average for 2025 is 21.24% (77.5 occupied days per available room). The management case assumes 31.36%, or 114.5 occupied days. On its face that is a 48% uplift on every night of the year.

**What the model says.** The annual average is a blend of three segments, not a flat uplift:

| Segment | Nights | Management | INE | Gap (pp) |
|---|---:|---:|---:|---:|
| Friday-Saturday weekends | 104 | 72.0% | 48.0% | +6.84 |
| Holiday bridges | 24 | 65.0% | 45.0% | +1.32 |
| Midweek | 237 | 10.1% | 7.1% | +1.97 |
| **Annual** | **365** | **31.36%** | **21.24%** | **+10.12** |

68% of the gap is weekend capture. The midweek assumption is only 3.0 pp above the market. Year 1 is deliberately weaker at 0.90x the mature curve (28.23%).

**Response.** The shape is plausible for a destination boutique with a restaurant: strong weekends, weak Tuesdays. The bridge reconciles exactly to the model's 31.36% and cannot change the P&L. The audit nevertheless fails Rule 10 at 1.48x the INE average, so the case is labelled as an upside, not as a base case.

**Residual risk.** The 72% and 65% anchors are judgement, not measured. There is no booking curve, no competitive set and no OTA pace data. A 60% weekend anchor would cut the annual occupancy to about 27%, below the covenant break-even.

---

## Attack 2: "Your market case reaches 32% anyway, so the downside is not a downside."

**Why it bites.** The INE market case starts at 21.24% but keeps the promoter's 25%/20% volume ramp and 5% nominal growth from Year 4, so it reaches 32.0% by Year 3. If the "downside" reaches the same occupancy as the "upside", the labels are misleading.

**What the model says.** At the official 21.24% in Year 1 the market case produces revenue of €95,555, EBITDA of -€18,566 and a DSCR of -1.46x. It never clears 1.0x within five years. The ramp, not the occupancy anchor, is what lifts it to 32%.

**Response.** The ramp is an assumption inherited from the original Excel and it is disclosed. The market case is a downside on unit economics and debt service, not a claim that demand stays at 21.24% for five years. A stricter version would hold occupancy at 21.24% throughout; that is what R6 does in the reform layer.

**Residual risk.** Mixing an INE starting point with a promoter ramp is a presentation weakness. A reader can reasonably ask for a flat-21.24% as-is case; the reform layer provides the equivalent test.

---

## Attack 3: "You charge €250k for land the family already owns."

**Why it bites.** If the land is contributed in kind, the project does not need to write a cheque for it. Charging it makes the return look worse.

**What the model says.** The land is carried at its opportunity value (€250,000) in both the as-is and reform cases. Total equity at close includes the in-kind land. The sources and uses close only with a cash-equity plug of €521,090 plus the land contribution.

**Response.** The opportunity value is the correct charge. Treating the land as free would turn a family subsidy into a project return and flatter every metric. The model shows the land separately so a reader can strip it out and see the operating business on its own.

**Residual risk.** The €250k is an appraisal assumption, not a binding offer. If the land is worth more, the project is worse, not better.

---

## Attack 4: "An 8.5% cap rate is too low for rural Segovia."

**Why it bites.** Rural hospitality assets in low-density provinces trade at wider yields. A 10-11% cap rate is defensible, and the base case uses 8.5%.

**What the model says.** R6 uses a 10% exit cap. Each +100 bp removes about €76k of gross value. At a 10% cap, R2's enterprise value falls to €713,214 and the net gap versus total investment widens to -€446,808.

**Response.** The 8.5% is a base-case assumption, and the sensitivity is explicit. The conclusion does not depend on it: the case fails at 8.5% and fails by more at 10%.

**Residual risk.** The exit multiple is 11.8x EBITDA at 8.5%, which is high for a rural asset. The model would be stronger with a market-derived cap rate from comparable transactions; none are in the repository.

---

## Attack 5: "Six external F&B covers per day is made up."

**Why it bites.** This is the single largest lever in the reform. It adds €61,320 of mature revenue and €13,698 of EBITDA. There is no evidence in the repository that the estate can attract six external covers a day, especially midweek.

**What the model says.** At six covers, R2 reaches €71,321 of EBITDA and a 2.13x DSCR. At three covers (R6), EBITDA turns negative (-€33,887) and the DSCR is -3.82x.

**Response.** Conceded. The assumption is not proven. That is exactly why the recommendation is not "build it" but "run a Phase 0 pop-up or leased-restaurant test first". The model is a tool to price the test, not a substitute for it.

**Residual risk.** This is the weakest point in the reform. If covers stay below four, the reform does not work at any plausible CapEx.

---

## Attack 6: "One extra FTE cannot serve six covers and breakfast."

**Why it bites.** Six external covers plus up to 21 in-house guests is a full service. One loaded FTE at €28k is a thin labour step-up.

**What the model says.** R2 adds one FTE; R6 adds 1.5. Moving R2 to 1.25-1.5 FTE would reduce EBITDA by roughly €7k-€14k and widen the net gap by the same amount.

**Response.** Conceded as a base-case weakness. The current base is the minimum labour step, not the comfortable one. A 1.5 FTE base would make R2's gap worse but would not change the direction of the conclusion.

**Residual risk.** Labour scheduling, turnover and wage inflation are not modelled. The payroll is part-time and compliant on hourly rates, but coverage risk remains.

---

## Attack 7: "Your Monte Carlo is a naive Gaussian."

**Why it bites.** Hospitality occupancy and ADR are fat-tailed and correlated. A Gaussian simulation understates joint downside.

**What the model says.** The Gaussian Monte Carlo is kept as a benchmark. The copula engine compares Gaussian, Student-t and Clayton dependence. The Clayton 99% CVaR implies a DSRA of €62,786 against the €13,824 contractual reserve.

**Response.** Correct. The copula is the real tail tool, and the DSRA recommendation is six months contractual versus the larger tail-based figure. Using the larger reserve would widen the equity requirement.

**Residual risk.** The copula marginals are still calibrated assumptions. It is a better tail model, not a validated one.

---

## Attack 8: "Unlevered NPV understates the equity case; leverage can rescue it."

**Why it bites.** Project NPV ignores the option value of leverage and the equity upside.

**What the model says.** The DSCR covenant caps the facility at €339,145 against the €367,535 requested. R2's equity IRR is 1.96%; R4's is 10.16% but only on the unproven eight-cover corner. The project does not earn its 8% cost of capital at the operating level.

**Response.** Leverage does not create value when the asset yield is below the cost of debt. It can magnify a positive spread, not manufacture one. The equity returns confirm the point: R2's equity IRR is below the project IRR.

**Residual risk.** A different capital stack (mezzanine, grant equity, deferred land payment) could change the equity outcome, but it would not change the asset-level value gap.

---

## Attack 9: "You double-count the grant and ignore VAT timing."

**Why it bites.** The LEADER grant and the VAT refund are both public-money inflows. If they fund the same costs twice, the funding stack is overstated.

**What the model says.** The grant is a capital source (€162,766 in R2), not revenue. The VAT bridge is a separate €175,000 facility drawn on CapEx VAT, repaid with the AEAT refund in Month 18, and it carries interest. The Phase II gate tests the double-spend and returns `DO NOT PROCEED`.

**Response.** There is no double count in the funding model. The grant reduces equity, the VAT bridge is temporary liquidity, and the phase gate is the control that stops the two being spent twice.

**Residual risk.** There is no award letter in the repository. The grant is treated as committed at Month 14/Year 2; the no-grant stress costs €119,838 of NPV.

---

## Attack 10: "A Year-5 exit at 11.8x EBITDA dominates the result."

**Why it bites.** The terminal value is large relative to the operating cash flows. A small change in the cap rate swings the IRR.

**What the model says.** Without an exit, the management project IRR is -35.43%. With an 8.5% exit it is -9.49%. The exit makes the failure smaller, not successful. The net-of-cost test is shown separately (3% of value; 4% in R6).

**Response.** The exit is a test, not a rescue. Both with and without exit are reported. The cap rate is stressed to 10% in R6, and the net proceeds are shown next to the gross value.

**Residual risk.** The terminal value still assumes a functioning sale market in Year 5. A forced sale or a distressed cap rate would produce a worse outcome than the base case.

---

## R7: five more attacks, because the cabin case actually passes

R7 is the only configuration in the workbook that clears both the WACC and the net total-investment test. That makes it the case a credit committee would attack hardest, not the one it would wave through.

## Attack 11: "€110k all-in per cabin is a catalogue price, not a hospitality unit."

**Why it bites.** If the real all-in cost is €130k, the net gap turns to -€87,672 and the case fails. The base is only 3.2% above water.

**What the model says.** The cost ladder is explicit: €110k passes (+€49,147), €120k fails (-€19,263), €130k fails (-€87,672), €150k fails (-€224,490) and €180k fails (-€429,718). The €110k is not a shell price; it includes the fitted unit, the deck, services and the share of common infrastructure. The benchmark note separates the €17-37k shell from the €85-110k installed standard package and the €130-150k premium one.

**Response.** The base is deliberately set at the top of the standard corridor, not the middle of the premium one. The recommendation does not say "build at €110k"; it says "run the Phase 0 test, then get a binding quote at or below €110k".

**Residual risk.** A QS quote at €125-135k is entirely plausible in 2026. If it arrives, the correct move is to cut a cabin or the restaurant scope, not to raise the ADR.

## Attack 12: "€200 ADR for a cabin in Segovia is optimistic."

**Why it bites.** The local OTA sample averages €236/night but spans €85-520; the median is far below the mean, and the €200 figure is an annual realised rate, not a peak weekend rate.

**What the model says.** At €190 ADR with 50% occupancy the net gap is -€39,932. At €200 it is +€49,147. The case lives inside a €10-20 band around the realised rate. The stretch case needs €230 and 55% occupancy, and the note explicitly says €250+ is not supported.

**Response.** The €200 is triangulated from three sources (OTA sample, rural house rates per person, glamping operator bands), not from a single listing. The downside runs €190.

**Residual risk.** If the realised rate settles at €185-190, R7 fails even at €110k. That is exactly what the Phase 0 test is for.

## Attack 13: "€45k of agronomic experiences is a story, not a revenue line."

**Why it bites.** €45k is 7.9% of total revenue and carries a 70% margin, so it contributes disproportionately to EBITDA. If it is really €25k, the net gap falls by roughly €14k and the base stops passing.

**What the model says.** The note builds the €45k two ways: 30 retreats × 12 people × €125, or 300 experiences × €150, which is a 27% attach on 1,095 cabin nights. The downside uses €25k.

**Response.** Experiences are modelled with an explicit host, calendar and marketing cost inside the 4.5 FTE and the fixed OPEX, not as passive income. The Phase 0 gate includes the realised attach rate.

**Residual risk.** A 27% attach is demanding for a first season. The case should be re-run at 15-20% attach before any construction commitment.

## Attack 14: "Six cabins is four too many for a first phase."

**Why it bites.** Building all six before proving demand turns a €50k option into a €1.54M commitment. The downside case (five cabins) still loses €989k.

**What the model says.** Five cabins at €110k with €45k of experiences clears the asset test (+€49,987) but fails total investment (-€29,183). The sixth cabin is what makes the case pass, because it adds ~€21k of EBITDA for €110k of CapEx, a 19% yield on cost.

**Response.** The recommendation is explicitly two-stage: Phase 0 proves demand with two cabins plus the house, and only then does the sixth cabin get built. The model prices the full configuration; the recommendation does not authorise it in one go.

**Residual risk.** A staged build carries its own cost premium and loses the scale economies assumed in the common infrastructure.

## Attack 15: "You charge €250k for land the family already owns, so the result is not the family's return."

**Why it bites.** The return that matters to the family is the cash it actually puts in. If the land is contributed in kind and never paid for, the equity cheque is smaller and the family IRR is higher than the project IRR.

**What the model says.** The €250k is in every R7 metric, including the €110k base. Removing it would add roughly €250k to the value gap and make the case look better, not worse: R7 passes *with* the land charged. The project test is deliberately the whole-asset test, because a bank lends against the whole asset and the land has an opportunity value (it could be sold or leased).

**Response.** The land stays in, and the equity cash-flow view is reported separately. The case does not pass by pretending the site is free; the family can still see a better family-only return if it wants to, but that is not the same decision.

**Residual risk.** The €250k is an internal opportunity value, not an appraisal. A formal valuation could move it in either direction, and with it the size of the gap.

## Attack 16: "Your entire +€49k gap is 30 basis points of cap compression."

**Why it bites.** The development yield on cost is 10.11% and the exit cap is 9.50%. The break-even exit cap is 9.80%, so the case clears by 30bp. At no compression the net gap is -€46,223, which is exactly the 3% exit-cost bill. The "profit" is the spread between what it costs to build and the cap rate at which it is sold.

**What the model says.** The valuation cross-check reports the yield on cost, the break-even cap and the no-compression case next to the headline gap. The multiple table is explicit: at 9.0x the net gap is -€181,390, at 10.5x it is +€45,172 and at 12.0x it is +€271,733. The base sits at 10.53x, so it needs the exit to happen at a tighter yield than the build cost implies.

**Response.** The gap is labelled as a development spread, not as operating value creation. The 9.5% exit cap is already the central case, not an aggressive one, and the Phase 0 gate includes a local valuer's opinion before any construction capital is committed. If the valuer clears 9.8% or better, the case survives; if not, it does not.

**Residual risk.** Rural Segovia cap rates for a six-key cabin operation could sit at 10.0-10.5%. At 10.5% R7 fails even with a €110k cabin, and no amount of ADR fixes a cap-rate problem.

## Attack 17: "You model five years of flat costs. Where is inflation?"

**Why it bites.** Payroll, energy and maintenance do not stay flat for five years. If real costs grow 2% a year while the ADR stays flat, the net gap falls from +€49,147 to -€142,819. At 2.5% it is -€192,609 and at 3% it is -€243,134. The base has no room for a real cost-price gap.

**What the model says.** The reform and R7 layers are in constant 2026 euros on both sides: ADR, payroll and OPEX are flat. That is internally consistent, and it is disclosed. The cost-inflation stress deliberately breaks the symmetry to isolate the margin squeeze, because a full nominal model would need indexed revenue and a nominal WACC; indexing revenue alone would flatter the terminal value against a CapEx spent at t=0.

**Response.** The stress is reported as a scenario, not a forecast, and the base conclusion is not allowed to depend on costs staying flat forever. The Phase 0 gate should include a payroll and energy quote, and the family should treat the 3.2% margin as contingent on holding the real cost base.

**Residual risk.** If payroll and energy outrun ADR by 2% a year, R7 fails at any cabin cost in the corridor. That is a structural margin problem, not a construction problem.

---

## What would change the verdict

The decline is robust to the attacks above, but it is not unfalsifiable. Three pieces of evidence would force a re-run:

1. **A signed Phase 0 demand test** showing at least four external covers per day, sustained across weekdays, with a menu and price point that clear the assumed €28 ticket.
2. **A binding construction quote at or below €900k** for the lean scope, with a QS report and a contingency that survives a 20% overrun.
3. **A LEADER award letter** with a disbursement date, plus a debt term sheet sized to the DSCR cap rather than 35% LTV.

Even with all three, R2 would still need a cap rate below roughly 7.2% to clear the total-investment test at €71,321 of EBITDA. That is not a rural Segovia cap rate. The honest conclusion is that the project is a **Phase 0 option**, not a construction project.

For R7 the list is different and narrower: a signed Phase 0 season at 45% occupancy, €190 realised ADR, eight external covers a day and €25k of experiences, plus a binding all-in cabin quote at or below €110k. If the occupancy gate fails, the case is dead regardless of the ADR; if the cost gate fails, the answer is fewer cabins or a smaller restaurant, not a higher price. Two further conditions are now explicit: a valuer's exit cap at or below 9.8%, and a real cost-price gap no worse than 1% a year.

---

## Open issues I have not resolved

- The weekend and holiday occupancy anchors are judgement, not measured.
- The INE segment split is inferred from the annual average, not published.
- The external-cover demand has no competitive set or daypart build-up.
- Labour is at the minimum step, not the comfortable one.
- The exit cap rate is not supported by comparable transactions.
- R6's zero enterprise value is an accounting floor, not a liquidation analysis.
- The rate sensitivity is a fixed-rate re-run, not a refinancing model.
- R7's €45k experience revenue has no signed programme, only a build-up.
- R7's €110k all-in cabin cost is a benchmark, not a contractor quote.
- R7 passes on a 30bp cap-rate spread and a flat real cost base; both are assumptions, not evidence.

These are listed in the README's limitations section. They are not hidden in an appendix.
