"""Cross-framework control mapping.

When a company implements one piece of evidence (e.g., MFA enforcement), it
typically satisfies multiple controls across frameworks (SOC 2 CC6.1, NDPA
Section 24, CBN 4.2). This module resolves those mappings from the
ControlMapping table.

Mappings are bidirectional in semantics but stored directionally so we can
record asymmetric strengths. When asking "what does control X cover?" we
look in both directions.
"""
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Control, ControlMapping, Framework, MappingStrength


@dataclass(frozen=True)
class MappedControl:
    """A control reachable from a starting control via a mapping."""
    framework_code: str
    control_code: str
    title: str
    strength: MappingStrength


def find_related_controls(
    db: Session,
    framework_code: str,
    control_code: str,
    *,
    min_strength: MappingStrength = MappingStrength.PARTIAL,
) -> list[MappedControl]:
    """Return all controls in other frameworks that map to (framework, code).

    Excludes the input control itself. Direction-agnostic: looks at both
    source→target and target→source mappings.
    """
    framework = (
        db.query(Framework).filter(Framework.code == framework_code).first()
    )
    if framework is None:
        return []

    source = (
        db.query(Control)
        .filter(Control.framework_id == framework.id, Control.code == control_code)
        .first()
    )
    if source is None:
        return []

    strength_order = {
        MappingStrength.RELATED: 0,
        MappingStrength.PARTIAL: 1,
        MappingStrength.EQUIVALENT: 2,
    }
    min_rank = strength_order[min_strength]

    mappings = (
        db.query(ControlMapping)
        .filter(
            or_(
                ControlMapping.source_control_id == source.id,
                ControlMapping.target_control_id == source.id,
            )
        )
        .all()
    )

    out: list[MappedControl] = []
    seen: dict[tuple[str, str], MappedControl] = {}
    for m in mappings:
        if strength_order[m.strength] < min_rank:
            continue
        other_id = (
            m.target_control_id if m.source_control_id == source.id else m.source_control_id
        )
        other = db.query(Control).filter(Control.id == other_id).first()
        if other is None:
            continue
        other_framework = (
            db.query(Framework).filter(Framework.id == other.framework_id).first()
        )
        if other_framework is None:
            continue
        key = (other_framework.code.value, other.code)
        new_entry = MappedControl(
            framework_code=other_framework.code.value,
            control_code=other.code,
            title=other.title,
            strength=m.strength,
        )
        # If we've seen this control via another mapping (e.g. forward and
        # reverse rows in YAML), keep the stronger one.
        existing = seen.get(key)
        if existing is None or strength_order[m.strength] > strength_order[existing.strength]:
            seen[key] = new_entry

    out = list(seen.values())
    return out


def get_framework_coverage_summary(
    db: Session,
    framework_codes: list[str] | None = None,
) -> dict[str, dict]:
    """For each framework, return total control count and basic metadata.

    Used to compute coverage percentages on framework score reports.
    """
    query = db.query(Framework)
    if framework_codes:
        query = query.filter(Framework.code.in_(framework_codes))

    summary: dict[str, dict] = {}
    for fw in query.all():
        control_count = (
            db.query(Control).filter(Control.framework_id == fw.id).count()
        )
        summary[fw.code.value] = {
            "name": fw.name,
            "version": fw.version,
            "control_count": control_count,
            "jurisdiction": fw.jurisdiction,
        }
    return summary


def build_evidence_satisfaction_matrix(
    db: Session,
    satisfied_controls: list[tuple[str, str]],
) -> dict[str, set[str]]:
    """Given controls already satisfied, compute the full set per framework.

    Input is a list of (framework_code, control_code) pairs the company has
    direct evidence for. Output expands these via ControlMapping (EQUIVALENT
    only) into a dict of framework_code -> set of satisfied control codes.

    This is the core of "satisfy multiple frameworks with one piece of
    evidence" — the user uploads evidence once for one control, and we
    propagate satisfaction across mapped controls in other frameworks.
    """
    satisfied: dict[str, set[str]] = defaultdict(set)
    for fw_code, ctrl_code in satisfied_controls:
        satisfied[fw_code].add(ctrl_code)

    for fw_code, ctrl_code in list(satisfied_controls):
        related = find_related_controls(
            db, fw_code, ctrl_code, min_strength=MappingStrength.EQUIVALENT
        )
        for r in related:
            satisfied[r.framework_code].add(r.control_code)

    return dict(satisfied)
