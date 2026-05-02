"""End-to-end tests for the reports API.

Covers full flow: signup -> assessment -> submit -> report generated ->
report retrieval. Plus tenant isolation on reports.
"""
import pytest


@pytest.fixture
def full_responses() -> dict:
    return {
        "co.primary_country": "NG",
        "co.serves_eu_users": False,
        "co.has_us_customers": True,
        "co.team_size": "11-50",
        "da.data_types": ["names_emails", "phone_numbers", "financial", "bvn_nin"],
        "da.data_volume": "10k_100k",
        "da.data_retention_policy": "informal",
        "da.encryption_at_rest": "some",
        "da.encryption_in_transit": "external_only",
        "ac.mfa_employees": "critical_only",
        "ac.access_reviews": "ad_hoc",
        "ac.offboarding": "within_week",
        "ac.privileged_access": "logged_not_restricted",
        "te.cloud_providers": ["aws"],
        "te.code_repository": "github",
        "te.code_review": "encouraged",
        "te.backups": "auto_untested",
        "te.vulnerability_scanning": "ad_hoc",
        "te.logging_monitoring": "scattered",
        "ve.vendor_count": "6-20",
        "ve.vendor_review": "informal",
        "ve.dpa_signed": "none",
        "po.security_policy": "draft",
        "po.privacy_policy_published": False,
        "po.security_training": "ad_hoc",
        "po.background_checks": "no",
        "po.dpo_appointed": False,
        "in.ir_plan": "informal",
        "in.breach_in_last_year": "no",
        "in.breach_notification_aware": False,
        "go.target_frameworks": ["soc2", "ndpa"],
        "go.target_timeline": "6_months",
        "go.driver": ["customer_requirement"],
    }


def _submit_assessment(client, full_responses) -> dict:
    """Helper: create, fill, submit. Returns the submit response."""
    created = client.post("/api/v1/assessments", json={}).json()
    aid = created["id"]
    client.patch(
        f"/api/v1/assessments/{aid}/responses", json={"responses": full_responses}
    )
    return client.post(f"/api/v1/assessments/{aid}/submit").json()


class TestSubmitGeneratesReport:
    def test_submit_returns_report_id(self, authed_client, full_responses):
        body = _submit_assessment(authed_client, full_responses)
        assert "report_id" in body
        assert body["report_id"]
        assert body["assessment"]["status"] == "completed"

    def test_initial_submit_marked_as_initial_report(
        self, authed_client, full_responses
    ):
        body = _submit_assessment(authed_client, full_responses)
        report = authed_client.get(f"/api/v1/reports/{body['report_id']}").json()
        assert report["report_type"] == "initial"

    def test_second_submit_marked_as_reassessment(
        self, authed_client, full_responses
    ):
        first = _submit_assessment(authed_client, full_responses)
        second = _submit_assessment(authed_client, full_responses)

        first_report = authed_client.get(
            f"/api/v1/reports/{first['report_id']}"
        ).json()
        second_report = authed_client.get(
            f"/api/v1/reports/{second['report_id']}"
        ).json()

        assert first_report["report_type"] == "initial"
        assert second_report["report_type"] == "reassessment"


