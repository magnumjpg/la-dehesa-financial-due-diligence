"""
Senior Debt amortization engine (French amortization system).

Calculates monthly and annual amortization schedules, tracking:
- Beginning balance
- Regular installment (cuota constante)
- Principal repayment
- Interest expense
- Ending balance
- Year-end current vs. non-current debt classification for the Balance Sheet
"""

from dataclasses import dataclass
from typing import List
import pandas as pd


@dataclass(frozen=True)
class LoanPeriod:
    period_month: int
    year: int
    beginning_balance: float
    payment: float
    principal: float
    interest: float
    ending_balance: float


class DebtAmortizationEngine:
    """
    Computes French system loan amortization (fixed periodic payment).
    Formula:
        PMT = P * [ r*(1+r)^n ] / [ (1+r)^n - 1 ]
    where:
        P = principal
        r = periodic interest rate (annual_rate / 12)
        n = total number of monthly payments (years * 12)
    """

    def __init__(
        self,
        principal: float = 507_500.0,
        annual_interest_rate: float = 0.035,
        tenure_years: int = 15,
    ):
        self.principal = principal
        self.annual_interest_rate = annual_interest_rate
        self.tenure_years = tenure_years
        self.total_periods = tenure_years * 12
        self.monthly_rate = annual_interest_rate / 12.0

        if self.monthly_rate > 0:
            factor = (1.0 + self.monthly_rate) ** self.total_periods
            self.monthly_payment = principal * (self.monthly_rate * factor) / (factor - 1.0)
        else:
            self.monthly_payment = principal / self.total_periods

    def generate_monthly_schedule(self) -> List[LoanPeriod]:
        """Generates full monthly amortization table."""
        schedule: List[LoanPeriod] = []
        balance = self.principal

        for month in range(1, self.total_periods + 1):
            year = (month - 1) // 12 + 1
            interest = round(balance * self.monthly_rate, 2)
            payment = self.monthly_payment

            # Handle last period precision
            if month == self.total_periods or balance + interest <= payment:
                principal = balance
                payment = principal + interest
                ending_balance = 0.0
            else:
                principal = round(payment - interest, 2)
                ending_balance = round(balance - principal, 2)

            schedule.append(
                LoanPeriod(
                    period_month=month,
                    year=year,
                    beginning_balance=round(balance, 2),
                    payment=round(payment, 2),
                    principal=principal,
                    interest=interest,
                    ending_balance=ending_balance,
                )
            )
            balance = ending_balance

        return schedule

    def get_monthly_schedule_df(self) -> pd.DataFrame:
        schedule = self.generate_monthly_schedule()
        data = [
            {
                "month": p.period_month,
                "year": p.year,
                "beginning_balance": p.beginning_balance,
                "payment": p.payment,
                "principal": p.principal,
                "interest": p.interest,
                "ending_balance": p.ending_balance,
            }
            for p in schedule
        ]
        return pd.DataFrame(data)

    def get_annual_schedule_df(self) -> pd.DataFrame:
        """Aggregates monthly debt schedule by year."""
        m_df = self.get_monthly_schedule_df()
        annual_records = []

        for year, group in m_df.groupby("year"):
            beg_bal = group.iloc[0]["beginning_balance"]
            end_bal = group.iloc[-1]["ending_balance"]
            tot_payment = group["payment"].sum()
            tot_principal = group["principal"].sum()
            tot_interest = group["interest"].sum()

            # Next 12 months principal (current debt liability for balance sheet)
            next_year_group = m_df[m_df["year"] == year + 1]
            short_term_debt = next_year_group["principal"].sum() if not next_year_group.empty else end_bal
            long_term_debt = max(0.0, end_bal - short_term_debt)

            annual_records.append(
                {
                    "year": int(year),
                    "beginning_balance": round(beg_bal, 2),
                    "payment": round(tot_payment, 2),
                    "principal": round(tot_principal, 2),
                    "interest": round(tot_interest, 2),
                    "ending_balance": round(end_bal, 2),
                    "short_term_debt": round(short_term_debt, 2),
                    "long_term_debt": round(long_term_debt, 2),
                }
            )

        return pd.DataFrame(annual_records)
