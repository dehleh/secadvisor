"""Tests for the policy lifecycle service and API."""
import pytest


# ----- Policy template endpoints ---------------------------------------------


class TestPolicyTemplateEndpoints:
    def test_list_templates(self, authed_client):
        resp = authed_client.get("/api/v1/policy-templates")
        assert resp.status_code == 200
        templates = resp.json()
        assert len(templates) >= 9

    def test_template_includes_variables(self, authed_client):
        resp = authed_client.get("/api/v1/policy-templates/information_security")
        assert resp.status_code == 200
        body = resp.json()
        assert body["template_code"] == "information_security"
        assert body["framework_codes"]
        assert body["variables"]
        # Each variable has the expected shape
        for v in body["variables"]:
            assert "name" in v
            assert "label" in v
            assert "required" in v

    def test_unknown_template_404s(self, authed_client):
        resp = authed_client.get("/api/v1/policy-templates/nope")
        assert resp.status_code == 404

    def test_templates_require_auth(self, client):
        assert client.get("/api/v1/policy-templates").status_code == 401


# ----- Policy generation -----------------------------------------------------


class TestPolicyGeneration:
    def test_generate_creates_draft_policy(self, authed_client):
        resp = authed_client.post(
            "/api/v1/policies",
            json={"template_code": "information_security"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["template_code"] == "information_security"
        assert body["status"] == "draft"
        assert body["version"] == 1
        assert "Information Security Policy" in body["content"]

    def test_generate_with_overrides(self, authed_client):
        resp = authed_client.post(
            "/api/v1/policies",
            json={
                "template_code": "information_security",
                "variable_overrides": {"effective_date": "2025-03-01"},
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "2025-03-01" in body["content"]
        assert body["rendered_variables"]["effective_date"] == "2025-03-01"

    def test_generate_unknown_template_404s(self, authed_client):
        resp = authed_client.post(
            "/api/v1/policies",
            json={"template_code": "nope"},
        )
        # Pydantic enum validation rejects unknown codes at the schema layer
        assert resp.status_code == 422

    def test_starter_pack_generates_all(self, authed_client):
        resp = authed_client.post("/api/v1/policies/starter-pack")
        assert resp.status_code == 201
        body = resp.json()
        assert len(body["generated"]) >= 9

    def test_starter_pack_idempotent(self, authed_client):
        # First call generates everything
        first = authed_client.post("/api/v1/policies/starter-pack").json()
        assert len(first["generated"]) >= 9
        # Second call generates nothing because non-archived versions exist
        second = authed_client.post("/api/v1/policies/starter-pack").json()
        assert len(second["generated"]) == 0


# ----- Policy lifecycle ------------------------------------------------------


class TestPolicyLifecycle:
    def test_publish_transitions_status(self, authed_client):
        created = authed_client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        pid = created["id"]

        resp = authed_client.post(f"/api/v1/policies/{pid}/publish")
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    def test_publishing_archives_prior_version(self, authed_client):
        # Generate v1 + publish
        v1 = authed_client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        authed_client.post(f"/api/v1/policies/{v1['id']}/publish")

        # Generate v2 + publish — v1 should be archived
        v2 = authed_client.post(
            "/api/v1/policies",
            json={
                "template_code": "information_security",
                "variable_overrides": {"effective_date": "2026-01-01"},
            },
        ).json()
        assert v2["version"] == 2
        authed_client.post(f"/api/v1/policies/{v2['id']}/publish")

        # Reload v1 — should be archived now
        v1_after = authed_client.get(f"/api/v1/policies/{v1['id']}").json()
        assert v1_after["status"] == "archived"

    def test_archive_directly(self, authed_client):
        created = authed_client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        resp = authed_client.post(f"/api/v1/policies/{created['id']}/archive")
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

    def test_cannot_publish_archived_policy(self, authed_client):
        created = authed_client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        authed_client.post(f"/api/v1/policies/{created['id']}/archive")
        resp = authed_client.post(f"/api/v1/policies/{created['id']}/publish")
        assert resp.status_code == 409


# ----- Acknowledgments -------------------------------------------------------


class TestPolicyAcknowledgments:
    def test_acknowledge_published_policy(self, authed_client):
        created = authed_client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        authed_client.post(f"/api/v1/policies/{created['id']}/publish")

        resp = authed_client.post(
            f"/api/v1/policies/{created['id']}/acknowledge",
            json={"acknowledged_text": "I have read and agree."},
        )
        assert resp.status_code == 200
        assert resp.json()["acknowledged_text"] == "I have read and agree."

    def test_acknowledge_idempotent(self, authed_client):
        created = authed_client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        authed_client.post(f"/api/v1/policies/{created['id']}/publish")
        first = authed_client.post(
            f"/api/v1/policies/{created['id']}/acknowledge", json={}
        ).json()
        second = authed_client.post(
            f"/api/v1/policies/{created['id']}/acknowledge", json={}
        ).json()
        assert first["id"] == second["id"]

    def test_cannot_acknowledge_draft(self, authed_client):
        created = authed_client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        resp = authed_client.post(
            f"/api/v1/policies/{created['id']}/acknowledge", json={}
        )
        assert resp.status_code == 409

    def test_list_acknowledgments(self, authed_client):
        created = authed_client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        authed_client.post(f"/api/v1/policies/{created['id']}/publish")
        authed_client.post(
            f"/api/v1/policies/{created['id']}/acknowledge", json={}
        )

        resp = authed_client.get(
            f"/api/v1/policies/{created['id']}/acknowledgments"
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1


# ----- Tenant isolation ------------------------------------------------------


class TestPolicyIsolation:
    def test_other_company_cannot_see_policy(
        self, client, signup_payload, license_company
    ):
        # Company A creates a policy
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
        a_policy = client.post(
            "/api/v1/policies", json={"template_code": "information_security"}
        ).json()
        pid = a_policy["id"]

        # Company B can't see it
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

        assert client.get(f"/api/v1/policies/{pid}").status_code == 404
        assert client.get("/api/v1/policies").json() == []
