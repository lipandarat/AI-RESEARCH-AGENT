"""
Scientific Database Integration Module

Provides access to cross-domain scientific knowledge through:
- arXiv (research papers)
- PubMed (biomedical literature)
- Semantic Scholar (CS papers)
- CrossRef (citation data)
- Custom APIs
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import httpx
from loguru import logger


class DatabaseType(str, Enum):
    """Supported scientific databases"""
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    CROSSREF = "crossref"
    CUSTOM = "custom"


@dataclass
class Paper:
    """Scientific paper metadata"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    publication_date: Optional[datetime]
    source: DatabaseType
    url: Optional[str] = None
    doi: Optional[str] = None
    citations: int = 0
    keywords: List[str] = None
    full_text: Optional[str] = None


@dataclass
class SearchQuery:
    """Structured search query"""
    keywords: List[str]
    domain: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    max_results: int = 10
    sort_by: str = "relevance"  # relevance, date, citations


class ScientificDatabaseIntegration:
    """
    Integration layer for scientific databases and APIs.

    Provides unified interface to query multiple scientific
    knowledge sources for cross-domain research.
    """

    def __init__(
        self,
        arxiv_enabled: bool = True,
        pubmed_enabled: bool = True,
        semantic_scholar_api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.arxiv_enabled = arxiv_enabled
        self.pubmed_enabled = pubmed_enabled
        self.semantic_scholar_api_key = semantic_scholar_api_key
        self.timeout = timeout

        # HTTP client for async requests
        self.client = httpx.AsyncClient(timeout=timeout)

        # Database endpoints
        self.endpoints = {
            DatabaseType.ARXIV: "http://export.arxiv.org/api/query",
            DatabaseType.PUBMED: "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            DatabaseType.SEMANTIC_SCHOLAR: "https://api.semanticscholar.org/graph/v1",
            DatabaseType.CROSSREF: "https://api.crossref.org/works"
        }

    async def search(
        self,
        query: SearchQuery,
        databases: Optional[List[DatabaseType]] = None
    ) -> List[Paper]:
        """
        Search across multiple scientific databases.

        Args:
            query: Structured search query
            databases: List of databases to search (None = all enabled)

        Returns:
            List of Paper objects from all databases
        """
        if databases is None:
            databases = self._get_enabled_databases()

        logger.info(f"Searching {len(databases)} databases for: {query.keywords}")

        all_papers = []

        for db in databases:
            try:
                papers = await self._search_database(db, query)
                all_papers.extend(papers)
                logger.debug(f"Found {len(papers)} papers in {db}")
            except Exception as e:
                logger.warning(f"Search failed for {db}: {e}")

        # Sort by relevance/date and limit results
        all_papers = self._rank_papers(all_papers, query)

        logger.success(f"Total papers found: {len(all_papers)}")
        return all_papers[:query.max_results]

    async def get_paper_details(
        self,
        paper_id: str,
        source: DatabaseType
    ) -> Optional[Paper]:
        """
        Retrieve full paper details including abstract and metadata.

        Args:
            paper_id: Paper identifier
            source: Database source

        Returns:
            Complete Paper object with full details
        """
        logger.info(f"Fetching paper {paper_id} from {source}")

        try:
            if source == DatabaseType.ARXIV:
                return await self._get_arxiv_paper(paper_id)
            elif source == DatabaseType.SEMANTIC_SCHOLAR:
                return await self._get_semantic_scholar_paper(paper_id)
            # Add other sources as needed

        except Exception as e:
            logger.error(f"Failed to fetch paper: {e}")
            return None

    async def get_related_papers(
        self,
        paper: Paper,
        max_results: int = 5
    ) -> List[Paper]:
        """
        Find papers related to given paper through citations.

        Args:
            paper: Reference paper
            max_results: Maximum related papers to return

        Returns:
            List of related papers
        """
        logger.info(f"Finding papers related to: {paper.title}")

        # Use Semantic Scholar for citation network
        if paper.doi or paper.id:
            try:
                related = await self._get_semantic_scholar_related(
                    paper.doi or paper.id
                )
                return related[:max_results]
            except Exception as e:
                logger.warning(f"Failed to get related papers: {e}")

        return []

    async def _search_database(
        self,
        database: DatabaseType,
        query: SearchQuery
    ) -> List[Paper]:
        """Search specific database"""

        if database == DatabaseType.ARXIV:
            return await self._search_arxiv(query)
        elif database == DatabaseType.PUBMED:
            return await self._search_pubmed(query)
        elif database == DatabaseType.SEMANTIC_SCHOLAR:
            return await self._search_semantic_scholar(query)

        return []

    async def _search_arxiv(self, query: SearchQuery) -> List[Paper]:
        """Search arXiv database"""

        # Build arXiv query string
        search_query = " AND ".join(query.keywords)
        params = {
            "search_query": f"all:{search_query}",
            "start": 0,
            "max_results": query.max_results,
            "sortBy": "relevance" if query.sort_by == "relevance" else "submittedDate",
            "sortOrder": "descending"
        }

        try:
            response = await self.client.get(
                self.endpoints[DatabaseType.ARXIV],
                params=params
            )
            response.raise_for_status()

            # Parse arXiv XML response
            papers = self._parse_arxiv_response(response.text)
            return papers

        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []

    async def _search_semantic_scholar(self, query: SearchQuery) -> List[Paper]:
        """Search Semantic Scholar"""

        if not self.semantic_scholar_api_key:
            logger.warning("Semantic Scholar API key not provided")
            return []

        search_query = " ".join(query.keywords)
        url = f"{self.endpoints[DatabaseType.SEMANTIC_SCHOLAR]}/paper/search"

        params = {
            "query": search_query,
            "limit": query.max_results,
            "fields": "paperId,title,abstract,authors,year,citationCount,url"
        }

        headers = {"x-api-key": self.semantic_scholar_api_key}

        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            papers = self._parse_semantic_scholar_response(data)
            return papers

        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []

    async def _search_pubmed(self, query: SearchQuery) -> List[Paper]:
        """Search PubMed (simplified implementation)"""

        # PubMed search is a 2-step process: search then fetch
        search_url = f"{self.endpoints[DatabaseType.PUBMED]}/esearch.fcgi"

        search_query = " AND ".join(query.keywords)
        params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": query.max_results,
            "retmode": "json"
        }

        try:
            # Step 1: Get IDs
            response = await self.client.get(search_url, params=params)
            response.raise_for_status()

            data = response.json()
            ids = data.get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            # Step 2: Fetch details (simplified)
            papers = []
            for pmid in ids[:query.max_results]:
                papers.append(Paper(
                    id=pmid,
                    title=f"PubMed Article {pmid}",
                    authors=[],
                    abstract="",
                    publication_date=None,
                    source=DatabaseType.PUBMED,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                ))

            return papers

        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    async def _get_arxiv_paper(self, arxiv_id: str) -> Optional[Paper]:
        """Get full arXiv paper details"""

        params = {
            "id_list": arxiv_id,
            "max_results": 1
        }

        try:
            response = await self.client.get(
                self.endpoints[DatabaseType.ARXIV],
                params=params
            )
            response.raise_for_status()

            papers = self._parse_arxiv_response(response.text)
            return papers[0] if papers else None

        except Exception as e:
            logger.error(f"Failed to fetch arXiv paper: {e}")
            return None

    async def _get_semantic_scholar_paper(self, paper_id: str) -> Optional[Paper]:
        """Get full Semantic Scholar paper details"""

        if not self.semantic_scholar_api_key:
            return None

        url = f"{self.endpoints[DatabaseType.SEMANTIC_SCHOLAR]}/paper/{paper_id}"
        params = {"fields": "paperId,title,abstract,authors,year,citationCount,url"}
        headers = {"x-api-key": self.semantic_scholar_api_key}

        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            return self._parse_semantic_scholar_paper(data)

        except Exception as e:
            logger.error(f"Failed to fetch Semantic Scholar paper: {e}")
            return None

    async def _get_semantic_scholar_related(self, paper_id: str) -> List[Paper]:
        """Get papers that cite or are cited by given paper"""

        if not self.semantic_scholar_api_key:
            return []

        url = f"{self.endpoints[DatabaseType.SEMANTIC_SCHOLAR]}/paper/{paper_id}/citations"
        params = {"fields": "paperId,title,abstract,authors,year", "limit": 10}
        headers = {"x-api-key": self.semantic_scholar_api_key}

        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            papers = []
            for item in data.get("data", []):
                citing_paper = item.get("citingPaper", {})
                if citing_paper:
                    papers.append(self._parse_semantic_scholar_paper(citing_paper))

            return papers

        except Exception as e:
            logger.error(f"Failed to get related papers: {e}")
            return []

    def _parse_arxiv_response(self, xml_text: str) -> List[Paper]:
        """Parse arXiv XML response"""
        import xml.etree.ElementTree as ET
        from datetime import datetime

        papers = []

        try:
            root = ET.fromstring(xml_text)

            # arXiv uses Atom namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            for entry in root.findall('atom:entry', ns):
                # Extract basic metadata
                title_elem = entry.find('atom:title', ns)
                title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else ""

                summary_elem = entry.find('atom:summary', ns)
                abstract = summary_elem.text.strip() if summary_elem is not None else ""

                # Extract arXiv ID from id URL
                id_elem = entry.find('atom:id', ns)
                arxiv_url = id_elem.text if id_elem is not None else ""
                arxiv_id = arxiv_url.split('/abs/')[-1] if arxiv_url else ""

                # Extract authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)

                # Extract publication date
                published_elem = entry.find('atom:published', ns)
                publication_date = None
                if published_elem is not None:
                    try:
                        publication_date = datetime.fromisoformat(
                            published_elem.text.replace('Z', '+00:00')
                        )
                    except:
                        pass

                # Extract DOI if available
                doi = None
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'doi':
                        doi = link.get('href', '').split('doi.org/')[-1]

                papers.append(Paper(
                    id=arxiv_id,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    publication_date=publication_date,
                    source=DatabaseType.ARXIV,
                    url=arxiv_url,
                    doi=doi,
                    citations=0,  # arXiv API doesn't provide citation counts
                    keywords=[]
                ))

        except Exception as e:
            logger.error(f"Failed to parse arXiv XML: {e}")

        return papers

    def _parse_semantic_scholar_response(self, data: Dict) -> List[Paper]:
        """Parse Semantic Scholar JSON response"""
        papers = []

        for item in data.get("data", []):
            papers.append(self._parse_semantic_scholar_paper(item))

        return papers

    def _parse_semantic_scholar_paper(self, data: Dict) -> Paper:
        """Parse single Semantic Scholar paper"""
        authors = [a.get("name", "") for a in data.get("authors", [])]

        return Paper(
            id=data.get("paperId", ""),
            title=data.get("title", ""),
            authors=authors,
            abstract=data.get("abstract", ""),
            publication_date=None,  # Parse year if needed
            source=DatabaseType.SEMANTIC_SCHOLAR,
            url=data.get("url"),
            citations=data.get("citationCount", 0)
        )

    def _rank_papers(self, papers: List[Paper], query: SearchQuery) -> List[Paper]:
        """Rank papers by relevance or other criteria"""

        if query.sort_by == "citations":
            return sorted(papers, key=lambda p: p.citations, reverse=True)
        elif query.sort_by == "date":
            return sorted(
                papers,
                key=lambda p: p.publication_date or datetime.min,
                reverse=True
            )

        # Default: keep original order (relevance from source)
        return papers

    def _get_enabled_databases(self) -> List[DatabaseType]:
        """Get list of enabled databases"""
        enabled = []

        if self.arxiv_enabled:
            enabled.append(DatabaseType.ARXIV)
        if self.pubmed_enabled:
            enabled.append(DatabaseType.PUBMED)
        if self.semantic_scholar_api_key:
            enabled.append(DatabaseType.SEMANTIC_SCHOLAR)

        return enabled

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
