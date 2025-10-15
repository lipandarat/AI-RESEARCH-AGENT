"""
Tests for Scientific Database Integration Module
"""

import pytest
from ajul.core.scientific_db import (
    ScientificDatabaseIntegration,
    SearchQuery,
    DatabaseType,
    Paper
)


@pytest.mark.asyncio
async def test_arxiv_search():
    """Test arXiv database search"""
    db = ScientificDatabaseIntegration(
        arxiv_enabled=True,
        pubmed_enabled=False,
        semantic_scholar_api_key=None
    )

    query = SearchQuery(
        keywords=["machine learning", "neural networks"],
        max_results=5
    )

    try:
        papers = await db.search(query, databases=[DatabaseType.ARXIV])

        assert isinstance(papers, list)
        assert len(papers) <= query.max_results

        if papers:
            paper = papers[0]
            assert isinstance(paper, Paper)
            assert paper.source == DatabaseType.ARXIV
            assert paper.title
            assert paper.authors

    finally:
        await db.close()


@pytest.mark.asyncio
async def test_search_query_structure():
    """Test SearchQuery dataclass"""
    query = SearchQuery(
        keywords=["quantum computing"],
        domain="physics",
        max_results=10,
        sort_by="citations"
    )

    assert query.keywords == ["quantum computing"]
    assert query.domain == "physics"
    assert query.max_results == 10
    assert query.sort_by == "citations"


@pytest.mark.asyncio
async def test_paper_ranking():
    """Test paper ranking by citations"""
    db = ScientificDatabaseIntegration()

    papers = [
        Paper(
            id="1",
            title="Paper A",
            authors=["Author 1"],
            abstract="Abstract A",
            publication_date=None,
            source=DatabaseType.ARXIV,
            citations=100
        ),
        Paper(
            id="2",
            title="Paper B",
            authors=["Author 2"],
            abstract="Abstract B",
            publication_date=None,
            source=DatabaseType.ARXIV,
            citations=50
        ),
        Paper(
            id="3",
            title="Paper C",
            authors=["Author 3"],
            abstract="Abstract C",
            publication_date=None,
            source=DatabaseType.ARXIV,
            citations=200
        )
    ]

    query = SearchQuery(keywords=["test"], sort_by="citations")
    ranked = db._rank_papers(papers, query)

    assert ranked[0].citations == 200
    assert ranked[1].citations == 100
    assert ranked[2].citations == 50

    await db.close()


@pytest.mark.asyncio
async def test_enabled_databases():
    """Test database enablement"""
    db = ScientificDatabaseIntegration(
        arxiv_enabled=True,
        pubmed_enabled=True,
        semantic_scholar_api_key="test_key"
    )

    enabled = db._get_enabled_databases()

    assert DatabaseType.ARXIV in enabled
    assert DatabaseType.PUBMED in enabled
    assert DatabaseType.SEMANTIC_SCHOLAR in enabled

    await db.close()


@pytest.mark.asyncio
async def test_multiple_database_search():
    """Test searching across multiple databases"""
    db = ScientificDatabaseIntegration(
        arxiv_enabled=True,
        pubmed_enabled=True
    )

    query = SearchQuery(
        keywords=["artificial intelligence"],
        max_results=3
    )

    try:
        papers = await db.search(query)

        # Should get results from multiple sources
        sources = {p.source for p in papers}
        assert len(sources) >= 1  # At least one database should return results

    finally:
        await db.close()
