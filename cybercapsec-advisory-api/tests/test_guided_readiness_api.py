"""Guided readiness API tests."""


def test_guided_readiness_profile_lifecycle(authed_client):
    initial = authed_client.get("/api/v1/guided-readiness")
    assert initial.status_code == 200
    assert initial.json() is None

    payload = {
        "selected_goal": "need_pci_dss",
        "target_framework": "pci_dss",
        "program_profile": {
            "objective": "secure_customer_data",
            "targetFrameworks": ["pci_dss"],
        },
        "scope_answers": {"payment_flow": "redirect_provider"},
        "baseline_answers": {"mfa_admins": "yes"},
        "questionnaire_drafts": [
            {
                "question": "Do you require MFA?",
                "answer": "Yes, MFA is required for administrative systems.",
            }
        ],
        "readiness_notes": "Founder is preparing payment-security evidence.",
    }

    created = authed_client.put("/api/v1/guided-readiness", json=payload)
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["selected_goal"] == "need_pci_dss"
    assert body["target_framework"] == "pci_dss"
    assert body["scope_answers"]["payment_flow"] == "redirect_provider"
    assert body["baseline_answers"]["mfa_admins"] == "yes"

    updated = authed_client.put(
        "/api/v1/guided-readiness",
        json={"target_framework": "soc2", "scope_answers": {"owners": "named"}},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["selected_goal"] == "need_pci_dss"
    assert updated.json()["target_framework"] == "soc2"
    assert updated.json()["scope_answers"] == {"owners": "named"}

    deleted = authed_client.delete("/api/v1/guided-readiness")
    assert deleted.status_code == 204
    assert authed_client.get("/api/v1/guided-readiness").json() is None
