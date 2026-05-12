"""Tests for the Session 6 knowledge base seed pipeline.

Covers:
  - Pydantic schema validation of YAML files
  - Seed loader idempotence
  - All shipped YAML files parse and seed cleanly
  - Cross-framework propagation works against the real corpus
  - InMemoryRetriever loads from YAML
"""
import pytest
import yaml

from app.models import (
    Control,
    ControlMapping,
    Framework,
    FrameworkCode,
    MappingStrength,
)
from app.services.seed import (
    FrameworkSeed,
    KnowledgeFile,
    MappingsFile,
    discover_framework_files,
    discover_knowledge_files,
    load_knowledge_snippets,
    seed_all,
)
from app.services.seed.loader import MAPPINGS_FILE


# ----- Schema validation -----------------------------------------------------


class TestYamlSchemas:
    def test_every_framework_yaml_validates(self):
        files = discover_framework_files()
        assert len(files) >= 5, "Expected at least 5 framework YAML files"
        for path in files:
            with open(path) as f:
                data = yaml.safe_load(f)
            seed = FrameworkSeed.model_validate(data)
            assert seed.controls, f"{path.name} has no controls"

    def test_mappings_file_validates(self):
        with open(MAPPINGS_FILE) as f:
            data = yaml.safe_load(f)
        mappings = MappingsFile.model_validate(data)
        assert len(mappings.mappings) > 50, (
            "Expected meaningful number of cross-framework mappings"
        )

    def test_every_knowledge_yaml_validates(self):
        files = discover_knowledge_files()
        assert files, "Expected at least one knowledge YAML file"
        for path in files:
            with open(path) as f:
                data = yaml.safe_load(f)
            kb = KnowledgeFile.model_validate(data)
            assert kb.snippets, f"{path.name} has no snippets"

    def test_duplicate_control_codes_in_framework_rejected(self, tmp_path):
        """Pydantic should reject a framework YAML with duplicate control codes."""
        bad = tmp_path / "bad.yaml"
        bad.write_text(
            """
code: soc2
name: Test
version: "1"
controls:
  - code: CC1.1
    title: First
    description: First control description here.
  - code: CC1.1
    title: Duplicate
    description: Duplicate control with same code.
"""
        )
        with open(bad) as f:
            data = yaml.safe_load(f)
        with pytest.raises(ValueError, match="Duplicate control codes"):
            FrameworkSeed.model_validate(data)


# ----- Seed loader -----------------------------------------------------------


class TestSeedLoader:
    def test_seed_all_creates_frameworks_and_controls(self, db_session):
        report = seed_all(db_session)
        assert report.frameworks_created >= 5
        assert report.controls_created >= 80

        frameworks = db_session.query(Framework).all()
        codes = {fw.code.value for fw in frameworks}
        assert "soc2" in codes
        assert "ndpa" in codes
        assert "cbn_cyber" in codes
        assert "iso27001" in codes
        assert "popia" in codes
        assert "kenya_dpa" in codes

    def test_seed_creates_mappings(self, db_session):
        seed_all(db_session)
        mappings = db_session.query(ControlMapping).all()
        assert len(mappings) >= 50

    def test_seed_loads_knowledge_corpus(self, db_session):
        report = seed_all(db_session)
        assert report.snippets_loaded >= 30

    def test_seed_idempotent(self, db_session):
        first = seed_all(db_session)
        second = seed_all(db_session)
        assert second.frameworks_created == 0
        assert second.frameworks_updated == first.frameworks_created
        assert second.controls_created == 0
        assert second.controls_updated == first.controls_created
        assert second.mappings_created == 0

    def test_seed_idempotent_no_duplicates(self, db_session):
        seed_all(db_session)
        seed_all(db_session)
        seed_all(db_session)
        # Total counts should match a single run
        total_frameworks = db_session.query(Framework).count()
        total_mappings = db_session.query(ControlMapping).count()
        assert total_frameworks == 7
        # No duplicate (source_id, target_id) pairs
        pairs = [
            (m.source_control_id, m.target_control_id)
            for m in db_session.query(ControlMapping).all()
        ]
        assert len(pairs) == len(set(pairs))


# ----- Real-corpus propagation ----------------------------------------------


