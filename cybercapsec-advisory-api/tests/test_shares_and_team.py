"""Tests for shareable public report links and team management endpoints."""
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


def _generate_report(client, full_responses) -> str:
    created = client.post("/api/v1/assessments", json={}).json()
    aid = created["id"]
    client.patch(
        f"/api/v1/assessments/{aid}/responses",
        json={"responses": full_responses},
    )
    submit = client.post(f"/api/v1/assessments/{aid}/submit").json()
    return submit["report_id"]


# ----- Report shares --------------------------------------------------------


class TestReportShares:
    def test_create_share_returns_token(self, authed_client, full_responses):
        report_id = _generate_report(authed_client, full_responses)
        resp = authed_client.post(
            f"/api/v1/reports/{report_id}/shares",
            json={"label": "Investor due diligence", "expires_in_days": 30},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["token"]
        assert len(body["token"]) >= 32
        assert body["label"] == "Investor due diligence"
        assert body["expires_at"] is not None
        assert body["view_count"] == 0
        assert body["revoked_at"] is None

    def test_list_shares(self, authed_client, full_responses):
        report_id = _generate_report(authed_client, full_responses)
        authed_client.post(
            f"/api/v1/reports/{report_id}/shares", json={"label": "A"}
        )
        authed_client.post(
            f"/api/v1/reports/{report_id}/shares", json={"label": "B"}
        )
        resp = authed_client.get(f"/api/v1/reports/{report_id}/shares")
        assert resp.status_code == 200
        labels = sorted(s["label"] for s in resp.json())
        assert labels == ["A", "B"]

    def test_revoke_share(self, authed_client, full_responses):
        report_id = _generate_report(authed_client, full_responses)
        share = authed_client.post(
            f"/api/v1/reports/{report_id}/shares", json={}
        ).json()
        token = share["token"]

        # Public access works first
        pub = authed_client.get(f"/api/v1/public/reports/{token}")
        assert pub.status_code == 200

        # Revoke
        del_resp = authed_client.delete(f"/api/v1/reports/shares/{share['id']}")
        assert del_resp.status_code == 204

        # Public access now denied
        pub2 = authed_client.get(f"/api/v1/public/reports/{token}")
        assert pub2.status_code == 410

    def test_share_404_for_other_company(self, client, full_responses):
        # Company A signs up and generates a report
        a_signup = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "a@example.com",
                "password": "Str0ngPass!",
                "full_name": "Alice A",
                "company_name": "Company A",
                "country": "NG",
                "sector": "fintech",
                "size": "small",
                "stage": "seed",
            },
        )
        a_token = a_signup.json()["tokens"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {a_token}"})

        # Upgrade A so report generation isn't capped
        from app.models import Company, SubscriptionTier

        company_a_id = a_signup.json()["company"]["id"]

        report_id = _generate_report(client, full_responses)
        share = client.post(
            f"/api/v1/reports/{report_id}/shares", json={}
        ).json()

        # Sign up B in same client
        b_signup = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "b@example.com",
                "password": "Str0ngPass!",
                "full_name": "Bob B",
                "company_name": "Company B",
                "country": "NG",
                "sector": "fintech",
                "size": "small",
                "stage": "seed",
            },
        )
        b_token = b_signup.json()["tokens"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {b_token}"})

        # B cannot access A's report shares
        resp = client.get(f"/api/v1/reports/{report_id}/shares")
        assert resp.status_code == 404
        # B cannot revoke A's share
        resp = client.delete(f"/api/v1/reports/shares/{share['id']}")
        assert resp.status_code == 404
        # Avoid unused-import lint
        _ = (Company, SubscriptionTier, company_a_id)


class TestPublicReport:
    def test_public_report_renders(self, authed_client, full_responses):
        report_id = _generate_report(authed_client, full_responses)
        share = authed_client.post(
            f"/api/v1/reports/{report_id}/shares",
            json={"label": "External"},
        ).json()
        # No auth header needed (public route), but auth header is harmless
        pub = authed_client.get(f"/api/v1/public/reports/{share['token']}")
        assert pub.status_code == 200
        body = pub.json()
        assert body["company_name"]
        assert body["report_type"] in {
            "initial",
            "reassessment",
            "quarterly",
            "ad_hoc",
        }
        assert body["label"] == "External"
        assert "executive_summary" in body
        assert "risk_register" in body
        assert "roadmap" in body
        assert "framework_gaps" in body
        # Sanitised: no raw IDs
        assert "id" not in body
        assert "report_id" not in body

    def test_public_report_increments_view_count(
        self, authed_client, full_responses
    ):
        report_id = _generate_report(authed_client, full_responses)
        share = authed_client.post(
            f"/api/v1/reports/{report_id}/shares", json={}
        ).json()
        token = share["token"]

        authed_client.get(f"/api/v1/public/reports/{token}")
        authed_client.get(f"/api/v1/public/reports/{token}")
        authed_client.get(f"/api/v1/public/reports/{token}")

        listed = authed_client.get(
            f"/api/v1/reports/{report_id}/shares"
        ).json()
        assert listed[0]["view_count"] == 3
        assert listed[0]["last_viewed_at"] is not None

    def test_public_report_unknown_token(self, client):
        resp = client.get("/api/v1/public/reports/does-not-exist")
        assert resp.status_code == 404


# ----- Users / team ---------------------------------------------------------


class TestTeamUsers:
    def test_list_includes_owner(self, authed_client):
        resp = authed_client.get("/api/v1/users")
        assert resp.status_code == 200
        users = resp.json()
        assert len(users) == 1
        assert users[0]["role"] == "owner"

    def test_invite_returns_temp_password(self, authed_client):
        resp = authed_client.post(
            "/api/v1/users",
            json={
                "email": "teammate@example.com",
                "full_name": "Test Mate",
                "role": "member",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["user"]["email"] == "teammate@example.com"
        assert body["user"]["role"] == "member"
        assert body["temporary_password"]
        assert len(body["temporary_password"]) >= 12

    def test_invited_user_can_login_with_temp_password(
        self, authed_client, client
    ):
        resp = authed_client.post(
            "/api/v1/users",
            json={
                "email": "newbie@example.com",
                "full_name": "Newbie",
                "role": "member",
            },
        )
        temp = resp.json()["temporary_password"]
        # Different client (no Authorization header)
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "newbie@example.com", "password": temp},
        )
        assert login.status_code == 200

    def test_only_owner_can_grant_owner_role(self, authed_client):
        # Owner invites an admin
        admin_resp = authed_client.post(
            "/api/v1/users",
            json={
                "email": "admin@example.com",
                "full_name": "Admin",
                "role": "admin",
            },
        )
        admin_pwd = admin_resp.json()["temporary_password"]

        # Admin logs in (login returns access_token at top level per existing tests)
        admin_login = authed_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": admin_pwd},
        )
        admin_token = admin_login.json()["access_token"]
        old_auth = authed_client.headers.get("Authorization")
        authed_client.headers["Authorization"] = f"Bearer {admin_token}"

        # Admin tries to invite an owner -> forbidden
        forbidden = authed_client.post(
            "/api/v1/users",
            json={
                "email": "another-owner@example.com",
                "full_name": "Xavier",
                "role": "owner",
            },
        )
        assert forbidden.status_code == 403

        # Restore
        authed_client.headers["Authorization"] = old_auth

    def test_cannot_demote_last_owner(self, authed_client):
        users = authed_client.get("/api/v1/users").json()
        owner_id = users[0]["id"]
        resp = authed_client.patch(
            f"/api/v1/users/{owner_id}", json={"role": "member"}
        )
        assert resp.status_code == 409

    def test_cannot_deactivate_last_owner(self, authed_client):
        users = authed_client.get("/api/v1/users").json()
        owner_id = users[0]["id"]
        resp = authed_client.patch(
            f"/api/v1/users/{owner_id}", json={"is_active": False}
        )
        assert resp.status_code == 409

    def test_change_password(self, authed_client, signup_payload):
        resp = authed_client.post(
            "/api/v1/users/me/password",
            json={
                "current_password": signup_payload["password"],
                "new_password": "BrandNew!Pass123",
            },
        )
        assert resp.status_code == 204

        # Old password fails, new works
        old = authed_client.post(
            "/api/v1/auth/login",
            json={
                "email": signup_payload["email"],
                "password": signup_payload["password"],
            },
        )
        assert old.status_code == 401

        new = authed_client.post(
            "/api/v1/auth/login",
            json={
                "email": signup_payload["email"],
                "password": "BrandNew!Pass123",
            },
        )
        assert new.status_code == 200

    def test_change_password_wrong_current(self, authed_client):
        resp = authed_client.post(
            "/api/v1/users/me/password",
            json={
                "current_password": "WrongOldPwd!9999",
                "new_password": "BrandNew!Pass123",
            },
        )
        assert resp.status_code == 401


# ----- Role enforcement (writer) --------------------------------------------


class TestRoleEnforcement:
    def test_auditor_cannot_create_assessment(self, authed_client, client):
        # Owner invites an auditor
        invite = authed_client.post(
            "/api/v1/users",
            json={
                "email": "auditor@example.com",
                "full_name": "Auditor",
                "role": "auditor",
            },
        )
        temp = invite.json()["temporary_password"]
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "auditor@example.com", "password": temp},
        ).json()
        client.headers.update(
            {"Authorization": f"Bearer {login['access_token']}"}
        )
        # Auditor should still be able to read
        list_resp = client.get("/api/v1/assessments")
        assert list_resp.status_code == 200
        # But not create
        create_resp = client.post("/api/v1/assessments", json={})
        assert create_resp.status_code == 403
