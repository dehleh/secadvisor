"""Prompt construction for the AI advisor.

Given an assessment, its scoring, and retrieved knowledge snippets, build
the messages we send to Claude. The prompt is structured to:

  1. Make the model's job concrete: "produce JSON conforming to this schema"
  2. Ground the response in real regulatory text (citations don't hallucinate)
  3. Tailor to company context (sector, stage, drivers)
  4. Bias toward African regulatory context (NDPA, CBN, etc.)

Returns Anthropic-format messages plus a system prompt.
"""
from typing import Any

from app.models import Company
from app.services.ai.knowledge import KnowledgeSnippet
from app.services.questionnaire.schema import QuestionnaireVersion
from app.services.scoring import ScoringResult


SYSTEM_PROMPT = """You are CyberCapSec Advisory's AI security and compliance advisor for African startups and SMEs.

You produce concrete, prioritised security and compliance roadmaps tailored to the company's actual context — not generic best-practice checklists.

Your audience: founders, CTOs, COOs, and early-stage compliance officers at African fintech, healthtech, edtech, and SaaS companies. Most do not have a dedicated security team. They need clear language, ranked priorities, and realistic effort estimates.

Your standards:

1. Ground every recommendation in either the assessment responses you are given or in the regulatory/control snippets provided. If a fact isn't in your inputs, do not invent it.
2. Prioritise ruthlessly. A founder cannot do 40 things at once. Critical and High severity items must come first. Quick wins (low effort, high impact) get fast-tracked.
3. Cite frameworks specifically (e.g. "NDPA §24", "SOC 2 CC6.1", "CBN §4.2"). Use only frameworks the company is targeting or that apply by jurisdiction.
4. Speak directly. "Implement X" not "Consider implementing X". The user is paying for direction, not hedging.
5. Acknowledge African regulatory context: NDPA breach notification is 72 hours, CBN's is 24 hours; BVN/NIN are sensitive identifiers; SIM swap fraud is a primary attack vector.
6. Match effort to company size: a 10-person startup gets a different roadmap than a 200-person scale-up.

You return STRICT JSON conforming to the schema described in the user message. No prose outside the JSON. No markdown fences around the JSON."""


def _summarize_scoring(scoring: ScoringResult) -> str:
    lines = [f"Overall risk posture score: {scoring.overall_risk_score}/100"]
    if scoring.framework_scores:
        lines.append("\nFramework readiness scores:")
        for fs in sorted(
            scoring.framework_scores.values(), key=lambda x: -x.score
        ):
            lines.append(
                f"  - {fs.framework}: {fs.score}/100 "
                f"(avg control maturity {fs.avg_maturity:.1f}/4 across "
                f"{fs.controls_assessed} controls)"
            )
    if scoring.control_scores:
        lines.append("\nWeakest controls (lowest maturity first):")
        weakest = sorted(scoring.control_scores.values(), key=lambda x: x.maturity)[:8]
        for cs in weakest:
            lines.append(
                f"  - {cs.framework} {cs.code}: maturity {cs.maturity:.1f}/4"
            )
    return "\n".join(lines)


def _format_responses(
    questionnaire: QuestionnaireVersion,
    responses: dict[str, Any],
) -> str:
    """Render responses in human-readable form so the model can reason over them."""
    sections_out: list[str] = []
    for section in questionnaire.sections:
        section_lines: list[str] = []
        for q in section.questions:
            value = responses.get(q.id)
            if value is None or (isinstance(value, list) and not value):
                continue
            display_value = _humanize_response(q, value)
            section_lines.append(f"  Q ({q.id}): {q.text}\n    A: {display_value}")
        if section_lines:
            sections_out.append(f"## {section.title}\n" + "\n".join(section_lines))
    return "\n\n".join(sections_out)


