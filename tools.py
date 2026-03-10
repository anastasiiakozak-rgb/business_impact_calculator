"""
Tool definitions for the Business Impact Calculator agent.

In production, these tools would connect to real data sources
(analytics platforms, revenue databases, A/B test history).
The stubs here demonstrate the interface contract so the agent
knows what data it can request and what format it will receive.
"""

from __future__ import annotations

import json
from typing import Any

# ---------------------------------------------------------------------------
# Tool schemas (passed to the Claude API in the `tools` list)
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_baseline_metrics",
        "description": (
            "Retrieve current baseline business metrics for the product. "
            "Returns key KPIs such as conversion rate, ARPU, DAU/MAU, "
            "churn rate, CAC, LTV and monthly revenue that the impact "
            "calculation should be based on."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment": {
                    "type": "string",
                    "description": (
                        "Optional product/user segment to scope the metrics, "
                        "e.g. 'checkout_funnel', 'premium_users', 'mobile'. "
                        "Leave empty for company-wide metrics."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "estimate_conversion_impact",
        "description": (
            "Estimate the impact on conversion rate (CR) for a given change. "
            "Returns a delta range (low/mid/high) based on comparable historical "
            "experiments and the type of change described."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "change_description": {
                    "type": "string",
                    "description": "Short description of the UX or product change being evaluated.",
                },
                "funnel_stage": {
                    "type": "string",
                    "description": "Which funnel stage is affected, e.g. 'awareness', 'activation', 'checkout', 'retention'.",
                },
                "change_type": {
                    "type": "string",
                    "enum": ["ux_simplification", "new_feature", "pricing_change", "content_change", "removal"],
                    "description": "Category of change.",
                },
            },
            "required": ["change_description", "funnel_stage", "change_type"],
        },
    },
    {
        "name": "check_cannibalization_risk",
        "description": (
            "Analyse whether the proposed idea risks cannibalising revenue from "
            "existing features, products, or customer segments. Returns overlap "
            "analysis and estimated revenue-at-risk from cannibalisation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "idea_description": {
                    "type": "string",
                    "description": "Full description of the idea being evaluated.",
                },
                "affected_features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of existing features or products that could be cannibalised.",
                },
            },
            "required": ["idea_description"],
        },
    },
    {
        "name": "calculate_revenue_delta",
        "description": (
            "Given a set of metric changes (e.g. CR +2%, ARPU +$5), calculate "
            "the net annual and monthly revenue delta in USD. Uses the baseline "
            "metrics automatically; you only need to supply the deltas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric_deltas": {
                    "type": "array",
                    "description": "List of metric changes to model.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "metric": {
                                "type": "string",
                                "description": "Metric name, e.g. 'conversion_rate', 'arpu', 'churn_rate'.",
                            },
                            "delta_percent": {
                                "type": "number",
                                "description": "Percentage change (positive = increase, negative = decrease).",
                            },
                        },
                        "required": ["metric", "delta_percent"],
                    },
                },
                "scenario": {
                    "type": "string",
                    "enum": ["optimistic", "base_case", "pessimistic"],
                    "description": "Which scenario to model.",
                },
            },
            "required": ["metric_deltas", "scenario"],
        },
    },
    {
        "name": "lookup_comparable_experiments",
        "description": (
            "Search historical A/B tests and product launches for experiments "
            "similar to the proposed idea. Returns outcome summaries, confidence "
            "intervals, and lessons learned to calibrate the current estimate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "idea_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords describing the idea, e.g. ['checkout', 'one-click', 'upsell'].",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of comparable experiments to return.",
                    "default": 5,
                },
            },
            "required": ["idea_keywords"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution stubs
# In production, replace each stub with a real data source call.
# ---------------------------------------------------------------------------

def execute_tool(name: str, tool_input: dict[str, Any]) -> str:
    """Dispatch a tool call and return the result as a JSON string."""
    handlers = {
        "get_baseline_metrics": _get_baseline_metrics,
        "estimate_conversion_impact": _estimate_conversion_impact,
        "check_cannibalization_risk": _check_cannibalization_risk,
        "calculate_revenue_delta": _calculate_revenue_delta,
        "lookup_comparable_experiments": _lookup_comparable_experiments,
    }
    handler = handlers.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    return json.dumps(handler(tool_input))


# --- stubs ------------------------------------------------------------------

def _get_baseline_metrics(inp: dict) -> dict:
    """
    STUB: Returns representative SaaS baseline metrics.
    Replace with a real analytics / data-warehouse query.
    """
    segment = inp.get("segment", "company-wide")
    return {
        "segment": segment,
        "monthly_active_users": 250_000,
        "monthly_revenue_usd": 1_800_000,
        "conversion_rate_percent": 3.2,          # visitor → paid
        "arpu_usd": 72,                           # average revenue per user/month
        "churn_rate_percent": 2.1,               # monthly churn
        "cac_usd": 95,                            # customer acquisition cost
        "ltv_usd": 3_428,                         # lifetime value
        "trial_to_paid_rate_percent": 18.5,
        "nps_score": 42,
        "note": "Stub data — replace with real analytics API call in production.",
    }


def _estimate_conversion_impact(inp: dict) -> dict:
    """
    STUB: Returns plausible CR impact ranges by change type.
    Replace with a model trained on historical experiment data.
    """
    change_type = inp.get("change_type", "new_feature")
    funnel_stage = inp.get("funnel_stage", "checkout")

    impact_table = {
        "ux_simplification":  {"low": -0.5, "mid": +2.1, "high": +5.0},
        "new_feature":        {"low": -1.0, "mid": +0.8, "high": +3.5},
        "pricing_change":     {"low": -8.0, "mid": -2.0, "high": +4.0},
        "content_change":     {"low": -0.3, "mid": +0.5, "high": +1.8},
        "removal":            {"low": -3.0, "mid": -0.5, "high": +1.0},
    }
    deltas = impact_table.get(change_type, {"low": -1.0, "mid": +0.5, "high": +2.0})

    return {
        "funnel_stage": funnel_stage,
        "change_type": change_type,
        "cr_delta_percent": deltas,
        "confidence": 0.60,
        "methodology": "Comparable historical A/B tests (stub)",
        "note": "Stub data — replace with experiment-history model in production.",
    }


def _check_cannibalization_risk(inp: dict) -> dict:
    """
    STUB: Returns a cannibalization risk assessment.
    Replace with feature-overlap analysis against your product catalogue.
    """
    return {
        "cannibalization_detected": True,
        "at_risk_revenue_usd_annual": 140_000,
        "overlap_features": inp.get("affected_features", ["existing premium feature"]),
        "overlap_percent": 18,
        "severity": "medium",
        "explanation": (
            "Estimated 18 % of users who would adopt the new feature "
            "are currently paying for an overlapping premium add-on. "
            "Annual revenue at risk: ~$140 k."
        ),
        "note": "Stub data — replace with product-catalogue overlap query in production.",
    }


def _calculate_revenue_delta(inp: dict) -> dict:
    """
    STUB: Projects revenue delta from metric changes.
    Replace with a proper financial model connected to baseline metrics.
    """
    baseline_monthly = 1_800_000
    deltas = inp.get("metric_deltas", [])
    scenario = inp.get("scenario", "base_case")

    # Simplistic combined-multiplier approach for demo purposes
    multiplier = 1.0
    for d in deltas:
        multiplier *= 1 + (d.get("delta_percent", 0) / 100)

    monthly_delta = baseline_monthly * (multiplier - 1)
    annual_delta = monthly_delta * 12

    scenario_haircuts = {"optimistic": 1.4, "base_case": 1.0, "pessimistic": 0.45}
    annual_delta *= scenario_haircuts.get(scenario, 1.0)

    return {
        "scenario": scenario,
        "monthly_revenue_delta_usd": round(monthly_delta, 2),
        "annual_revenue_delta_usd": round(annual_delta, 2),
        "metric_deltas_applied": deltas,
        "note": "Stub — replace with real financial model in production.",
    }


def _lookup_comparable_experiments(inp: dict) -> dict:
    """
    STUB: Returns synthetic comparable experiment history.
    Replace with a query to your experimentation platform (e.g. Statsig, Optimizely, LaunchDarkly).
    """
    keywords = inp.get("idea_keywords", [])
    return {
        "query_keywords": keywords,
        "experiments": [
            {
                "name": "Checkout simplification v2 (2023-Q3)",
                "outcome": "+2.4 % CR, +$210 k ARR",
                "confidence": "95 %",
                "lesson": "Reducing form fields had outsized impact vs visual changes.",
            },
            {
                "name": "One-click upsell modal (2023-Q1)",
                "outcome": "-1.1 % CR due to modal fatigue, +0.9 % ARPU net positive",
                "confidence": "90 %",
                "lesson": "Upsells at high-intent moments convert; interstitial upsells hurt CR.",
            },
            {
                "name": "Premium feature gate removal (2022-Q4)",
                "outcome": "+5.0 % trial-to-paid, -12 % ARPU — net negative",
                "confidence": "88 %",
                "lesson": "Free-tier expansion drives volume but erodes unit economics.",
            },
        ],
        "note": "Stub data — replace with your experimentation platform API in production.",
    }
