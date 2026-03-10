"""
Orchestrator Integration Shim
==============================
Drop-in adapter that lets the Business Impact Calculator agent run
as a node inside a multi-agent orchestrator (e.g. alongside Legal Risk,
Architecture Review, and Confidence Risk agents).

The orchestrator calls `run_agent_node(payload)` and receives a
standardized `AgentNodeResult` that every agent in the system produces.

Example orchestrator pipeline
------------------------------
    from orchestrator_integration import run_agent_node

    idea = "Add one-click upsell on checkout confirmation page"

    # Run agents in parallel
    results = await asyncio.gather(
        legal_agent.run_agent_node({"idea": idea}),
        architecture_agent.run_agent_node({"idea": idea}),
        business_impact_agent.run_agent_node({"idea": idea}),   # <-- this module
    )

    final_verdict = synthesise_results(results)
"""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel

from agent import run_business_impact_agent
from models import BusinessImpactReport


class AgentNodeResult(BaseModel):
    """Standardised envelope returned by every agent in the orchestrator."""

    agent_id: str = "business_impact_calculator"
    agent_version: str = "1.0.0"
    status: str           # "success" | "error"
    payload: dict[str, Any] | None = None
    error: str | None = None

    # Convenience fields for the orchestrator's routing / ranking logic
    recommendation: str | None = None    # mirrors BusinessImpactReport.overall_recommendation
    confidence: float | None = None      # mirrors BusinessImpactReport.confidence_score
    expected_value_usd: float | None = None


async def run_agent_node(
    orchestrator_payload: dict[str, Any],
) -> AgentNodeResult:
    """
    Entry point called by the orchestrator.

    Parameters
    ----------
    orchestrator_payload:
        Must contain at minimum:
            "idea": str  — the raw product idea to evaluate
        Optional keys:
            "context": dict — extra metadata from other agents or the PM

    Returns
    -------
    AgentNodeResult
    """
    idea = orchestrator_payload.get("idea", "")
    context = orchestrator_payload.get("context", {})

    if not idea:
        return AgentNodeResult(
            status="error",
            error="orchestrator_payload must include a non-empty 'idea' key",
        )

    try:
        report: BusinessImpactReport = await run_business_impact_agent(
            idea=idea,
            context=context,
        )
        return AgentNodeResult(
            status="success",
            payload=report.model_dump(),
            recommendation=report.overall_recommendation,
            confidence=report.confidence_score,
            expected_value_usd=report.total_expected_value_usd,
        )
    except Exception as exc:
        return AgentNodeResult(
            status="error",
            error=str(exc),
        )


# Quick sanity-check when run directly
if __name__ == "__main__":
    result = asyncio.run(
        run_agent_node({
            "idea": "Introduce a freemium tier with usage-based caps to expand the top of funnel.",
            "context": {
                "source": "product_roadmap_q3",
                "priority": "high",
                "estimated_implementation_cost_usd": 80_000,
            },
        })
    )
    print(result.model_dump_json(indent=2))
