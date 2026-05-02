"""Tests for cross-framework control mapping."""
import pytest

from app.models import (
    Control,
    ControlMapping,
    Framework,
    FrameworkCode,
    MappingStrength,
)
from app.services.framework_mapping import (
    build_evidence_satisfaction_matrix,
    find_related_controls,
    get_framework_coverage_summary,
)


@pytest.fixture
def seeded_frameworks(db_session):
    """Seed two frameworks (SOC 2, NDPA) with a few controls and mappings."""
    soc2 = Framework(
        code=FrameworkCode.SOC2,
        name="SOC 2",
        version="2017",
        jurisdiction="USA",
    )
    ndpa = Framework(
        code=FrameworkCode.NDPA,
        name="Nigeria Data Protection Act",
        version="2023",
        jurisdiction="Nigeria",
    )
    cbn = Framework(
        code=FrameworkCode.CBN_CYBER,
        name="CBN Cybersecurity Framework",
        version="2022",
        jurisdiction="Nigeria",
    )
    db_session.add_all([soc2, ndpa, cbn])
    db_session.flush()

    # SOC 2 controls
    cc61 = Control(
        framework_id=soc2.id,
        code="CC6.1",
        title="Logical access controls",
        description="Access to systems is controlled.",
    )
    cc62 = Control(
        framework_id=soc2.id,
        code="CC6.2",
        title="Access provisioning",
        description="Access is granted based on role.",
    )
    # NDPA controls
    sec24 = Control(
        framework_id=ndpa.id,
        code="SEC_24",
        title="Security of processing",
        description="Implement appropriate security measures.",
    )
    # CBN controls
    cbn42 = Control(
        framework_id=cbn.id,
        code="4.2",
        title="Access management",
        description="Access management policies.",
    )

    db_session.add_all([cc61, cc62, sec24, cbn42])
    db_session.flush()

    # Mappings
    db_session.add(
        ControlMapping(
            source_control_id=cc61.id,
            target_control_id=sec24.id,
            strength=MappingStrength.EQUIVALENT,
        )
    )
    db_session.add(
        ControlMapping(
            source_control_id=cc61.id,
            target_control_id=cbn42.id,
            strength=MappingStrength.PARTIAL,
        )
    )
    db_session.commit()

    return {"soc2": soc2, "ndpa": ndpa, "cbn": cbn, "cc61": cc61, "sec24": sec24}


class TestFindRelatedControls:
    def test_finds_equivalent_mapping(self, db_session, seeded_frameworks):
        related = find_related_controls(db_session, "soc2", "CC6.1")
        codes = {(r.framework_code, r.control_code) for r in related}
        assert ("ndpa", "SEC_24") in codes
        assert ("cbn_cyber", "4.2") in codes

    def test_finds_mapping_in_reverse_direction(self, db_session, seeded_frameworks):
        # We mapped CC6.1 -> SEC_24. Looking up from SEC_24 should still find CC6.1.
        related = find_related_controls(db_session, "ndpa", "SEC_24")
        codes = {(r.framework_code, r.control_code) for r in related}
        assert ("soc2", "CC6.1") in codes

    def test_min_strength_filter_excludes_partial(self, db_session, seeded_frameworks):
        related = find_related_controls(
            db_session, "soc2", "CC6.1", min_strength=MappingStrength.EQUIVALENT
        )
        codes = {(r.framework_code, r.control_code) for r in related}
        # Only the EQUIVALENT mapping (NDPA SEC_24) survives
        assert ("ndpa", "SEC_24") in codes
        assert ("cbn_cyber", "4.2") not in codes

    def test_returns_empty_for_unknown_control(self, db_session, seeded_frameworks):
        assert find_related_controls(db_session, "soc2", "DOES_NOT_EXIST") == []

    def test_returns_empty_for_unknown_framework(self, db_session, seeded_frameworks):
        assert find_related_controls(db_session, "fake_framework", "CC6.1") == []


class TestEvidenceSatisfactionMatrix:
    def test_evidence_propagates_via_equivalent_mapping(self, db_session, seeded_frameworks):
        # Company has direct evidence for SOC 2 CC6.1.
        matrix = build_evidence_satisfaction_matrix(
            db_session, [("soc2", "CC6.1")]
        )
        # NDPA SEC_24 should be implicitly satisfied (EQUIVALENT mapping)
        assert "SEC_24" in matrix["ndpa"]
        assert "CC6.1" in matrix["soc2"]
        # CBN 4.2 should NOT be (only PARTIAL mapping)
        assert "4.2" not in matrix.get("cbn_cyber", set())

    def test_empty_input_yields_empty_matrix(self, db_session, seeded_frameworks):
        matrix = build_evidence_satisfaction_matrix(db_session, [])
        assert matrix == {}


class TestFrameworkCoverageSummary:
    def test_summary_includes_seeded_frameworks(self, db_session, seeded_frameworks):
        summary = get_framework_coverage_summary(db_session)
        assert "soc2" in summary
        assert summary["soc2"]["control_count"] == 2  # CC6.1, CC6.2
        assert summary["ndpa"]["control_count"] == 1
        assert summary["cbn_cyber"]["control_count"] == 1

    def test_summary_filtered_by_codes(self, db_session, seeded_frameworks):
        summary = get_framework_coverage_summary(db_session, ["soc2"])
        assert "soc2" in summary
        assert "ndpa" not in summary