class TestReportRetrieval:
    def test_get_report_returns_full_payload(self, authed_client, full_responses):
        body = _submit_assessment(authed_client, full_responses)
        rid = body["report_id"]

        resp = authed_client.get(f"/api/v1/reports/{rid}")
        assert resp.status_code == 200
        report = resp.json()

        # Required structured fields
        assert report["executive_summary"]
        assert isinstance(report["risk_register"], list)
        assert len(report["risk_register"]) > 0
        assert isinstance(report["roadmap"], list)
        assert len(report["roadmap"]) > 0
        assert isinstance(report["framework_gaps"], dict)

        # Each risk has the canonical shape
        first_risk = report["risk_register"][0]
        for key in ("id", "title", "severity", "likelihood", "description"):
            assert key in first_risk

        # Each roadmap task has effort and week
        first_task = report["roadmap"][0]
        for key in ("id", "title", "effort", "week_target", "severity"):
            assert key in first_task

    def test_list_reports_for_company(self, authed_client, full_responses):
        _submit_assessment(authed_client, full_responses)
        _submit_assessment(authed_client, full_responses)

        resp = authed_client.get("/api/v1/reports")
        assert resp.status_code == 200
        reports = resp.json()
        assert len(reports) == 2

    def test_list_reports_by_assessment(self, authed_client, full_responses):
        # Create one assessment + report
        body = _submit_assessment(authed_client, full_responses)
        aid = body["assessment"]["id"]

        resp = authed_client.get(f"/api/v1/reports/by-assessment/{aid}")
        assert resp.status_code == 200
        reports = resp.json()
        assert len(reports) == 1
        assert reports[0]["assessment_id"] == aid

    def test_get_report_not_found(self, authed_client):
        resp = authed_client.get("/api/v1/reports/no-such-id")
        assert resp.status_code == 404

    def test_reports_require_auth(self, client):
        resp = client.get("/api/v1/reports")
        assert resp.status_code == 401


class TestTenantIsolation:
    def test_other_company_cannot_see_report(
        self, client, signup_payload, full_responses
    ):
        # Company A signs up and generates a report
        client.post("/api/v1/auth/signup", json=signup_payload)
        login_a = client.post(
            "/api/v1/auth/login",
            json={
                "email": signup_payload["email"],
                "password": signup_payload["password"],
            },
        ).json()
        client.headers.update({"Authorization": f"Bearer {login_a['access_token']}"})
        body = _submit_assessment(client, full_responses)
        rid = body["report_id"]

        # Company B signs up
        client.headers.clear()
        b_payload = {
            **signup_payload,
            "email": "rival@beta.ng",
            "company_name": "Rival Co",
        }
        client.post("/api/v1/auth/signup", json=b_payload)
        login_b = client.post(
            "/api/v1/auth/login",
            json={"email": b_payload["email"], "password": b_payload["password"]},
        ).json()
        client.headers.update({"Authorization": f"Bearer {login_b['access_token']}"})

        # B cannot see A's report
        resp = client.get(f"/api/v1/reports/{rid}")
        assert resp.status_code == 404

        # B's report list is empty
        resp = client.get("/api/v1/reports")
        assert resp.status_code == 200
        assert resp.json() == []


class TestReportContents:
    def test_report_contains_company_specific_summary(
        self, authed_client, full_responses, signup_payload
    ):
        body = _submit_assessment(authed_client, full_responses)
        rid = body["report_id"]
        report = authed_client.get(f"/api/v1/reports/{rid}").json()

        # Mock advisor injects company name; summary should be specific
        assert signup_payload["company_name"] in report["executive_summary"]

    def test_report_addresses_realistic_gaps(self, authed_client, full_responses):
        # Realistic responses have weak access controls -> we should see
        # access-related risks
        body = _submit_assessment(authed_client, full_responses)
        rid = body["report_id"]
        report = authed_client.get(f"/api/v1/reports/{rid}").json()

        risk_titles = " ".join(r["title"].lower() for r in report["risk_register"])
        # At least one of the major weak areas should surface
        weak_signals = ["mfa", "access", "training", "incident", "encryption", "vendor"]
        assert any(signal in risk_titles for signal in weak_signals), risk_titles

    def test_report_tracks_token_usage(self, authed_client, full_responses):
        body = _submit_assessment(authed_client, full_responses)
        rid = body["report_id"]
        report = authed_client.get(f"/api/v1/reports/{rid}").json()
        # Mock advisor reports zero tokens (no API call), but the field is populated
        assert report["generation_tokens_input"] is not None
        assert report["generation_tokens_output"] is not None
        assert report["model_used"]
