"""
Planning and Reasoning Module

Implements the 4-stage research process:
1. Observation - Domain exploration
2. Planning - Hypothesis generation & experiment design
3. Analysis - Data evaluation
4. Synthesis - Knowledge integration
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from anthropic import AsyncAnthropic
from loguru import logger


class ResearchStage(str, Enum):
    """Research process stages"""
    OBSERVATION = "observation"
    PLANNING = "planning"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"


@dataclass
class Hypothesis:
    """Scientific hypothesis structure"""
    id: str
    title: str
    description: str
    domain: str
    assumptions: List[str]
    testable_predictions: List[str]
    variables: Dict[str, str]  # independent/dependent variables
    novelty_score: float  # 0-1
    feasibility_score: float  # 0-1
    generated_at: datetime
    stage: ResearchStage = ResearchStage.OBSERVATION


@dataclass
class ExperimentPlan:
    """Experimental design plan"""
    id: str
    hypothesis_id: str
    objective: str
    methodology: str
    variables_to_measure: List[str]
    control_conditions: List[str]
    experimental_conditions: List[str]
    data_collection_methods: List[str]
    expected_outcomes: List[str]
    validation_criteria: Dict[str, any]
    estimated_duration: str
    resources_needed: List[str]


class PlanningReasoningModule:
    """
    Core module for scientific reasoning and experiment planning.

    Implements chain-of-thought reasoning for:
    - Hypothesis generation
    - Experimental design
    - Logical inference
    - Knowledge synthesis
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.reasoning_history: List[Dict] = []

    async def generate_hypothesis(
        self,
        domain: str,
        observations: List[str],
        existing_knowledge: Optional[str] = None
    ) -> Hypothesis:
        """
        Generate novel scientific hypothesis from observations.

        Uses chain-of-thought reasoning to:
        1. Analyze observations
        2. Identify patterns and gaps
        3. Formulate testable hypothesis
        4. Assess novelty and feasibility

        Args:
            domain: Research domain (e.g., "machine_learning", "physics")
            observations: List of observed phenomena or data
            existing_knowledge: Optional context from knowledge base

        Returns:
            Structured Hypothesis object
        """
        logger.info(f"Generating hypothesis for domain: {domain}")

        prompt = self._build_hypothesis_prompt(
            domain, observations, existing_knowledge
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                system=self._get_hypothesis_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            hypothesis_text = response.content[0].text
            hypothesis = self._parse_hypothesis(hypothesis_text, domain)

            # Log reasoning chain
            self.reasoning_history.append({
                "stage": ResearchStage.OBSERVATION,
                "action": "hypothesis_generation",
                "domain": domain,
                "output": hypothesis,
                "timestamp": datetime.now()
            })

            logger.success(f"Generated hypothesis: {hypothesis.title}")
            return hypothesis

        except Exception as e:
            logger.error(f"Hypothesis generation failed: {e}")
            raise

    async def plan_experiment(
        self,
        hypothesis: Hypothesis,
        constraints: Optional[Dict] = None
    ) -> ExperimentPlan:
        """
        Design experimental plan to test hypothesis.

        Creates detailed experimental methodology including:
        - Variable selection and control
        - Data collection procedures
        - Validation criteria
        - Resource requirements

        Args:
            hypothesis: Hypothesis to test
            constraints: Optional resource/time constraints

        Returns:
            Structured ExperimentPlan object
        """
        logger.info(f"Planning experiment for hypothesis: {hypothesis.title}")

        prompt = self._build_experiment_prompt(hypothesis, constraints)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.5,  # Lower temp for methodical planning
                system=self._get_experiment_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            plan_text = response.content[0].text
            plan = self._parse_experiment_plan(plan_text, hypothesis.id)

            # Log reasoning chain
            self.reasoning_history.append({
                "stage": ResearchStage.PLANNING,
                "action": "experiment_planning",
                "hypothesis_id": hypothesis.id,
                "output": plan,
                "timestamp": datetime.now()
            })

            logger.success(f"Experiment plan created: {plan.objective}")
            return plan

        except Exception as e:
            logger.error(f"Experiment planning failed: {e}")
            raise

    async def reason_about_results(
        self,
        experiment_results: Dict,
        hypothesis: Hypothesis
    ) -> Dict[str, any]:
        """
        Analyze experimental results and draw conclusions.

        Uses logical reasoning to:
        1. Compare results with predictions
        2. Assess hypothesis validity
        3. Identify unexpected findings
        4. Suggest next steps

        Args:
            experiment_results: Raw experimental data
            hypothesis: Original hypothesis

        Returns:
            Analysis with conclusions and recommendations
        """
        logger.info("Reasoning about experimental results...")

        prompt = self._build_analysis_prompt(experiment_results, hypothesis)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=3072,
                temperature=0.4,
                system=self._get_analysis_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text
            analysis = self._parse_analysis(analysis_text)

            # Log reasoning chain
            self.reasoning_history.append({
                "stage": ResearchStage.ANALYSIS,
                "action": "result_analysis",
                "hypothesis_id": hypothesis.id,
                "output": analysis,
                "timestamp": datetime.now()
            })

            logger.success("Analysis complete")
            return analysis

        except Exception as e:
            logger.error(f"Result analysis failed: {e}")
            raise

    async def synthesize_knowledge(
        self,
        hypotheses: List[Hypothesis],
        experiment_results: List[Dict],
        domain: str
    ) -> Dict[str, any]:
        """
        Synthesize findings into coherent knowledge.

        Integrates multiple experiments to:
        1. Identify overarching patterns
        2. Build theoretical frameworks
        3. Generate meta-insights
        4. Suggest research directions

        Args:
            hypotheses: List of tested hypotheses
            experiment_results: All experimental outcomes
            domain: Research domain

        Returns:
            Synthesized knowledge and insights
        """
        logger.info(f"Synthesizing knowledge for {len(hypotheses)} hypotheses")

        prompt = self._build_synthesis_prompt(
            hypotheses, experiment_results, domain
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.6,
                system=self._get_synthesis_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            synthesis_text = response.content[0].text
            synthesis = self._parse_synthesis(synthesis_text)

            # Log reasoning chain
            self.reasoning_history.append({
                "stage": ResearchStage.SYNTHESIS,
                "action": "knowledge_synthesis",
                "domain": domain,
                "output": synthesis,
                "timestamp": datetime.now()
            })

            logger.success("Knowledge synthesis complete")
            return synthesis

        except Exception as e:
            logger.error(f"Knowledge synthesis failed: {e}")
            raise

    # System prompts for each stage
    def _get_hypothesis_system_prompt(self) -> str:
        return """You are a scientific reasoning engine specialized in hypothesis generation.

Generate novel, testable hypotheses by:
1. Analyzing observations carefully
2. Identifying patterns and anomalies
3. Connecting to existing knowledge
4. Formulating clear predictions
5. Ensuring testability

Be creative but rigorous. Focus on falsifiable hypotheses."""

    def _get_experiment_system_prompt(self) -> str:
        return """You are an experimental design specialist.

Create rigorous experimental plans that:
1. Clearly define variables (independent, dependent, control)
2. Specify measurement procedures
3. Establish validation criteria
4. Consider confounding factors
5. Ensure reproducibility

Be methodical and comprehensive."""

    def _get_analysis_system_prompt(self) -> str:
        return """You are a scientific data analyst.

Analyze results objectively by:
1. Comparing predictions vs outcomes
2. Assessing statistical significance
3. Identifying unexpected findings
4. Drawing logical conclusions
5. Suggesting improvements

Be critical and evidence-based."""

    def _get_synthesis_system_prompt(self) -> str:
        return """You are a knowledge synthesizer.

Integrate findings to:
1. Identify meta-patterns across experiments
2. Build coherent theoretical frameworks
3. Generate higher-level insights
4. Propose future research directions

Be integrative and visionary."""

    # Prompt builders (simplified implementations)
    def _build_hypothesis_prompt(
        self,
        domain: str,
        observations: List[str],
        knowledge: Optional[str]
    ) -> str:
        obs_text = "\n".join(f"- {o}" for o in observations)
        knowledge_section = f"\n\nExisting Knowledge:\n{knowledge}" if knowledge else ""

        return f"""Domain: {domain}

Observations:
{obs_text}{knowledge_section}

Generate a novel scientific hypothesis that:
1. Explains these observations
2. Makes testable predictions
3. Is falsifiable
4. Advances understanding

Format:
**Title**: [hypothesis name]
**Description**: [detailed explanation]
**Assumptions**: [underlying assumptions]
**Predictions**: [testable predictions]
**Variables**: [key variables to measure]
**Novelty**: [0-1 score]
**Feasibility**: [0-1 score]"""

    def _build_experiment_prompt(
        self,
        hypothesis: Hypothesis,
        constraints: Optional[Dict]
    ) -> str:
        constraint_text = ""
        if constraints:
            constraint_text = "\n\nConstraints:\n" + "\n".join(
                f"- {k}: {v}" for k, v in constraints.items()
            )

        return f"""Hypothesis: {hypothesis.title}

{hypothesis.description}

Predictions:
{chr(10).join(f"- {p}" for p in hypothesis.testable_predictions)}{constraint_text}

Design a rigorous experimental plan with:
1. Clear objective
2. Methodology (step-by-step)
3. Variables to measure
4. Control conditions
5. Experimental conditions
6. Data collection methods
7. Expected outcomes
8. Validation criteria
9. Resource requirements"""

    def _build_analysis_prompt(
        self,
        results: Dict,
        hypothesis: Hypothesis
    ) -> str:
        return f"""Hypothesis: {hypothesis.title}

Predicted Outcomes:
{chr(10).join(f"- {p}" for p in hypothesis.testable_predictions)}

Experimental Results:
{chr(10).join(f"- {k}: {v}" for k, v in results.items())}

Analyze:
1. Do results support the hypothesis?
2. What was unexpected?
3. What are the implications?
4. What should be done next?

Be objective and evidence-based."""

    def _build_synthesis_prompt(
        self,
        hypotheses: List[Hypothesis],
        results: List[Dict],
        domain: str
    ) -> str:
        hyp_summary = "\n".join(
            f"{i+1}. {h.title}: {h.description[:100]}..."
            for i, h in enumerate(hypotheses)
        )

        return f"""Domain: {domain}

Tested Hypotheses:
{hyp_summary}

Total Experiments: {len(results)}

Synthesize findings into:
1. Meta-patterns across experiments
2. Coherent theoretical framework
3. Key insights and discoveries
4. Future research directions

Create integrative knowledge."""

    # Parsing methods (simplified - would be more robust in production)
    def _parse_hypothesis(self, text: str, domain: str) -> Hypothesis:
        """Parse LLM response into Hypothesis object"""
        import uuid

        # Simple parsing - extract key sections
        lines = text.strip().split('\n')
        title = "Generated Hypothesis"
        description = ""
        assumptions = []
        predictions = []
        variables = {}

        for line in lines:
            if line.startswith('**Title**:'):
                title = line.split(':', 1)[1].strip()
            elif line.startswith('**Description**:'):
                description = line.split(':', 1)[1].strip()

        return Hypothesis(
            id=str(uuid.uuid4()),
            title=title,
            description=description or text[:200],
            domain=domain,
            assumptions=assumptions,
            testable_predictions=predictions or ["Prediction to be extracted"],
            variables=variables or {"independent": "X", "dependent": "Y"},
            novelty_score=0.7,
            feasibility_score=0.8,
            generated_at=datetime.now(),
            stage=ResearchStage.OBSERVATION
        )

    def _parse_experiment_plan(
        self,
        text: str,
        hypothesis_id: str
    ) -> ExperimentPlan:
        """Parse LLM response into ExperimentPlan"""
        import uuid

        return ExperimentPlan(
            id=str(uuid.uuid4()),
            hypothesis_id=hypothesis_id,
            objective="Test hypothesis validity",
            methodology=text[:500],
            variables_to_measure=["outcome_variable"],
            control_conditions=["baseline"],
            experimental_conditions=["treatment"],
            data_collection_methods=["measurement"],
            expected_outcomes=["positive_result"],
            validation_criteria={"significance": 0.05},
            estimated_duration="1 week",
            resources_needed=["compute", "data"]
        )

    def _parse_analysis(self, text: str) -> Dict[str, any]:
        """Parse analysis results"""
        return {
            "conclusion": text[:200],
            "hypothesis_supported": True,
            "confidence": 0.8,
            "unexpected_findings": [],
            "next_steps": ["Replicate experiment"],
            "full_analysis": text
        }

    def _parse_synthesis(self, text: str) -> Dict[str, any]:
        """Parse synthesis results"""
        return {
            "meta_patterns": ["Pattern 1", "Pattern 2"],
            "theoretical_framework": text[:500],
            "key_insights": ["Insight 1"],
            "future_directions": ["Direction 1"],
            "full_synthesis": text
        }

    def get_reasoning_chain(self) -> List[Dict]:
        """Return complete reasoning history"""
        return self.reasoning_history
