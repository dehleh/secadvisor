"""Policy template engine.

Templates live as Markdown files with YAML front-matter. The front-matter
declares metadata (template_code, version, frameworks/controls satisfied,
declared variables); the body is a Jinja2 template that renders against
company-specific values.

Files are auto-discovered from `templates/`. Adding a new policy: drop a
.md file in that directory, add the matching code to PolicyTemplateCode
in models, and tests will pick it up.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined, TemplateError, meta
from pydantic import BaseModel, Field

from app.models import PolicyTemplateCode


TEMPLATES_DIR = Path(__file__).parent / "templates"

# StrictUndefined: any reference to an unprovided variable raises rather
# than rendering a silent empty string. Critical for compliance documents.
_jinja_env = Environment(
    autoescape=False,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)


class TemplateVariable(BaseModel):
    """A declared variable a template needs at render time."""
    name: str
    label: str | None = None
    description: str | None = None
    required: bool = True
    default: Any | None = None

    def display_label(self) -> str:
        """Return label or a humanized version of name."""
        if self.label:
            return self.label
        return self.name.replace("_", " ").capitalize()


class TemplateMetadata(BaseModel):
    """Front-matter schema for a policy template."""
    template_code: str
    template_version: str = "1.0.0"
    title: str
    description: str = ""
    framework_codes: list[str] = Field(default_factory=list)
    control_refs: list[dict[str, str]] = Field(default_factory=list)
    variables: list[TemplateVariable] = Field(default_factory=list)


@dataclass(frozen=True)
class PolicyTemplate:
    metadata: TemplateMetadata
    body_template: str
    file_path: Path

    def declared_variable_names(self) -> set[str]:
        return {v.name for v in self.metadata.variables}

    def used_variable_names(self) -> set[str]:
        """Variables actually referenced in the Jinja body."""
        ast = _jinja_env.parse(self.body_template)
        return meta.find_undeclared_variables(ast)


class TemplateRenderError(Exception):
    """Raised when a template cannot be rendered (missing var, syntax, etc.)."""


# ----- Loading ----------------------------------------------------------------


def _split_frontmatter(raw: str, file_path: Path) -> tuple[dict, str]:
    """Split a Markdown file with YAML front-matter into (metadata, body)."""
    if not raw.startswith("---"):
        raise ValueError(f"{file_path.name}: missing YAML front-matter delimiter")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{file_path.name}: malformed front-matter")
    _, frontmatter_raw, body = parts
    try:
        metadata = yaml.safe_load(frontmatter_raw) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{file_path.name}: invalid YAML front-matter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError(f"{file_path.name}: front-matter must be a YAML mapping")
    return metadata, body.lstrip("\n")


def load_template(file_path: Path) -> PolicyTemplate:
    raw = file_path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(raw, file_path)
    metadata = TemplateMetadata.model_validate(fm)

    template = PolicyTemplate(metadata=metadata, body_template=body, file_path=file_path)

    # Validate: every variable referenced in the body must be declared
    declared = template.declared_variable_names()
    used = template.used_variable_names()
    undeclared = used - declared
    if undeclared:
        raise ValueError(
            f"{file_path.name}: template uses undeclared variables: "
            f"{sorted(undeclared)}"
        )

    return template


def discover_templates(directory: Path | None = None) -> dict[str, PolicyTemplate]:
    """Load every .md template from the templates directory.

    Returns a dict keyed by template_code for easy lookup.
    """
    directory = directory or TEMPLATES_DIR
    out: dict[str, PolicyTemplate] = {}
    for path in sorted(directory.glob("*.md")):
        template = load_template(path)
        if template.metadata.template_code in out:
            raise ValueError(
                f"Duplicate template_code '{template.metadata.template_code}' "
                f"in {path.name}"
            )
        out[template.metadata.template_code] = template
    return out


# ----- Rendering --------------------------------------------------------------


def render_policy(
    template: PolicyTemplate,
    variables: dict[str, Any],
) -> str:
    """Render a template against a variable dict.

    Missing required variables fall back to declared defaults. If neither
    is present and the variable is referenced, raises TemplateRenderError.
    """
    merged = dict(variables)
    for var in template.metadata.variables:
        if var.name not in merged:
            if var.default is not None:
                merged[var.name] = var.default
            elif var.required:
                # Will trigger StrictUndefined when Jinja hits the reference
                pass

    try:
        jinja_template = _jinja_env.from_string(template.body_template)
        return jinja_template.render(**merged)
    except TemplateError as exc:
        raise TemplateRenderError(
            f"Failed to render {template.metadata.template_code}: {exc}"
        ) from exc


# ----- Variable inference -----------------------------------------------------


def build_default_variables(company) -> dict[str, Any]:
    """Build a default variable dict from a Company model.

    Most templates pull from these. Render-time overrides win.
    """
    return {
        "company_name": company.name,
        "company_country": company.country,
        "company_sector": company.sector.value if company.sector else "other",
        "effective_date": "TBD — set at publication",
        "owner": "Chief Executive Officer",
        "review_cadence": "annually",
        "contact_email": f"security@{company.slug}.com",
        "dpo_name": "TBD",
        "dpo_email": f"dpo@{company.slug}.com",
        "data_retention_years": 7,
    }


# ----- Registry singleton -----------------------------------------------------

_template_cache: dict[str, PolicyTemplate] | None = None


def get_templates() -> dict[str, PolicyTemplate]:
    """Cached template registry."""
    global _template_cache
    if _template_cache is None:
        _template_cache = discover_templates()
    return _template_cache


def reset_template_cache() -> None:
    """For tests."""
    global _template_cache
    _template_cache = None


def get_template(code: str | PolicyTemplateCode) -> PolicyTemplate | None:
    code_str = code.value if isinstance(code, PolicyTemplateCode) else code
    return get_templates().get(code_str)
