"""
Business Impact Calculator Agent
=================================
Evaluates a raw product idea and returns a structured financial impact
report — revenue projections, metric deltas, and risk flags (CR drop,
cannibalization, churn, etc.).

This agent is designed to be called as a node inside a larger
AI orchestrator that validates ideas across multiple dimensions.

Usage
-----
    python agent.py "Add a one-click upsell modal on the checkout confirmation page"

Or import and call from your orchestrator:

    from agent import run_business_impact_agent
    report = await run_business_impact_agent(idea="...", context={})

Requirements
------------
    pip install anthropic pydantic python-dotenv
    export ANTHROPIC_API_KEY="sk-ant-..."
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

import anthropic
from dotenv import load_dotenv

from models import BusinessImpactReport
from tools import TOOLS, execute_tool

load_dotenv()

MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """You are a Senior Business Analyst and Revenue Strategist embedded in a
product-validation AI orchestrator.

Your job is to evaluate a raw product idea and produce a rigorous, data-grounded
Business Impact Report. You MUST use the available tools to gather data before
drawing conclusions — do NOT estimate from memory alone.

## Analytical Framework

Work through these steps using the tools:

1. **Baseline** — Call `get_baseline_metrics` to anchor all calculations.
2. **Comparable experiments** — Call `lookup_comparable_experiments` with relevant
   keywords to calibrate your estimates against historical data.
3. **Conversion impact** — Call `estimate_conversion_impact` for every funnel
   stage the idea touches.
4. **Cannibalization** — Call `check_cannibalization_risk` if the idea could
   overlap with existing paid features or products.
5. **Financial model** — Call `calculate_revenue_delta` for optimistic, base-case,
   and pessimistic scenarios using the metric changes you've identified.

## Report Requirements

After gathering data, synthesise a `BusinessImpactReport` JSON object that covers:
- Probability-weighted net annual revenue impact (USD)
- Metric impacts (CR, ARPU, churn, LTV, etc.) with confidence levels
- Risk register: CR drop, cannibalization, churn increase, mis-attribution, etc.
- Suggested A/B tests or validation experiments before full rollout

## Risk Taxonomy

Always check for — and explicitly address — each of these risk types:
- **CR drop**: Any friction, distraction, or confusion the idea could introduce
- **Cannibalization**: Revenue shifted away from existing paid features/tiers
- **Churn acceleration**: Does the idea expose a pain point or reduce lock-in?
- **Adverse selection**: Does the idea attract low-LTV users disproportionately?
- **Experiment mis-attribution**: Confounders that could make A/B results misleading
- **Regulatory / compliance**: Anything that could create legal exposure

## Output Format

Return ONLY a valid JSON object matching the `BusinessImpactReport` schema.
Do not wrap it in markdown code fences. Do not add prose outside the JSON.
"""


async def run_business_impact_agent(
    idea: str,
    context: dict[str, Any] | None = None,
) -> BusinessImpactReport:
    """
    Run the Business Impact Calculator agent for a given idea.

    Parameters
    ----------
    idea:
        The raw product idea or hypothesis to evaluate.
    context:
        Optional dict with additional context for the orchestrator
        (e.g. target segment, implementation cost estimate, priority score
        from other agents). This is appended to the user prompt.

    Returns
    -------
    BusinessImpactReport
        A fully validated Pydantic model with the financial analysis.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_prompt = f"Evaluate the following product idea:\n\n{idea}"
    if context:
        user_prompt += f"\n\nAdditional context from the orchestrator:\n{json.dumps(context, indent=2)}"

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]

    print(f"[BusinessImpactAgent] Evaluating idea: {idea[:80]}...")

    # Agentic loop — keep going until Claude stops calling tools
    while True:
        with client.messages.stream(
            model=MODEL,
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            # Stream tokens to console so progress is visible
            for event in stream:
                if (
                    event.type == "content_block_delta"
                    and hasattr(event.delta, "text")
                ):
                    print(event.delta.text, end="", flush=True)

            response = stream.get_final_message()

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            # Append assistant turn (including tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool and collect results
            tool_results = []
            for block in tool_use_blocks:
                print(f"\n[Tool] {block.name}({json.dumps(block.input, separators=(',', ':'))})")
                result = execute_tool(block.name, block.input)
                print(f"[Tool result] {result[:200]}{'...' if len(result) > 200 else ''}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})
            continue

        # pause_turn: server-side iteration limit hit — re-send to continue
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue

        # Any other stop reason — exit loop
        break

    # Extract the final text block (the JSON report)
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    print("\n")  # newline after streaming output

    try:
        report_data = json.loads(final_text.strip())
        return BusinessImpactReport.model_validate(report_data)
    except (json.JSONDecodeError, Exception) as exc:
        raise ValueError(
            f"Agent did not return valid BusinessImpactReport JSON.\n"
            f"Error: {exc}\n"
            f"Raw output:\n{final_text}"
        ) from exc


def _print_report(report: BusinessImpactReport) -> None:
    """Pretty-print the report to stdout."""
    sep = "=" * 70
    print(sep)
    print("BUSINESS IMPACT REPORT")
    print(sep)
    print(f"Idea        : {report.idea_summary}")
    print(f"Recommend   : {report.overall_recommendation.upper()}")
    print(f"Confidence  : {report.confidence_score:.0%}")
    print(f"Expected NPV: ${report.total_expected_value_usd:,.0f} / year (probability-weighted)")
    print()

    proj = report.revenue_projection
    print(f"Revenue Projection ({proj.timeframe_months}-month horizon)")
    print(f"  Base case   : ${proj.base_case_usd:,.0f}")
    print(f"  Optimistic  : ${proj.optimistic_case_usd:,.0f}")
    print(f"  Pessimistic : ${proj.pessimistic_case_usd:,.0f}")
    if proj.payback_period_months:
        print(f"  Payback     : {proj.payback_period_months} months")
    print()

    print("Metric Impacts")
    for m in report.metric_impacts:
        direction_icon = "+" if m.direction == "positive" else ("-" if m.direction == "negative" else "~")
        delta_str = f"{m.delta_percent:+.1f}%" if m.delta_percent is not None else "N/A"
        print(f"  {direction_icon} {m.metric_name}: {delta_str}  (confidence {m.confidence:.0%})")
    print()

    print("Risk Register")
    for r in report.risks:
        impact_str = f"  ~${abs(r.estimated_impact_usd):,.0f}" if r.estimated_impact_usd else ""
        print(f"  [{r.severity.upper()}] {r.risk_type}{impact_str}")
        print(f"           {r.description}")
        print(f"           Mitigation: {r.mitigation}")
    print()

    print("Key Unknowns")
    for u in report.key_unknowns:
        print(f"  ? {u}")
    print()

    print("Suggested Experiments")
    for e in report.suggested_experiments:
        print(f"  - {e}")
    print()

    print("Analyst Notes")
    print(f"  {report.analyst_notes}")
    print(sep)


if __name__ == "__main__":
    idea = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "Add a one-click upsell modal on the checkout confirmation page "
            "offering an annual plan at 20% discount for monthly subscribers."
        )
    )

    report = asyncio.run(run_business_impact_agent(idea=idea))
    _print_report(report)

    # Also dump the raw JSON for downstream orchestrator consumers
    print("\nRaw JSON (for orchestrator):")
    print(report.model_dump_json(indent=2))