class TestRealCorpusPropagation:
    """Now that we have real mappings, evidence at SOC 2 CC6.1 should
    propagate to NDPA SEC_24, ISO A.5.15, CBN 4.2, POPIA section 19,
    and Kenya DPA section 41 — as documented in the mappings YAML."""

    def test_cc6_1_propagates_to_all_security_clauses(
        self, authed_client, db_session
    ):
        seed_all(db_session)
        ev = authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "MFA enforced org-wide",
                "kind": "external_link",
                "framework_code": "soc2",
                "control_code": "CC6.1",
                "external_url": "https://example.com/mfa",
            },
        ).json()

        propagated = {
            (p["framework_code"], p["control_code"])
            for p in ev["propagated_controls"]
        }
        # All major security clauses should be reached
        assert ("ndpa", "SEC_24") in propagated
        assert ("iso27001", "A.5.15") in propagated
        assert ("cbn_cyber", "4.2") in propagated
        assert ("popia", "COND_7_S19") in propagated
        assert ("kenya_dpa", "SEC_41") in propagated

    def test_coverage_matrix_after_real_evidence(self, authed_client, db_session):
        seed_all(db_session)
        # Submit one piece of evidence at SOC 2 CC6.1
        authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "MFA enforced",
                "kind": "external_link",
                "framework_code": "soc2",
                "control_code": "CC6.1",
                "external_url": "https://example.com/mfa",
            },
        )

        cov = authed_client.get("/api/v1/evidence/coverage/matrix").json()[
            "coverage"
        ]
        # Single piece of evidence covers controls in 6 frameworks
        assert "soc2" in cov
        assert "ndpa" in cov
        assert "iso27001" in cov
        assert "cbn_cyber" in cov
        assert "popia" in cov
        assert "kenya_dpa" in cov


# ----- InMemoryRetriever loads from YAML -------------------------------------


class TestKnowledgeRetrieverYAMLLoading:
    def test_default_retriever_loads_from_yaml(self):
        from app.services.ai.knowledge import InMemoryRetriever

        # Default constructor (no arg) loads YAML corpus
        retriever = InMemoryRetriever()
        all_snippets = retriever.all_snippets
        # YAML corpus has 40+ snippets; hardcoded fallback has 22
        assert len(all_snippets) >= 30, (
            f"Expected ≥30 snippets from YAML corpus, got {len(all_snippets)}"
        )

    def test_retriever_filters_by_framework(self):
        from app.services.ai.knowledge import InMemoryRetriever

        retriever = InMemoryRetriever()
        ndpa_snippets = retriever.retrieve(framework_codes=["ndpa"])
        assert ndpa_snippets, "Should find NDPA snippets"
        for s in ndpa_snippets:
            assert "ndpa" in s.framework_codes

    def test_retriever_explicit_snippets_still_works(self):
        """Constructor-injected snippets bypass YAML loading."""
        from app.services.ai.knowledge import (
            InMemoryRetriever,
            KnowledgeSnippet,
        )

        custom = [
            KnowledgeSnippet(
                id="custom.1",
                title="Custom",
                content="x" * 25,
                framework_codes=frozenset({"soc2"}),
            )
        ]
        retriever = InMemoryRetriever(snippets=custom)
        assert len(retriever.all_snippets) == 1
        assert retriever.get_by_id("custom.1") is not None


# ----- Error handling --------------------------------------------------------


class TestSeedErrorHandling:
    def test_invalid_yaml_in_framework_file_raises(self, tmp_path, monkeypatch):
        """Bad YAML fails the seed, not silently loaded."""
        from app.services.seed import loader

        bad_dir = tmp_path / "frameworks"
        bad_dir.mkdir()
        (bad_dir / "broken.yaml").write_text("this is: not valid yaml: : :")

        monkeypatch.setattr(loader, "FRAMEWORKS_DIR", bad_dir)
        monkeypatch.setattr(loader, "MAPPINGS_FILE", tmp_path / "nope.yaml")
        monkeypatch.setattr(loader, "KNOWLEDGE_DIR", tmp_path / "knowledge")

        # Re-discover should surface the bad file
        files = loader.discover_framework_files(bad_dir)
        assert len(files) == 1
        # Loading it should fail validation
        with pytest.raises((ValueError, Exception)):
            data = loader._load_yaml(files[0])
            FrameworkSeed.model_validate(data)
