"""End-to-end tests for the assessment API.

Covers the full happy path: signup -> create draft -> save responses ->
check progress -> submit -> retrieve scoring. Plus tenant isolation and
state-machine guards.
"""
import pytest


# -----------------------------------------------------------------------------
# Shared fixture: a signed-up authed client + a complete response set
# -----------------------------------------------------------------------------


@pytest.fixture
def full_responses() -> dict:
    return {
        "co.primary_country": "NG",
        "co.serves_eu_users": False,
        "co.has_us_customers": True,
        "co.team_size": "11-50",
        "co.industry": "fintech",
        "co.business_model": "b2b",
        "co.regulated_activity": True,
        "co.handles_card_data": False,
        "da.data_types": ["names_emails", "phone_numbers", "financial"],
        "da.data_volume": "10k_100k",
        "da.data_retention_policy": "yes_manual",
        "da.encryption_at_rest": "all",
        "da.encryption_in_transit": "all",
        "ac.mfa_employees": "all_systems",
        "ac.access_reviews": "annually",
        "ac.offboarding": "same_day_manual",
        "ac.privileged_access": "yes_full",
        "te.cloud_providers": ["aws"],
        "te.code_repository": "github",
        "te.code_review": "required_all",
        "te.backups": "auto_tested",
        "te.vulnerability_scanning": "periodic",
        "te.logging_monitoring": "centralized_alerting",
        "ve.vendor_count": "6-20",
        "ve.vendor_review": "informal",
        "ve.dpa_signed": "some",
        "po.security_policy": "yes_static",
        "po.privacy_policy_published": True,
        "po.security_training": "onboarding_only",
        "po.background_checks": "sensitive_roles",
        "po.dpo_appointed": False,
        "in.ir_plan": "yes_untested",
        "in.breach_in_last_year": "no",
        "in.breach_notification_aware": True,
        "go.target_frameworks": ["soc2", "ndpa"],
        "go.target_timeline": "6_months",
        "go.driver": ["customer_requirement"],
    }


# -----------------------------------------------------------------------------
# Questionnaire endpoints
# -----------------------------------------------------------------------------


class TestQuestionnaireEndpoints:
    def test_get_latest_questionnaire(self, authed_client):
        resp = authed_client.get("/api/v1/questionnaires/latest")
        assert resp.status_code == 200
        body = resp.json()
        assert body["version"] == "1.0.0"
        assert len(body["sections"]) >= 5

    def test_get_specific_version(self, authed_client):
        resp = authed_client.get("/api/v1/questionnaires/1.0.0")
        assert resp.status_code == 200

    def test_get_unknown_version_404(self, authed_client):
        resp = authed_client.get("/api/v1/questionnaires/999.0.0")
        assert resp.status_code == 404

    def test_questionnaires_require_auth(self, client):
        resp = client.get("/api/v1/questionnaires/latest")
        assert resp.status_code == 401


# -----------------------------------------------------------------------------
# Assessment lifecycle
# -----------------------------------------------------------------------------


