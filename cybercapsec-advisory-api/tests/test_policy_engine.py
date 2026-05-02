"""Tests for the policy template engine."""
from pathlib import Path

import pytest

from app.services.policies.engine import (
    PolicyTemplate,
    TemplateMetadata,
    TemplateRenderError,
    build_default_variables,
    discover_templates,
    get_templates,
    load_template,
    render_policy,
)


# ----- Template discovery -----------------------------------------------------


class TestTemplateDiscovery:
    def test_discovers_all_v1_templates(self):
        templates = discover_templates()
        assert len(templates) >= 9, "Expected at least 9 v1 templates"

        expected_codes = {
            "information_security",
            "access_control",
            "data_protection",
            "data_retention",
            "incident_response",
            "acceptable_use",
            "vendor_management",
            "change_management",
            "backup_recovery",
            "security_awareness",
        }
        assert expected_codes.issubset(set(templates.keys()))

    def test_each_template_declares_used_variables(self):
        """No template references a variable that isn't declared in front-matter."""
        for code, template in get_templates().items():
            declared = template.declared_variable_names()
            used = template.used_variable_names()
            undeclared = used - declared
            assert not undeclared, (
                f"{code} uses undeclared variables: {sorted(undeclared)}"
            )

    def test_each_template_has_at_least_one_framework(self):
        for code, template in get_templates().items():
            assert template.metadata.framework_codes, (
                f"{code} declares no framework_codes"
            )

    def test_each_template_has_at_least_one_control_ref(self):
        for code, template in get_templates().items():
            assert template.metadata.control_refs, (
                f"{code} declares no control_refs"
            )

    def test_template_codes_are_unique(self):
        templates = get_templates()
        codes = [t.metadata.template_code for t in templates.values()]
        assert len(codes) == len(set(codes))


# ----- Loading edge cases -----------------------------------------------------


class TestTemplateLoading:
    def test_missing_frontmatter_raises(self, tmp_path):
        p = tmp_path / "bad.md"
        p.write_text("Just markdown with no front-matter.")
        with pytest.raises(ValueError, match="front-matter"):
            load_template(p)

    def test_malformed_yaml_raises(self, tmp_path):
        p = tmp_path / "bad.md"
        p.write_text("---\nthis is: not: valid: yaml\n---\nbody")
        with pytest.raises(ValueError):
            load_template(p)

    def test_undeclared_variable_in_body_raises(self, tmp_path):
        p = tmp_path / "bad.md"
        p.write_text(
            "---\n"
            "template_code: test\n"
            "title: Test\n"
            "variables:\n"
            "  - name: foo\n"
            "---\n"
            "Body with {{ undeclared_variable }}."
        )
        with pytest.raises(ValueError, match="undeclared variables"):
            load_template(p)


# ----- Rendering --------------------------------------------------------------


class _FakeCompany:
    def __init__(self):
        self.name = "Test Co"
        self.country = "NG"
        self.slug = "test-co"

        class _S:
            value = "fintech"

        self.sector = _S()


class TestRendering:
    def test_renders_with_company_defaults(self):
        templates = get_templates()
        template = templates["information_security"]
        company = _FakeCompany()
        variables = build_default_variables(company)
        rendered = render_policy(template, variables)

        assert "Test Co" in rendered
        assert "Information Security Policy" in rendered

    def test_overrides_take_precedence(self):
        template = get_templates()["information_security"]
        company = _FakeCompany()
        variables = build_default_variables(company)
        variables["effective_date"] = "2025-01-01"
        rendered = render_policy(template, variables)
        assert "2025-01-01" in rendered

    def test_missing_required_variable_raises(self):
        template = get_templates()["information_security"]
        # Don't pass any variables — required ones will be missing
        with pytest.raises(TemplateRenderError):
            render_policy(template, {})

    def test_default_used_when_variable_missing(self):
        """Variables with declared defaults shouldn't error."""
        template = get_templates()["information_security"]
        company = _FakeCompany()
        variables = build_default_variables(company)
        # remove the variable that has a default; engine should fill it
        variables.pop("review_cadence", None)
        rendered = render_policy(template, variables)
        assert "annually" in rendered  # the default

    def test_all_v1_templates_render_with_defaults(self):
        """Every shipped template must render successfully against company defaults."""
        company = _FakeCompany()
        variables = build_default_variables(company)
        for code, template in get_templates().items():
            try:
                rendered = render_policy(template, variables)
            except TemplateRenderError as exc:
                pytest.fail(f"Template {code} failed to render: {exc}")
            assert "Test Co" in rendered, f"{code} did not include company name"
            assert len(rendered) > 500, f"{code} rendered suspiciously short"


# ----- Default variables ------------------------------------------------------


class TestDefaultVariables:
    def test_builds_from_company(self):
        company = _FakeCompany()
        vars = build_default_variables(company)
        assert vars["company_name"] == "Test Co"
        assert vars["company_country"] == "NG"
        assert vars["company_sector"] == "fintech"
        assert "@" in vars["contact_email"]
        assert "@" in vars["dpo_email"]
