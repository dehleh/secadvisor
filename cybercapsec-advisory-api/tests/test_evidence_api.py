"""Tests for the evidence API and cross-framework propagation."""
import pytest

from app.models import (
    Control,
    ControlMapping,
    Framework,
    FrameworkCode,
    MappingStrength,
)


@pytest.fixture
def seed_mapping(db_session):
    """Seed SOC 2 CC6.1 <-> NDPA SEC_24 EQUIVALENT mapping for tests."""
    soc2 = Framework(
        code=FrameworkCode.SOC2,
        name="SOC 2",
        version="2017",
        jurisdiction="USA",
    )
    ndpa = Framework(
        code=FrameworkCode.NDPA,
        name="NDPA",
        version="2023",
        jurisdiction="Nigeria",
    )
    cbn = Framework(
        code=FrameworkCode.CBN_CYBER,
        name="CBN",
        version="2022",
        jurisdiction="Nigeria",
    )
    db_session.add_all([soc2, ndpa, cbn])
    db_session.flush()

    cc61 = Control(
        framework_id=soc2.id,
        code="CC6.1",
        title="Logical access controls",
        description="Access is controlled.",
    )
    sec24 = Control(
        framework_id=ndpa.id,
        code="SEC_24",
        title="Security of processing",
        description="Implement security measures.",
    )
    cbn42 = Control(
        framework_id=cbn.id,
        code="4.2",
        title="Access management",
        description="CBN access management.",
    )
    db_session.add_all([cc61, sec24, cbn42])
    db_session.flush()

    db_session.add_all([
        ControlMapping(
            source_control_id=cc61.id,
            target_control_id=sec24.id,
            strength=MappingStrength.EQUIVALENT,
        ),
        ControlMapping(
            source_control_id=cc61.id,
            target_control_id=cbn42.id,
            strength=MappingStrength.PARTIAL,
        ),
    ])
    db_session.commit()


# ----- Evidence creation ------------------------------------------------------


class TestCreateEvidence:
    def test_create_external_link_evidence(self, authed_client, seed_mapping):
        resp = authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "MFA enforcement screenshot",
                "description": "GitHub org showing MFA required",
                "kind": "external_link",
                "framework_code": "soc2",
                "control_code": "CC6.1",
                "external_url": "https://example.com/mfa-screenshot",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["evidence"]["title"] == "MFA enforcement screenshot"
        assert body["evidence"]["kind"] == "external_link"

    def test_external_link_requires_url(self, authed_client, seed_mapping):
        resp = authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "Bad link",
                "kind": "external_link",
                "framework_code": "soc2",
                "control_code": "CC6.1",
            },
        )
        assert resp.status_code == 422

    def test_unknown_framework_rejected(self, authed_client):
        resp = authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "Test",
                "kind": "narrative",
                "framework_code": "fake_framework",
                "control_code": "X.1",
                "narrative_text": "We do this.",
            },
        )
        assert resp.status_code == 422

    def test_narrative_evidence(self, authed_client):
        resp = authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "Quarterly access review process",
                "kind": "narrative",
                "framework_code": "soc2",
                "control_code": "CC6.2",
                "narrative_text": (
                    "Engineering manager runs quarterly access reviews using a "
                    "manual checklist; results are stored in our internal wiki."
                ),
            },
        )
        assert resp.status_code == 201

    def test_policy_ref_requires_existing_policy(self, authed_client):
        resp = authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "Bad policy ref",
                "kind": "policy_ref",
                "framework_code": "soc2",
                "control_code": "CC1.1",
                "referenced_policy_id": "no-such-policy",
            },
        )
        assert resp.status_code == 404


# ----- Cross-framework propagation -------------------------------------------


