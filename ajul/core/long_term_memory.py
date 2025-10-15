"""
Long-term Memory System with RAG

Implements persistent memory for autonomous research agent:
- Stores experiment results and hypotheses
- Retrieves relevant past experiences
- Learns from successes and failures
- Evolves knowledge over time

Uses vector embeddings for semantic retrieval.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import hashlib

import numpy as np
from loguru import logger

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available, using fallback memory")

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available for embeddings")


class MemoryType(str, Enum):
    """Types of memory following Mem0 architecture"""
    WORKING = "working"  # Short-term session awareness
    FACTUAL = "factual"  # Long-term structured knowledge
    EPISODIC = "episodic"  # Specific past conversations
    SEMANTIC = "semantic"  # General knowledge over time


@dataclass
class MemoryEntry:
    """Single memory entry"""
    id: str
    content: str
    memory_type: MemoryType
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: datetime = None
    importance_score: float = 0.5  # 0-1
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    decay_factor: float = 1.0  # Decreases over time

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ExperimentMemory:
    """Memory of a specific experiment"""
    experiment_id: str
    hypothesis_id: str
    domain: str
    methodology: str
    results: Dict[str, Any]
    conclusion: str
    success: bool
    timestamp: datetime
    papers_referenced: List[str] = None
    code_artifacts: List[str] = None
    insights: List[str] = None


@dataclass
class HypothesisMemory:
    """Memory of a hypothesis and its outcomes"""
    hypothesis_id: str
    title: str
    description: str
    domain: str
    tested: bool
    validated: bool
    experiments_count: int
    insights_gained: List[str]
    timestamp: datetime


class LongTermMemory:
    """
    RAG-based long-term memory system for research agent.

    Stores and retrieves:
    - Experiment results
    - Hypotheses tested
    - Insights discovered
    - Domain knowledge
    - Successful/failed strategies

    Features:
    - Semantic search via embeddings
    - Memory decay (forget irrelevant info)
    - Importance scoring
    - Multimodal support (text + metadata)
    """

    def __init__(
        self,
        collection_name: str = "ajul_research_memory",
        persist_directory: str = "./data/memory",
        embedding_model: str = "text-embedding-3-small",
        openai_api_key: Optional[str] = None,
        use_chromadb: bool = True
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model

        # Initialize embedding client
        if OPENAI_AVAILABLE and openai_api_key:
            self.embedding_client = AsyncOpenAI(api_key=openai_api_key)
        else:
            self.embedding_client = None
            logger.warning("No embedding client available")

        # Initialize vector store
        if use_chromadb and CHROMADB_AVAILABLE:
            self._init_chromadb()
        else:
            self._init_fallback_memory()

        # Memory statistics
        self.stats = {
            "total_memories": 0,
            "retrievals": 0,
            "avg_retrieval_time": 0.0
        }

    def _init_chromadb(self):
        """Initialize ChromaDB vector store"""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Ajul AI Research Agent Memory"}
            )

            logger.info(f"ChromaDB initialized: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self._init_fallback_memory()

    def _init_fallback_memory(self):
        """Fallback in-memory storage"""
        self.memory_store: Dict[str, MemoryEntry] = {}
        logger.info("Using fallback in-memory storage")

    async def store_experiment(
        self,
        experiment: ExperimentMemory
    ) -> str:
        """
        Store experiment result in long-term memory.

        Args:
            experiment: Experiment memory to store

        Returns:
            Memory ID
        """
        logger.info(f"Storing experiment: {experiment.experiment_id}")

        # Create searchable content
        content = self._create_experiment_content(experiment)

        metadata = {
            "type": "experiment",
            "experiment_id": experiment.experiment_id,
            "hypothesis_id": experiment.hypothesis_id,
            "domain": experiment.domain,
            "success": experiment.success,
            "timestamp": experiment.timestamp.isoformat()
        }

        memory_id = await self.store_memory(
            content=content,
            memory_type=MemoryType.EPISODIC,
            metadata=metadata,
            importance=0.8 if experiment.success else 0.6
        )

        logger.success(f"Experiment stored: {memory_id}")
        return memory_id

    async def store_hypothesis(
        self,
        hypothesis: HypothesisMemory
    ) -> str:
        """
        Store hypothesis and its outcome in memory.

        Args:
            hypothesis: Hypothesis memory to store

        Returns:
            Memory ID
        """
        logger.info(f"Storing hypothesis: {hypothesis.title}")

        content = self._create_hypothesis_content(hypothesis)

        metadata = {
            "type": "hypothesis",
            "hypothesis_id": hypothesis.hypothesis_id,
            "domain": hypothesis.domain,
            "tested": hypothesis.tested,
            "validated": hypothesis.validated,
            "timestamp": hypothesis.timestamp.isoformat()
        }

        memory_id = await self.store_memory(
            content=content,
            memory_type=MemoryType.FACTUAL,
            metadata=metadata,
            importance=0.9 if hypothesis.validated else 0.5
        )

        logger.success(f"Hypothesis stored: {memory_id}")
        return memory_id

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Dict[str, Any],
        importance: float = 0.5
    ) -> str:
        """
        Store generic memory entry.

        Args:
            content: Memory content (text)
            memory_type: Type of memory
            metadata: Additional metadata
            importance: Importance score (0-1)

        Returns:
            Memory ID
        """
        # Generate unique ID
        memory_id = self._generate_id(content)

        # Generate embedding
        embedding = await self._get_embedding(content)

        # Create memory entry
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            embedding=embedding,
            importance_score=importance,
            timestamp=datetime.now()
        )

        # Store in vector DB
        if CHROMADB_AVAILABLE and hasattr(self, 'collection'):
            self.collection.add(
                ids=[memory_id],
                documents=[content],
                embeddings=[embedding] if embedding else None,
                metadatas=[{
                    "memory_type": memory_type.value,
                    "importance": importance,
                    "timestamp": memory.timestamp.isoformat(),
                    **metadata
                }]
            )
        else:
            # Fallback storage
            self.memory_store[memory_id] = memory

        self.stats["total_memories"] += 1
        return memory_id

    async def retrieve_relevant(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        domain: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[MemoryEntry]:
        """
        Retrieve relevant memories via semantic search.

        Args:
            query: Search query
            memory_type: Filter by memory type
            domain: Filter by domain
            top_k: Number of results
            min_similarity: Minimum similarity threshold

        Returns:
            List of relevant memory entries
        """
        import time
        start_time = time.time()

        logger.info(f"Retrieving memories for: {query[:50]}...")

        # Generate query embedding
        query_embedding = await self._get_embedding(query)

        # Build filters
        where_filter = {}
        if memory_type:
            where_filter["memory_type"] = memory_type.value
        if domain:
            where_filter["domain"] = domain

        # Search vector DB
        if CHROMADB_AVAILABLE and hasattr(self, 'collection'):
            results = self.collection.query(
                query_embeddings=[query_embedding] if query_embedding else None,
                query_texts=[query] if not query_embedding else None,
                n_results=top_k,
                where=where_filter if where_filter else None
            )

            memories = self._parse_chromadb_results(results)
        else:
            # Fallback: simple text matching
            memories = self._fallback_search(query, memory_type, top_k)

        # Update access statistics
        for memory in memories:
            memory.access_count += 1
            memory.last_accessed = datetime.now()

        # Calculate retrieval time
        retrieval_time = time.time() - start_time
        self.stats["retrievals"] += 1
        self.stats["avg_retrieval_time"] = (
            (self.stats["avg_retrieval_time"] * (self.stats["retrievals"] - 1) + retrieval_time)
            / self.stats["retrievals"]
        )

        logger.success(f"Retrieved {len(memories)} memories in {retrieval_time*1000:.2f}ms")
        return memories

    async def retrieve_similar_experiments(
        self,
        hypothesis_description: str,
        domain: Optional[str] = None,
        top_k: int = 3
    ) -> List[ExperimentMemory]:
        """
        Find similar past experiments for reference.

        Args:
            hypothesis_description: Description of new hypothesis
            domain: Optional domain filter
            top_k: Number of results

        Returns:
            List of similar experiment memories
        """
        memories = await self.retrieve_relevant(
            query=hypothesis_description,
            domain=domain,
            top_k=top_k
        )

        experiments = []
        for memory in memories:
            if memory.metadata.get("type") == "experiment":
                experiments.append(self._parse_experiment_from_memory(memory))

        return experiments

    async def get_domain_insights(
        self,
        domain: str,
        insight_type: str = "success"
    ) -> List[str]:
        """
        Extract insights from past experiments in a domain.

        Args:
            domain: Research domain
            insight_type: "success" or "failure"

        Returns:
            List of insights
        """
        logger.info(f"Extracting {insight_type} insights for {domain}")

        where_filter = {
            "domain": domain,
            "type": "experiment"
        }

        if insight_type == "success":
            where_filter["success"] = True

        if CHROMADB_AVAILABLE and hasattr(self, 'collection'):
            results = self.collection.get(
                where=where_filter,
                limit=20
            )

            insights = []
            for metadata in results.get("metadatas", []):
                if "insights" in metadata:
                    insights.extend(metadata["insights"])

            return insights
        else:
            return []

    async def decay_memories(self, decay_rate: float = 0.05):
        """
        Apply time-based decay to memories.

        Less important and older memories get lower scores.
        This prevents memory bloat.

        Args:
            decay_rate: Rate of decay per day
        """
        logger.info("Applying memory decay...")

        if hasattr(self, 'memory_store'):
            now = datetime.now()
            for memory in self.memory_store.values():
                days_old = (now - memory.timestamp).days
                memory.decay_factor = max(0.1, memory.decay_factor - (decay_rate * days_old))

        logger.success("Memory decay applied")

    async def prune_memories(
        self,
        min_importance: float = 0.3,
        min_decay: float = 0.2
    ):
        """
        Remove low-importance, decayed memories.

        Args:
            min_importance: Minimum importance to keep
            min_decay: Minimum decay factor to keep
        """
        logger.info("Pruning low-value memories...")

        if hasattr(self, 'memory_store'):
            before_count = len(self.memory_store)

            to_remove = [
                mem_id for mem_id, mem in self.memory_store.items()
                if mem.importance_score < min_importance or mem.decay_factor < min_decay
            ]

            for mem_id in to_remove:
                del self.memory_store[mem_id]

            after_count = len(self.memory_store)
            logger.success(f"Pruned {before_count - after_count} memories")

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self.embedding_client:
            return None

        try:
            response = await self.embedding_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None

    def _generate_id(self, content: str) -> str:
        """Generate unique ID from content hash"""
        timestamp = datetime.now().isoformat()
        data = f"{content}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _create_experiment_content(self, exp: ExperimentMemory) -> str:
        """Create searchable content from experiment"""
        return f"""
