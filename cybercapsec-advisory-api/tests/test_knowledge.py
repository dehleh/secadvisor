"""Tests for the knowledge retrieval layer."""
from app.services.ai.knowledge import (
    InMemoryRetriever,
    KnowledgeSnippet,
    default_retriever,
)


class TestInMemoryRetriever:
    def test_retriever_has_seed_corpus(self):
        snippets = default_retriever.retrieve(limit=100)
        # Sanity: we seeded enough for v1
        assert len(snippets) >= 15

    def test_get_by_id(self):
        snippet = default_retriever.get_by_id("ndpa.security_processing")
        assert snippet is not None
        assert "NDPA" in snippet.title

    def test_get_by_unknown_id_returns_none(self):
        assert default_retriever.get_by_id("does_not_exist") is None

    def test_filter_by_framework(self):
        ndpa_only = default_retriever.retrieve(framework_codes=["ndpa"], limit=100)
        for s in ndpa_only:
            assert "ndpa" in s.framework_codes

    def test_filter_by_multiple_frameworks(self):
        results = default_retriever.retrieve(
            framework_codes=["ndpa", "cbn_cyber"], limit=100
        )
        for s in results:
            assert s.framework_codes & {"ndpa", "cbn_cyber"}

    def test_tag_overlap_ranks_higher(self):
        # Snippets matching more requested tags should appear first
        results = default_retriever.retrieve(
            framework_codes=["soc2"],
            tags=["mfa", "access_control"],
            limit=10,
        )
        # The first result should have at least one tag overlap
        assert results[0].tags & {"mfa", "access_control"}

    def test_limit_caps_results(self):
        results = default_retriever.retrieve(limit=3)
        assert len(results) == 3

    def test_unknown_framework_returns_empty(self):
        assert default_retriever.retrieve(framework_codes=["fake"]) == []

    def test_custom_corpus(self):
        custom = InMemoryRetriever(
            [
                KnowledgeSnippet(
                    id="custom.1",
                    title="Custom",
                    content="Custom snippet content",
                    framework_codes=frozenset({"soc2"}),
                )
            ]
        )
        assert len(custom.retrieve()) == 1
        assert custom.get_by_id("custom.1") is not None
