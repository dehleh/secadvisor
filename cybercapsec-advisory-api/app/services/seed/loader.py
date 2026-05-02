"""Seed loader.

Reads YAML from app/data/, validates with the schemas, upserts into the DB.
Idempotent: running it twice produces the same DB state. Updates change
existing rows; new entries are added; nothing is ever deleted automatically
(safer for production: a YAML edit doesn't accidentally drop controls
that have evidence attached).

Usage:
    from app.services.seed.loader import seed_all
    seed_all(db_session)

Or via CLI:
    python -m app.cli seed
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.models import (
    Control,
    ControlMapping,
    Framework,
    FrameworkCode,
    MappingStrength,
)
from app.services.seed.schema import (
    FrameworkSeed,
    KnowledgeFile,
    MappingsFile,
)

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
FRAMEWORKS_DIR = DATA_DIR / "frameworks"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
MAPPINGS_FILE = DATA_DIR / "mappings.yaml"


@dataclass
class SeedReport:
    """Summary of what the seed run did."""
    frameworks_created: int = 0
    frameworks_updated: int = 0
    controls_created: int = 0
    controls_updated: int = 0
    mappings_created: int = 0
    mappings_updated: int = 0
    snippets_loaded: int = 0
    warnings: list[str] = field(default_factory=list)

    def render(self) -> str:
        return (
            f"Seed run complete:\n"
            f"  Frameworks: +{self.frameworks_created} new, "
            f"~{self.frameworks_updated} updated\n"
            f"  Controls:   +{self.controls_created} new, "
            f"~{self.controls_updated} updated\n"
            f"  Mappings:   +{self.mappings_created} new, "
            f"~{self.mappings_updated} updated\n"
            f"  Snippets loaded: {self.snippets_loaded}\n"
            + (
                "  Warnings:\n    " + "\n    ".join(self.warnings)
                if self.warnings
                else ""
            )
        )


# ----- File discovery ---------------------------------------------------------


def _load_yaml(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a YAML mapping")
    return data


def discover_framework_files(directory: Path = FRAMEWORKS_DIR) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob("*.yaml"))


def discover_knowledge_files(directory: Path = KNOWLEDGE_DIR) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob("*.yaml"))


# ----- Framework + control upsert --------------------------------------------


def seed_framework_file(
    db: Session, path: Path, report: SeedReport
) -> Framework:
    data = _load_yaml(path)
    seed = FrameworkSeed.model_validate(data)

    fw = db.query(Framework).filter(Framework.code == seed.code).first()
    if fw is None:
        fw = Framework(
            code=seed.code,
            name=seed.name,
            version=seed.version,
            jurisdiction=seed.jurisdiction,
            description=seed.description,
            source_url=seed.source_url,
        )
        db.add(fw)
        db.flush()
        report.frameworks_created += 1
    else:
        fw.name = seed.name
        fw.version = seed.version
        fw.jurisdiction = seed.jurisdiction
        fw.description = seed.description
        fw.source_url = seed.source_url
        report.frameworks_updated += 1

    # Index existing controls for fast lookup
    existing_by_code = {
        c.code: c
        for c in db.query(Control).filter(Control.framework_id == fw.id).all()
    }

    for control_seed in seed.controls:
        existing = existing_by_code.get(control_seed.code)
        if existing is None:
            db.add(
                Control(
                    framework_id=fw.id,
                    code=control_seed.code,
                    title=control_seed.title,
                    description=control_seed.description,
                    category=control_seed.category,
                    guidance=control_seed.guidance,
                )
            )
            report.controls_created += 1
        else:
            existing.title = control_seed.title
            existing.description = control_seed.description
            existing.category = control_seed.category
            existing.guidance = control_seed.guidance
            report.controls_updated += 1

    db.flush()
    return fw


# ----- Mapping upsert ---------------------------------------------------------


def seed_mappings(db: Session, path: Path, report: SeedReport) -> None:
    if not path.exists():
        report.warnings.append(f"Mappings file not found at {path}; skipping")
        return

    data = _load_yaml(path)
    seed = MappingsFile.model_validate(data)

    # Build a lookup of (framework_code, control_code) -> control_id
    framework_by_code: dict[FrameworkCode, Framework] = {
        fw.code: fw for fw in db.query(Framework).all()
    }
    controls_by_pair: dict[tuple[FrameworkCode, str], Control] = {}
    for fw in framework_by_code.values():
        for c in db.query(Control).filter(Control.framework_id == fw.id).all():
            controls_by_pair[(fw.code, c.code)] = c

    for mapping in seed.mappings:
        src = controls_by_pair.get((mapping.source_framework, mapping.source_code))
        tgt = controls_by_pair.get((mapping.target_framework, mapping.target_code))
        if src is None:
            report.warnings.append(
                f"Mapping skipped: source control "
                f"{mapping.source_framework.value} {mapping.source_code} not found"
            )
            continue
        if tgt is None:
            report.warnings.append(
                f"Mapping skipped: target control "
                f"{mapping.target_framework.value} {mapping.target_code} not found"
            )
            continue
        if src.id == tgt.id:
            report.warnings.append(
                f"Mapping skipped: source equals target "
                f"{mapping.source_framework.value} {mapping.source_code}"
            )
            continue

        existing = (
            db.query(ControlMapping)
            .filter(
                ControlMapping.source_control_id == src.id,
                ControlMapping.target_control_id == tgt.id,
            )
            .first()
        )
        if existing is None:
            db.add(
                ControlMapping(
                    source_control_id=src.id,
                    target_control_id=tgt.id,
                    strength=mapping.strength,
                    notes=mapping.notes,
                )
            )
            report.mappings_created += 1
        else:
            existing.strength = mapping.strength
            existing.notes = mapping.notes
            report.mappings_updated += 1

    db.flush()


# ----- Knowledge snippet loading ---------------------------------------------
#
# Knowledge snippets don't live in the DB in v1 — they're served from the
# in-memory retriever. We load them at module import time to a process-wide
# registry, validating each file against the schema. The seed command loads
# them strictly to confirm the corpus is parseable, but doesn't write to DB.


def load_knowledge_snippets() -> list:
    """Load all knowledge YAML files; validate; return as KnowledgeSnippet objects.

    Imported lazily inside this function to avoid circular dependency with
    the AI services package.
    """
    from app.services.ai.knowledge import KnowledgeSnippet

    out: list[KnowledgeSnippet] = []
    seen_ids: set[str] = set()
    for path in discover_knowledge_files():
        data = _load_yaml(path)
        kb = KnowledgeFile.model_validate(data)
        for s in kb.snippets:
            if s.id in seen_ids:
                raise ValueError(
                    f"Duplicate knowledge snippet id '{s.id}' across files"
                )
            seen_ids.add(s.id)
            out.append(
                KnowledgeSnippet(
                    id=s.id,
                    title=s.title,
                    content=s.content,
                    framework_codes=frozenset(fc.value for fc in s.framework_codes),
                    tags=frozenset(s.tags),
                    source=s.source,
                )
            )
    return out


# ----- Top-level orchestration -----------------------------------------------


def seed_all(db: Session) -> SeedReport:
    """Run the full seed: frameworks → mappings → knowledge corpus check."""
    report = SeedReport()

    framework_files = discover_framework_files()
    if not framework_files:
        report.warnings.append(
            f"No framework YAML files found in {FRAMEWORKS_DIR}"
        )
        return report

    for path in framework_files:
        seed_framework_file(db, path, report)

    seed_mappings(db, MAPPINGS_FILE, report)

    # Validate knowledge corpus parses (doesn't persist to DB)
    snippets = load_knowledge_snippets()
    report.snippets_loaded = len(snippets)

    db.commit()
    logger.info(report.render())
    return report
