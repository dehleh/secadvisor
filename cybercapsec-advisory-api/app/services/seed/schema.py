"""Pydantic schemas for seed YAML files.

Every YAML file under app/data/ is validated by one of these models before
loading. The seed loader fails loud on bad data — typos, duplicate codes,
references to nonexistent frameworks — so we never silently corrupt the DB.
"""
from pydantic import BaseModel, Field, field_validator

from app.models import FrameworkCode, MappingStrength


class ControlSeed(BaseModel):
    """One row in a framework's controls list."""
    code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=3, max_length=500)
    description: str = Field(min_length=10)
    category: str | None = None
    guidance: str | None = None


class FrameworkSeed(BaseModel):
    """One YAML file per framework."""
    code: FrameworkCode
    name: str = Field(min_length=2, max_length=255)
    version: str = Field(min_length=1, max_length=50)
    jurisdiction: str | None = None
    description: str | None = None
    source_url: str | None = None
    controls: list[ControlSeed] = Field(min_length=1)

    @field_validator("controls")
    @classmethod
    def control_codes_unique(cls, v: list[ControlSeed]) -> list[ControlSeed]:
        codes = [c.code for c in v]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate control codes within a framework")
        return v


class MappingSeed(BaseModel):
    """One mapping between two controls in different frameworks."""
    source_framework: FrameworkCode
    source_code: str
    target_framework: FrameworkCode
    target_code: str
    strength: MappingStrength
    notes: str | None = None

    @field_validator("source_framework", "target_framework")
    @classmethod
    def normalize_framework(cls, v: FrameworkCode) -> FrameworkCode:
        return v


class MappingsFile(BaseModel):
    """The mappings.yaml file is one big list."""
    mappings: list[MappingSeed]


class KnowledgeSnippetSeed(BaseModel):
    """One YAML file per knowledge snippet, or grouped per framework."""
    id: str = Field(min_length=3, max_length=100)
    title: str = Field(min_length=3, max_length=255)
    content: str = Field(min_length=20)
    framework_codes: list[FrameworkCode] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None


class KnowledgeFile(BaseModel):
    """A YAML file containing multiple snippets."""
    snippets: list[KnowledgeSnippetSeed]

    @field_validator("snippets")
    @classmethod
    def snippet_ids_unique(
        cls, v: list[KnowledgeSnippetSeed]
    ) -> list[KnowledgeSnippetSeed]:
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate snippet IDs within a file")
        return v
