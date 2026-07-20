"""Tests for the roadmap tracker API."""
import pytest


@pytest.fixture
def full_responses() -> dict:
    return {
        "co.primary_country": "NG",
        "co.serves_eu_users": False,
        "co.has_us_customers": True,
        "co.team_size": "11-50",
        "da.data_types": ["names_emails", "financial"],
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


def _submit(client, full_responses) -> dict:
    created = client.post("/api/v1/assessments", json={}).json()
    aid = created["id"]
    client.patch(
        f"/api/v1/assessments/{aid}/responses", json={"responses": full_responses}
    )
    return client.post(f"/api/v1/assessments/{aid}/submit").json()


# ----- Auto-seeding on report generation -------------------------------------


class TestAutoSeed:
    def test_submit_auto_seeds_roadmap_items(self, authed_client, full_responses):
        _submit(authed_client, full_responses)
        resp = authed_client.get("/api/v1/roadmap/items")
        assert resp.status_code == 200
        items = resp.json()
        # The mock advisor produces 5+ tasks for our realistic responses
        assert len(items) >= 5

    def test_seeded_items_match_report_tasks(self, authed_client, full_responses):
        body = _submit(authed_client, full_responses)
        rid = body["report_id"]
        report = authed_client.get(f"/api/v1/reports/{rid}").json()

        report_task_ids = {t["id"] for t in report["roadmap"]}
        roadmap_items = authed_client.get(
            f"/api/v1/roadmap/items?report_id={rid}"
        ).json()
        seeded_source_ids = {i["source_task_id"] for i in roadmap_items}

        assert report_task_ids == seeded_source_ids


# ----- Manual seeding --------------------------------------------------------


class TestManualSeed:
    def test_seed_endpoint_idempotent(self, authed_client, full_responses):
        body = _submit(authed_client, full_responses)
        rid = body["report_id"]

        # Items are already auto-seeded; calling seed again should add zero
        resp = authed_client.post(f"/api/v1/roadmap/seed-from-report/{rid}")
        assert resp.status_code == 201
        assert resp.json()["seeded"] == 0


# ----- Item updates ----------------------------------------------------------


class TestItemUpdates:
    def test_update_status_to_in_progress(self, authed_client, full_responses):
        _submit(authed_client, full_responses)
        items = authed_client.get("/api/v1/roadmap/items").json()
        iid = items[0]["id"]

        resp = authed_client.patch(
            f"/api/v1/roadmap/items/{iid}",
            json={"status": "in_progress"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_marking_done_stamps_completed_at(
        self, authed_client, full_responses
    ):
        _submit(authed_client, full_responses)
        items = authed_client.get("/api/v1/roadmap/items").json()
        iid = items[0]["id"]

        resp = authed_client.patch(
            f"/api/v1/roadmap/items/{iid}",
            json={"status": "done"},
        )
        assert resp.json()["completed_at"] is not None

    def test_un_done_clears_completed_at(self, authed_client, full_responses):
        _submit(authed_client, full_responses)
        items = authed_client.get("/api/v1/roadmap/items").json()
        iid = items[0]["id"]

        authed_client.patch(
            f"/api/v1/roadmap/items/{iid}", json={"status": "done"}
        )
        resp = authed_client.patch(
            f"/api/v1/roadmap/items/{iid}",
            json={"status": "in_progress"},
        )
        assert resp.json()["completed_at"] is None

    def test_blocked_requires_reason(self, authed_client, full_responses):
        _submit(authed_client, full_responses)
        items = authed_client.get("/api/v1/roadmap/items").json()
        iid = items[0]["id"]

        no_reason = authed_client.patch(
            f"/api/v1/roadmap/items/{iid}",
            json={"status": "blocked"},
        )
        assert no_reason.status_code == 422

        with_reason = authed_client.patch(
            f"/api/v1/roadmap/items/{iid}",
            json={"status": "blocked", "blocked_reason": "Awaiting vendor response."},
        )
        assert with_reason.status_code == 200

    def test_assign_to_user_in_company(self, authed_client, full_responses):
        # Get current user id
        me = authed_client.get("/api/v1/auth/me").json()
        _submit(authed_client, full_responses)
        items = authed_client.get("/api/v1/roadmap/items").json()
        iid = items[0]["id"]

        resp = authed_client.patch(
            f"/api/v1/roadmap/items/{iid}",
            json={"assignee_user_id": me["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["assignee_user_id"] == me["id"]

    def test_assign_to_unknown_user_404s(self, authed_client, full_responses):
        _submit(authed_client, full_responses)
        items = authed_client.get("/api/v1/roadmap/items").json()
        iid = items[0]["id"]

        resp = authed_client.patch(
            f"/api/v1/roadmap/items/{iid}",
            json={"assignee_user_id": "no-such-user"},
        )
        assert resp.status_code == 404


# ----- Filters and progress --------------------------------------------------


class TestRoadmapQueries:
    def test_filter_by_status(self, authed_client, full_responses):
        _submit(authed_client, full_responses)
        items = authed_client.get("/api/v1/roadmap/items").json()
        iid = items[0]["id"]
        authed_client.patch(
            f"/api/v1/roadmap/items/{iid}", json={"status": "done"}
        )

        done_items = authed_client.get(
            "/api/v1/roadmap/items?status_filter=done"
        ).json()
        assert len(done_items) == 1
        assert done_items[0]["id"] == iid

    def test_progress_aggregates(self, authed_client, full_responses):
        _submit(authed_client, full_responses)
        items = authed_client.get("/api/v1/roadmap/items").json()
        # Mark one done, one in_progress
        authed_client.patch(
            f"/api/v1/roadmap/items/{items[0]['id']}", json={"status": "done"}
        )
        authed_client.patch(
            f"/api/v1/roadmap/items/{items[1]['id']}",
            json={"status": "in_progress"},
        )

        progress = authed_client.get("/api/v1/roadmap/progress").json()
        assert progress["total"] == len(items)
        assert progress["done"] == 1
        assert progress["in_progress"] == 1
        assert progress["completion_pct"] == round(1 / len(items) * 100)


# ----- Tenant isolation ------------------------------------------------------


class TestRoadmapIsolation:
    def test_other_company_cannot_see_items(
        self, client, signup_payload, full_responses, license_company
    ):
        # Company A
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
        _submit(client, full_responses)
        a_items = client.get("/api/v1/roadmap/items").json()
        assert len(a_items) > 0

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

        b_items = client.get("/api/v1/roadmap/items").json()
        assert b_items == []

        # Cross-tenant lookup of an item id 404s
        a_item_id = a_items[0]["id"]
        assert client.get(f"/api/v1/roadmap/items/{a_item_id}").status_code == 404
