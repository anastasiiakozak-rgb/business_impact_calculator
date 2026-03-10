from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskItem(BaseModel):
    risk_type: str = Field(description="Type of risk, e.g. 'CR drop', 'Cannibalization', 'Churn increase'")
    description: str = Field(description="Detailed explanation of the risk")
    severity: RiskSeverity
    estimated_impact_usd: Optional[float] = Field(
        default=None,
        description="Estimated annual revenue impact in USD (negative = loss)",
    )
    probability: float = Field(
        ge=0.0, le=1.0, description="Probability this risk materializes (0–1)"
    )
    mitigation: str = Field(description="Suggested mitigation strategy")


class MetricImpact(BaseModel):
    metric_name: str = Field(description="e.g. 'Conversion Rate', 'ARPU', 'CAC', 'LTV'")
    current_value: Optional[float] = Field(default=None, description="Current baseline value")
    projected_value: Optional[float] = Field(default=None, description="Projected value after change")
    delta_percent: Optional[float] = Field(
        default=None, description="% change relative to current value"
    )
    direction: str = Field(description="'positive', 'negative', or 'neutral'")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in this projection (0–1)"
    )
    notes: str


class RevenueProjection(BaseModel):
    timeframe_months: int = Field(description="Projection horizon in months")
    base_case_usd: float = Field(description="Expected revenue delta in USD")
    optimistic_case_usd: float = Field(description="Upside scenario revenue delta in USD")
    pessimistic_case_usd: float = Field(description="Downside scenario revenue delta in USD")
    payback_period_months: Optional[int] = Field(
        default=None, description="Months to recoup implementation cost, if applicable"
    )
    assumptions: List[str] = Field(description="Key assumptions behind the projection")


class BusinessImpactReport(BaseModel):
    idea_summary: str = Field(description="One-sentence summary of the evaluated idea")
    overall_recommendation: str = Field(
        description="'proceed', 'proceed_with_caution', 'requires_validation', or 'do_not_proceed'"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence in this analysis (0–1)",
    )
    revenue_projection: RevenueProjection
    metric_impacts: List[MetricImpact]
    risks: List[RiskItem]
    total_expected_value_usd: float = Field(
        description="Probability-weighted net revenue impact in USD (annual)"
    )
    key_unknowns: List[str] = Field(
        description="Critical unknowns that would change the analysis significantly"
    )
    suggested_experiments: List[str] = Field(
        description="A/B tests or validation steps before full rollout"
    )
    analyst_notes: str = Field(
        description="Qualitative commentary from the agent on the most important factors"
    )