class TestPropagation:
    def test_evidence_propagates_via_equivalent_mapping(
        self, authed_client, seed_mapping
    ):
        resp = authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "MFA enforced",
                "kind": "external_link",
                "framework_code": "soc2",
                "control_code": "CC6.1",
                "external_url": "https://example.com/mfa",
            },
        ).json()
        # Evidence anchored at SOC 2 CC6.1 propagates to NDPA SEC_24 (EQUIVALENT)
        # and CBN 4.2 (PARTIAL — included by default min_strength=PARTIAL)
        propagated_codes = {
            (p["framework_code"], p["control_code"])
            for p in resp["propagated_controls"]
        }
        assert ("ndpa", "SEC_24") in propagated_codes
        assert ("cbn_cyber", "4.2") in propagated_codes

    def test_coverage_matrix_includes_propagated_controls(
        self, authed_client, seed_mapping
    ):
        # Submit SOC 2 evidence; check that NDPA shows up in coverage matrix
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

        resp = authed_client.get("/api/v1/evidence/coverage/matrix")
        assert resp.status_code == 200
        coverage = resp.json()["coverage"]
        assert "CC6.1" in coverage["soc2"]
        # NDPA SEC_24 should be there (EQUIVALENT mapping propagates by default)
        assert "SEC_24" in coverage.get("ndpa", [])

    def test_list_evidence_for_control_shows_direct_and_propagated(
        self, authed_client, seed_mapping
    ):
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

        # Direct lookup at SOC 2 CC6.1
        direct = authed_client.get(
            "/api/v1/evidence/by-control/soc2/CC6.1"
        ).json()
        assert len(direct["direct_evidence"]) == 1
        assert direct["direct_evidence"][0]["title"] == "MFA enforced"

        # Lookup at the mapped NDPA control — should see it as propagated
        propagated = authed_client.get(
            "/api/v1/evidence/by-control/ndpa/SEC_24"
        ).json()
        assert len(propagated["direct_evidence"]) == 0
        assert len(propagated["propagated_evidence"]) == 1
        assert propagated["propagated_evidence"][0]["title"] == "MFA enforced"


# ----- Status updates --------------------------------------------------------


class TestEvidenceStatus:
    def test_update_to_expired(self, authed_client):
        created = authed_client.post(
            "/api/v1/evidence",
            json={
                "title": "Test",
                "kind": "narrative",
                "framework_code": "soc2",
                "control_code": "CC6.1",
                "narrative_text": "We do this.",
            },
        ).json()
        eid = created["evidence"]["id"]

        resp = authed_client.patch(
            f"/api/v1/evidence/{eid}/status", json={"status": "expired"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "expired"


# ----- Tenant isolation ------------------------------------------------------


class TestEvidenceIsolation:
    def test_other_company_cannot_see_evidence(
        self, client, signup_payload, license_company
    ):
        # Company A submits evidence
        resp_a = client.post("/api/v1/auth/signup", json=signup_payload)
        license_company(resp_a.json()["company"]["id"])
        login_a = client.post(
            "/api/v1/auth/login",
            json={
                "email": signup_payload["email"],
                "password": signup_payload["password"],
            },
        ).json()
        client.headers.update({"Authorization": f"Bearer {login_a['access_token']}"})
        a_evidence = client.post(
            "/api/v1/evidence",
            json={
                "title": "A's evidence",
                "kind": "narrative",
                "framework_code": "soc2",
                "control_code": "CC6.1",
                "narrative_text": "Private.",
            },
        ).json()
        eid = a_evidence["evidence"]["id"]

        # Company B
        client.headers.clear()
        b_payload = {
            **signup_payload,
            "email": "rival@beta.ng",
            "company_name": "Rival Co",
        }
        resp_b = client.post("/api/v1/auth/signup", json=b_payload)
        license_company(resp_b.json()["company"]["id"])
        login_b = client.post(
            "/api/v1/auth/login",
            json={"email": b_payload["email"], "password": b_payload["password"]},
        ).json()
        client.headers.update({"Authorization": f"Bearer {login_b['access_token']}"})

        assert client.get(f"/api/v1/evidence/{eid}").status_code == 404
        assert client.get("/api/v1/evidence").json() == []