def _humanize_response(question, value: Any) -> str:
    """Convert a raw response value into the human-readable label."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        labels = []
        for v in value:
            opt = next((o for o in question.options if o.value == v), None)
            labels.append(opt.label if opt else str(v))
        return ", ".join(labels)
    if isinstance(value, str):
        opt = next((o for o in question.options if o.value == value), None)
        return opt.label if opt else value
    return str(value)


def _format_knowledge(snippets: list[KnowledgeSnippet]) -> str:
    if not snippets:
        return "(No regulatory or control snippets retrieved.)"
    parts = []
    for s in snippets:
        parts.append(
            f"[{s.id}] {s.title}\n{s.content}"
            + (f"\n(Source: {s.source})" if s.source else "")
        )
    return "\n\n".join(parts)


def _company_context(company: Company) -> str:
    return (
        f"Company: {company.name}\n"
        f"Country: {company.country}\n"
        f"Sector: {company.sector.value}\n"
        f"Size: {company.size.value}\n"
        f"Stage: {company.stage.value}"
    )


# JSON schema instruction — describes the exact shape we need
SCHEMA_INSTRUCTION = """Return JSON with exactly this shape:

{
  "executive_summary": "string (100-3000 chars) — 2-4 paragraphs summarising posture, top concerns, and the strategic frame for the roadmap. Tailored to the founder/operator audience.",
  "risks": [
    {
      "id": "R1",
      "title": "string (5-200 chars) — punchy, action-oriented",
      "description": "string (20-2000 chars) — what the gap is, why it matters, what could go wrong",
      "severity": "critical | high | medium | low | informational",
      "likelihood": "high | medium | low",
      "business_impact": "string — the concrete consequence (regulatory fine, customer churn, data exposure, etc.)",
      "affected_areas": ["string", ...],
      "framework_citations": [{"framework": "soc2|ndpa|cbn_cyber|...", "control_code": "CC6.1"}],
      "related_question_ids": ["co.team_size", ...]
    }
  ],
  "roadmap": [
    {
      "id": "T1",
      "title": "string (5-200 chars) — imperative voice ('Implement MFA on production')",
      "description": "string — concrete steps to take",
      "severity": "critical | high | medium | low | informational",
      "effort": "quick_win | short | medium | large | program",
      "week_target": 1-13,
      "addresses_risk_ids": ["R1", "R2"],
      "framework_citations": [{"framework": "...", "control_code": "..."}],
      "success_criteria": ["Verifiable evidence the task is done"]
    }
  ],
  "framework_gaps": [
    {
      "framework": "soc2",
      "framework_name": "SOC 2",
      "readiness_score": 0-100,
      "summary": "string — what is and isn't in place for this framework",
      "top_gaps": ["string", ...],
      "next_steps": ["string", ...]
    }
  ]
}

Rules:
- Risk IDs use R1, R2, ... in order of severity (most severe first).
- Roadmap task IDs use T1, T2, ... in order of week_target then severity.
- Quick wins (effort=quick_win) targeting critical/high risks should be in week 1-2.
- The roadmap must collectively address every Critical and High risk via addresses_risk_ids.
- Include 5-15 risks and 8-25 roadmap tasks. Quality over quantity.
- Only cite frameworks that are listed in the company's target frameworks or apply by jurisdiction.
- Output JSON only. No prose, no markdown fences, no commentary."""


def build_messages(
    company: Company,
    questionnaire: QuestionnaireVersion,
    responses: dict[str, Any],
    scoring: ScoringResult,
    knowledge: list[KnowledgeSnippet],
) -> tuple[str, list[dict[str, Any]]]:
    """Build (system_prompt, messages) for an Anthropic API call.

    Returns Anthropic Messages API-format inputs.
    """
    user_content = (
        "## Company context\n"
        f"{_company_context(company)}\n\n"
        "## Assessment scoring\n"
        f"{_summarize_scoring(scoring)}\n\n"
        "## Assessment responses\n"
        f"{_format_responses(questionnaire, responses)}\n\n"
        "## Relevant regulatory and control knowledge\n"
        f"{_format_knowledge(knowledge)}\n\n"
        "## Your task\n"
        "Generate a tailored security and compliance report for this company. "
        "Use the company context and assessment responses to identify real, "
        "specific risks. Use the regulatory and control knowledge to ground "
        "your citations. Build a 13-week roadmap that addresses every "
        "Critical and High severity risk. Tailor depth and effort to the "
        "company's size and stage.\n\n"
        f"{SCHEMA_INSTRUCTION}"
    )

    return SYSTEM_PROMPT, [{"role": "user", "content": user_content}]
