"""Configuration management for Ajul"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Main configuration"""

    # API Keys
    anthropic_api_key: str

    # Model Settings
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.3
    max_tokens: int = 4096

    # Memory Settings
    memory_backend: str = "chromadb"
    memory_collection: str = "ajul_memory"

    # Agent Settings
    max_research_cycles: int = 10
    enable_multimodal: bool = True
    enable_expert_feedback: bool = True
    enable_self_evaluation: bool = True

    # Performance
    async_workers: int = 4

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        return cls(
            anthropic_api_key=api_key,
            model=os.getenv("AJUL_MODEL", "claude-sonnet-4-20250514"),
            temperature=float(os.getenv("AJUL_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("AJUL_MAX_TOKENS", "4096")),
            memory_backend=os.getenv("AJUL_MEMORY_BACKEND", "chromadb"),
            max_research_cycles=int(os.getenv("AJUL_MAX_CYCLES", "10")),
            enable_multimodal=os.getenv("AJUL_MULTIMODAL", "true").lower() == "true",
            enable_expert_feedback=os.getenv("AJUL_EXPERT_FEEDBACK", "true").lower() == "true",
            enable_self_evaluation=os.getenv("AJUL_SELF_EVAL", "true").lower() == "true",
        )
