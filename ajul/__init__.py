"""
Ajul - Autonomous AI Research Agent

A self-directed AI system for scientific hypothesis generation,
experiment planning, and automated discovery.
"""

__version__ = "0.1.0"
__author__ = "Claude Code"

# Core modules
from ajul.core.planning_reasoning import PlanningReasoningModule
from ajul.core.scientific_db import ScientificDatabaseIntegrator
from ajul.core.long_term_memory import LongTermMemorySystem
from ajul.core.multi_agent import MultiAgentCollaborationFramework
from ajul.core.evolution_optimizer import EvolutionaryOptimizer
from ajul.core.generative_hypothesis import GenerativeHypothesisEngine
from ajul.core.automated_experimentation import AutomatedExperimentationEngine
from ajul.core.data_analysis import DataAnalysisPipeline
from ajul.core.validation_reproducibility import ValidationReproducibilityEngine
from ajul.core.code_experimentation import CodeExperimentationEngine
from ajul.core.multimodal_integration import MultimodalIntegrationEngine
from ajul.core.expert_feedback import ExpertFeedbackEngine
from ajul.core.self_evaluation import SelfEvaluationEngine
from ajul.core.domain_integration import DomainIntegrationEngine
from ajul.core.benchmarking import BenchmarkingEngine

# Orchestrator
from ajul.orchestrator import AjulResearchAgent

__all__ = [
    "AjulResearchAgent",
    "PlanningReasoningModule",
    "ScientificDatabaseIntegrator",
    "LongTermMemorySystem",
    "MultiAgentCollaborationFramework",
    "EvolutionaryOptimizer",
    "GenerativeHypothesisEngine",
    "AutomatedExperimentationEngine",
    "DataAnalysisPipeline",
    "ValidationReproducibilityEngine",
    "CodeExperimentationEngine",
    "MultimodalIntegrationEngine",
    "ExpertFeedbackEngine",
    "SelfEvaluationEngine",
    "DomainIntegrationEngine",
    "BenchmarkingEngine",
]