Experiment: {exp.experiment_id}
Domain: {exp.domain}
Methodology: {exp.methodology}
Conclusion: {exp.conclusion}
Success: {exp.success}
Insights: {', '.join(exp.insights or [])}
"""

    def _create_hypothesis_content(self, hyp: HypothesisMemory) -> str:
        """Create searchable content from hypothesis"""
        return f"""
Hypothesis: {hyp.title}
Description: {hyp.description}
Domain: {hyp.domain}
Tested: {hyp.tested}
Validated: {hyp.validated}
Insights: {', '.join(hyp.insights_gained)}
"""

    def _parse_chromadb_results(self, results: Dict) -> List[MemoryEntry]:
        """Parse ChromaDB query results"""
        memories = []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}

            memory = MemoryEntry(
                id=doc_id,
                content=documents[i] if i < len(documents) else "",
                memory_type=MemoryType(metadata.get("memory_type", "semantic")),
                metadata=metadata,
                importance_score=metadata.get("importance", 0.5)
            )
            memories.append(memory)

        return memories

    def _parse_experiment_from_memory(self, memory: MemoryEntry) -> ExperimentMemory:
        """Parse experiment from memory entry"""
        metadata = memory.metadata

        return ExperimentMemory(
            experiment_id=metadata.get("experiment_id", "unknown"),
            hypothesis_id=metadata.get("hypothesis_id", "unknown"),
            domain=metadata.get("domain", "unknown"),
            methodology=metadata.get("methodology", ""),
            results=metadata.get("results", {}),
            conclusion=metadata.get("conclusion", ""),
            success=metadata.get("success", False),
            timestamp=datetime.fromisoformat(metadata.get("timestamp", datetime.now().isoformat()))
        )

    def _fallback_search(
        self,
        query: str,
        memory_type: Optional[MemoryType],
        top_k: int
    ) -> List[MemoryEntry]:
        """Simple text-based search fallback"""
        query_lower = query.lower()
        matches = []

        for memory in self.memory_store.values():
            if memory_type and memory.memory_type != memory_type:
                continue

            if query_lower in memory.content.lower():
                matches.append(memory)

        # Sort by importance
        matches.sort(key=lambda m: m.importance_score, reverse=True)
        return matches[:top_k]

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            **self.stats,
            "avg_retrieval_ms": self.stats["avg_retrieval_time"] * 1000
        }