class TestAssessmentLifecycle:
    def test_create_draft_assessment(self, authed_client):
        resp = authed_client.post("/api/v1/assessments", json={})
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "draft"
        assert body["responses"] == {}
        assert body["overall_risk_score"] is None

    def test_save_partial_responses(self, authed_client):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]
        resp = authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"co.primary_country": "NG"}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["responses"] == {"co.primary_country": "NG"}
        assert body["status"] == "in_progress"

    def test_save_responses_merge_default(self, authed_client):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]
        authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"co.primary_country": "NG"}},
        )
        resp = authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"co.team_size": "11-50"}},
        )
        body = resp.json()
        assert body["responses"]["co.primary_country"] == "NG"
        assert body["responses"]["co.team_size"] == "11-50"

    def test_save_responses_replace_when_merge_false(self, authed_client):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]
        authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"co.primary_country": "NG"}},
        )
        resp = authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"co.team_size": "11-50"}, "merge": False},
        )
        body = resp.json()
        assert "co.primary_country" not in body["responses"]
        assert body["responses"]["co.team_size"] == "11-50"

    def test_save_invalid_response_rejected(self, authed_client):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]
        resp = authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"co.primary_country": "INVALID_OPTION"}},
        )
        assert resp.status_code == 422

    def test_save_unknown_question_rejected(self, authed_client):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]
        resp = authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"q.fake": "anything"}},
        )
        assert resp.status_code == 422

    def test_progress_reflects_completion(self, authed_client, full_responses):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]

        # 0% at start
        progress = authed_client.get(f"/api/v1/assessments/{aid}/progress").json()
        assert progress["completion_pct"] == 0
        assert progress["answered_questions"] == 0

        # Save partial
        partial = {k: v for k, v in list(full_responses.items())[:5]}
        authed_client.patch(
            f"/api/v1/assessments/{aid}/responses", json={"responses": partial}
        )
        progress = authed_client.get(f"/api/v1/assessments/{aid}/progress").json()
        assert 0 < progress["completion_pct"] < 100

        # Complete
        authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": full_responses},
        )
        progress = authed_client.get(f"/api/v1/assessments/{aid}/progress").json()
        assert progress["completion_pct"] == 100
        assert progress["remaining_question_ids"] == []

    def test_submit_incomplete_returns_422(self, authed_client):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]
        resp = authed_client.post(f"/api/v1/assessments/{aid}/submit")
        assert resp.status_code == 422

    def test_full_submit_flow(self, authed_client, full_responses):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]

        authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": full_responses},
        )
        resp = authed_client.post(f"/api/v1/assessments/{aid}/submit")
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # Assessment finalized
        assert body["assessment"]["status"] == "completed"
        assert body["assessment"]["overall_risk_score"] is not None
        assert 0 < body["assessment"]["overall_risk_score"] < 100

        # SOC 2 / NDPA scores populated since questionnaire references them
        assert body["assessment"]["soc2_readiness_score"] is not None
        assert body["assessment"]["ndpa_compliance_score"] is not None

        # Scoring summary returned
        scoring = body["scoring"]
        assert scoring["overall_risk_score"] == body["assessment"]["overall_risk_score"]
        framework_codes = {fs["framework"] for fs in scoring["framework_scores"]}
        assert "soc2" in framework_codes
        assert "ndpa" in framework_codes
        assert scoring["response_count"] > 0
        assert len(scoring["control_scores"]) > 0

    def test_cannot_submit_completed_assessment_twice(self, authed_client, full_responses):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]
        authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": full_responses},
        )
        first = authed_client.post(f"/api/v1/assessments/{aid}/submit")
        assert first.status_code == 200

        second = authed_client.post(f"/api/v1/assessments/{aid}/submit")
        assert second.status_code == 409  # state machine rejects

    def test_cannot_modify_responses_after_submit(self, authed_client, full_responses):
        created = authed_client.post("/api/v1/assessments", json={}).json()
        aid = created["id"]
        authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": full_responses},
        )
        authed_client.post(f"/api/v1/assessments/{aid}/submit")

        resp = authed_client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"co.primary_country": "KE"}},
        )
        assert resp.status_code == 409

    def test_list_assessments_scoped_to_company(self, authed_client):
        for _ in range(3):
            authed_client.post("/api/v1/assessments", json={})
        resp = authed_client.get("/api/v1/assessments")
        assert resp.status_code == 200
        assert len(resp.json()) == 3


# -----------------------------------------------------------------------------
# Tenant isolation
# -----------------------------------------------------------------------------


class TestTenantIsolation:
    def test_other_company_cannot_see_assessment(self, client, signup_payload, full_responses):
        # Company A signs up and creates an assessment
        resp_a = client.post("/api/v1/auth/signup", json=signup_payload)
        token_a = resp_a.json()["tokens"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token_a}"})
        a_assessment = client.post("/api/v1/assessments", json={}).json()
        aid = a_assessment["id"]

        # Company B signs up
        client.headers.clear()
        b_payload = {
            **signup_payload,
            "email": "rival@beta.ng",
            "company_name": "Rival Co",
        }
        resp_b = client.post("/api/v1/auth/signup", json=b_payload)
        token_b = resp_b.json()["tokens"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token_b}"})

        # Company B cannot see Company A's assessment
        resp = client.get(f"/api/v1/assessments/{aid}")
        assert resp.status_code == 404

        # Company B cannot modify it
        resp = client.patch(
            f"/api/v1/assessments/{aid}/responses",
            json={"responses": {"co.primary_country": "ZA"}},
        )
        assert resp.status_code == 404

        # Company B's list does not include it
        resp = client.get("/api/v1/assessments")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_assessment_endpoints_require_auth(self, client):
        resp = client.post("/api/v1/assessments", json={})
        assert resp.status_code == 401

        resp = client.get("/api/v1/assessments")
        assert resp.status_code == 401
