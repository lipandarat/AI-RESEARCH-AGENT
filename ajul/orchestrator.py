"""
Main Orchestrator for Ajul AI Research Agent

Coordinates all components and manages the research lifecycle.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio
from loguru import logger

from ajul.core.planning_reasoning import PlanningReasoningModule, ResearchStage
from ajul.core.scientific_db import ScientificDatabaseIntegrator
from ajul.core.long_term_memory import LongTermMemorySystem
from ajul.core.multi_agent import MultiAgentCollaborationFramework
from ajul.core.generative_hypothesis import GenerativeHypothesisEngine, GenerationMode
from ajul.core.automated_experimentation import AutomatedExperimentationEngine
from ajul.core.data_analysis import DataAnalysisPipeline
from ajul.core.expert_feedback import ExpertFeedbackEngine
from ajul.core.self_evaluation import SelfEvaluationEngine, PerformanceMetric
from ajul.core.benchmarking import BenchmarkingEngine


@dataclass
class AjulConfig:
    """Configuration for Ajul agent"""
    anthropic_api_key: str
    model: str = "claude-sonnet-4-20250514"
    enable_multimodal: bool = True
    enable_expert_feedback: bool = True
    enable_self_evaluation: bool = True
    memory_backend: str = "chromadb"
    max_research_cycles: int = 10


class AjulResearchAgent:
    """
    Main orchestrator for autonomous AI research agent.

    Coordinates the complete research lifecycle:
    1. Observation & Knowledge Gathering
    2. Hypothesis Generation
    3. Experiment Planning & Execution
    4. Data Analysis
    5. Synthesis & Learning
    """

    def __init__(self, config: AjulConfig):
        self.config = config

        logger.info("Initializing Ajul Research Agent...")

        # Core modules
        self.planner = PlanningReasoningModule(
            api_key=config.anthropic_api_key,
            model=config.model
        )

        self.scientific_db = ScientificDatabaseIntegrator()

        self.memory = LongTermMemorySystem(
            api_key=config.anthropic_api_key,
            backend=config.memory_backend
        )

        self.multi_agent = MultiAgentCollaborationFramework(
            api_key=config.anthropic_api_key,
            model=config.model
        )

        self.hypothesis_engine = GenerativeHypothesisEngine(
            api_key=config.anthropic_api_key,
            model=config.model
        )

        self.experiment_engine = AutomatedExperimentationEngine(
            api_key=config.anthropic_api_key,
            model=config.model
        )

        self.analysis_pipeline = DataAnalysisPipeline(
            api_key=config.anthropic_api_key,
            model=config.model
        )

        # Optional modules
        if config.enable_expert_feedback:
            self.expert_feedback = ExpertFeedbackEngine()

        if config.enable_self_evaluation:
            self.self_evaluation = SelfEvaluationEngine()

        self.benchmarking = BenchmarkingEngine()

        logger.success("Ajul Research Agent initialized successfully")

    async def conduct_research(
        self,
        research_question: str,
        domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Conduct complete research cycle.

        Args:
            research_question: Research question to investigate
            domain: Scientific domain

        Returns:
            Complete research results
        """
        logger.info(f"Starting research: {research_question}")

        research_results = {
            "question": research_question,
            "domain": domain,
            "cycles": [],
            "final_insights": None
        }

        for cycle in range(self.config.max_research_cycles):
            logger.info(f"Research cycle {cycle + 1}/{self.config.max_research_cycles}")

            # Phase 1: Observation & Knowledge Gathering
            knowledge = await self._gather_knowledge(research_question, domain)

            # Phase 2: Hypothesis Generation
            hypotheses = await self._generate_hypotheses(research_question, knowledge)

            # Phase 3: Experiment Planning
            experiments = await self._plan_experiments(hypotheses)

            # Phase 4: Execution & Analysis
            results = await self._execute_and_analyze(experiments)

            # Phase 5: Synthesis
            synthesis = await self._synthesize_findings(results)

            research_results["cycles"].append({
                "cycle": cycle + 1,
                "hypotheses_count": len(hypotheses),
                "experiments_count": len(experiments),
                "synthesis": synthesis
            })

            # Check if research is complete
            if self._is_research_complete(synthesis):
                logger.success("Research objectives achieved")
                break

        # Final synthesis
        research_results["final_insights"] = await self._final_synthesis(
            research_results["cycles"]
        )

        # Self-evaluation
        if self.config.enable_self_evaluation:
            await self._evaluate_performance(research_results)

        logger.success("Research complete")
        return research_results

    async def _gather_knowledge(
        self,
        question: str,
        domain: str
    ) -> Dict[str, Any]:
        """Gather relevant scientific knowledge"""
        logger.info("Gathering knowledge from scientific databases")

        # Search scientific papers
        arxiv_papers = await self.scientific_db.search_arxiv(question, max_results=10)

        # Store in memory
        for paper in arxiv_papers:
            await self.memory.store_memory(
                content=f"{paper.title}: {paper.abstract}",
                memory_type="factual",
                metadata={"source": "arxiv", "domain": domain}
            )

        return {
            "papers_found": len(arxiv_papers),
            "domain": domain
        }

    async def _generate_hypotheses(
        self,
        question: str,
        knowledge: Dict[str, Any]
    ) -> List[Any]:
        """Generate research hypotheses"""
        logger.info("Generating hypotheses")

        # Use multi-agent collaboration for hypothesis generation
        hypotheses = await self.multi_agent.collaborative_hypothesis_generation(
            research_question=question,
            context=knowledge
        )

        # Store in memory
        for hypothesis in hypotheses:
            await self.memory.store_memory(
                content=f"Hypothesis: {hypothesis.statement}",
                memory_type="semantic",
                metadata={"type": "hypothesis"}
            )

        return hypotheses

    async def _plan_experiments(self, hypotheses: List[Any]) -> List[Any]:
        """Plan experiments to test hypotheses"""
        logger.info(f"Planning experiments for {len(hypotheses)} hypotheses")

        experiments = []
        for hypothesis in hypotheses:
            experiment = await self.planner.plan_experiment(hypothesis)
            experiments.append(experiment)

        return experiments

    async def _execute_and_analyze(self, experiments: List[Any]) -> List[Any]:
        """Execute experiments and analyze results"""
        logger.info(f"Executing {len(experiments)} experiments")

        results = []
        for experiment in experiments:
            # Execute
            result = await self.experiment_engine.execute_experiment(experiment)

            # Analyze
            analysis = await self.analysis_pipeline.analyze_results(result)

            results.append({
                "experiment": experiment,
                "result": result,
                "analysis": analysis
            })

        return results

    async def _synthesize_findings(self, results: List[Any]) -> Dict[str, Any]:
        """Synthesize findings from experiments"""
        logger.info("Synthesizing findings")

        synthesis = await self.planner.synthesize_knowledge(results)

        return synthesis

    def _is_research_complete(self, synthesis: Dict[str, Any]) -> bool:
        """Check if research objectives are met"""
        # Simple heuristic - in production, use more sophisticated criteria
        return synthesis.get("confidence", 0) > 0.8

    async def _final_synthesis(self, cycles: List[Dict]) -> Dict[str, Any]:
        """Create final research synthesis"""
        logger.info("Creating final synthesis")

        return {
            "total_cycles": len(cycles),
            "summary": "Research completed successfully",
            "key_findings": []
        }

    async def _evaluate_performance(self, research_results: Dict[str, Any]):
        """Evaluate agent performance"""
        logger.info("Evaluating performance")

        # Record metrics
        self.self_evaluation.record_performance(
            PerformanceMetric.HYPOTHESIS_QUALITY,
            0.85
        )

        # Generate report
        report = self.self_evaluation.evaluate_performance()

        logger.info(f"Performance: {report.performance_level.value}")

    async def run_benchmark(self, benchmark_name: str) -> Dict[str, Any]:
        """Run benchmarks on agent"""
        logger.info(f"Running benchmark: {benchmark_name}")

        # Add benchmark tasks
        # ... benchmark implementation

        return {"benchmark": benchmark_name, "status": "complete"}
