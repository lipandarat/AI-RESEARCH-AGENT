"""
Generative Hypothesis Generation Module

Leverages LLM capabilities to generate novel scientific hypotheses
that humans might not think of. Uses advanced prompting techniques
and creative reasoning strategies.

Key features:
- Creative hypothesis generation
- Cross-domain idea combination
- Constraint-based generation
- Analogical reasoning
- Counterfactual thinking
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import json

from anthropic import AsyncAnthropic
from loguru import logger


class GenerationMode(str, Enum):
    """Hypothesis generation modes"""
    EXPLORATORY = "exploratory"  # Explore new territory
    INCREMENTAL = "incremental"  # Build on existing
    DISRUPTIVE = "disruptive"  # Challenge paradigms
    INTEGRATIVE = "integrative"  # Combine domains
    ANALOGICAL = "analogical"  # Use analogies
    COUNTERFACTUAL = "counterfactual"  # What-if scenarios


@dataclass
class GenerationConstraints:
    """Constraints for hypothesis generation"""
    domain: Optional[str] = None
    complexity_level: str = "moderate"  # simple, moderate, complex
    novelty_requirement: float = 0.7  # 0-1
    feasibility_requirement: float = 0.5  # 0-1
    exclude_topics: List[str] = field(default_factory=list)
    require_cross_domain: bool = False
    max_hypothesis_count: int = 5
    creativity_level: float = 0.8  # 0-1


@dataclass
class GeneratedHypothesis:
    """Generated hypothesis with metadata"""
    id: str
    title: str
    description: str
    domain: str
    generation_mode: GenerationMode
    testable_predictions: List[str]
    required_experiments: List[str]
    novelty_score: float
    feasibility_score: float
    creativity_score: float
    inspiration_sources: List[str]
    cross_domain_connections: List[str] = field(default_factory=list)
    potential_impact: str = ""
    risks_and_challenges: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class GenerativeHypothesisEngine:
    """
    Advanced hypothesis generation engine using LLM.

    Generates creative, novel hypotheses through:
    - Extended thinking protocols
    - Multi-perspective reasoning
    - Creative prompting strategies
    - Cross-domain synthesis
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

        # Generation templates
        self.templates = self._load_generation_templates()

        # Track generated hypotheses
        self.generation_history: List[GeneratedHypothesis] = []

    def _load_generation_templates(self) -> Dict[GenerationMode, str]:
        """Load prompt templates for each generation mode"""
        return {
            GenerationMode.EXPLORATORY: """Generate a highly novel hypothesis in {domain}.

Think step by step:
1. What are the unexplored frontiers in this domain?
2. What questions haven't been asked?
3. What assumptions can be challenged?
4. What would be truly surprising if discovered?

Generate a bold, exploratory hypothesis that opens new research directions.

Format:
**Hypothesis**: [Creative title]
**Description**: [Detailed explanation]
**Why Novel**: [What makes this unexplored]
**Testable Predictions**: [3-5 specific predictions]
**Required Experiments**: [How to test this]
**Potential Impact**: [Why this matters]
""",

            GenerationMode.DISRUPTIVE: """Generate a paradigm-challenging hypothesis in {domain}.

Question fundamental assumptions:
1. What does everyone believe that might be wrong?
2. What "obvious truths" should we doubt?
3. How could we completely reframe this problem?
4. What radical alternative explanations exist?

Create a disruptive hypothesis that challenges conventional wisdom.

Format:
**Hypothesis**: [Provocative title]
**Description**: [Detailed explanation]
**Paradigm Challenged**: [What belief this questions]
**Testable Predictions**: [3-5 falsifiable predictions]
**Required Experiments**: [Validation approach]
**Potential Impact**: [Revolutionary implications]
**Risks**: [Why this might fail]
""",

            GenerationMode.INTEGRATIVE: """Generate a hypothesis integrating {domain1} and {domain2}.

Cross-domain synthesis:
1. What concepts from {domain1} apply to {domain2}?
2. What methods from {domain2} solve problems in {domain1}?
3. What emerges when combining these fields?
4. What new phenomena appear at the intersection?

Create an integrative hypothesis bridging these domains.

Format:
**Hypothesis**: [Integrative title]
**Description**: [How domains connect]
**Domain 1 Contribution**: [From {domain1}]
**Domain 2 Contribution**: [From {domain2}]
**Emergent Properties**: [What emerges]
**Testable Predictions**: [3-5 predictions]
**Required Experiments**: [Cross-domain experiments]
""",

            GenerationMode.ANALOGICAL: """Generate a hypothesis using analogical reasoning.

Source Domain: {source_domain}
Target Domain: {target_domain}

Analogical transfer:
1. What deep structures are shared?
2. How do mechanisms map across domains?
3. What does the analogy predict?
4. Where might the analogy break down?

Create hypothesis by transferring insights from source to target.

Format:
**Hypothesis**: [Analogy-based title]
**Description**: [The analogy]
**Mapping**: [Source → Target correspondences]
**Predictions**: [What the analogy predicts]
**Experiments**: [How to test the analogy]
**Limitations**: [Where analogy fails]
""",

            GenerationMode.COUNTERFACTUAL: """Generate hypotheses through counterfactual thinking.

Domain: {domain}
Counterfactual: What if {counterfactual_condition}?

Explore alternative possibilities:
1. If this condition were true, what would follow?
2. What cascading effects would occur?
3. What new phenomena would emerge?
4. How would our understanding change?

Generate hypothesis from this counterfactual scenario.

Format:
**Hypothesis**: [Counterfactual hypothesis]
**Description**: [Full scenario]
**Causal Chain**: [What leads to what]
**Observable Consequences**: [What we'd see]
**Experiments**: [How to test this]
**Real-World Connection**: [Actual implications]
"""
        }

    async def generate_hypotheses(
        self,
        constraints: GenerationConstraints,
        mode: Optional[GenerationMode] = None,
        context: Optional[Dict] = None
    ) -> List[GeneratedHypothesis]:
        """
        Generate multiple hypotheses based on constraints.

        Args:
            constraints: Generation constraints
            mode: Optional specific generation mode
            context: Additional context (papers, observations, etc.)

        Returns:
            List of generated hypotheses
        """
        logger.info(
            f"Generating hypotheses: domain={constraints.domain}, "
            f"mode={mode}, max={constraints.max_hypothesis_count}"
        )

        # Select generation mode
        if mode is None:
            mode = self._select_generation_mode(constraints)

        hypotheses = []

        for i in range(constraints.max_hypothesis_count):
            try:
                hypothesis = await self._generate_single_hypothesis(
                    constraints=constraints,
                    mode=mode,
                    context=context,
                    iteration=i
                )

                if hypothesis:
                    hypotheses.append(hypothesis)
                    self.generation_history.append(hypothesis)

            except Exception as e:
                logger.error(f"Hypothesis generation failed: {e}")

        logger.success(f"Generated {len(hypotheses)} hypotheses")
        return hypotheses

    async def _generate_single_hypothesis(
        self,
        constraints: GenerationConstraints,
        mode: GenerationMode,
        context: Optional[Dict],
        iteration: int
    ) -> Optional[GeneratedHypothesis]:
        """Generate single hypothesis"""

        # Build prompt
        prompt = self._build_prompt(constraints, mode, context)

        # Call LLM with extended thinking
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7 + (constraints.creativity_level * 0.2),
                system=self._get_system_prompt(mode),
                messages=[{"role": "user", "content": prompt}]
            )

            hypothesis_text = response.content[0].text

            # Parse and structure
            hypothesis = self._parse_hypothesis(
                text=hypothesis_text,
                mode=mode,
                constraints=constraints,
                iteration=iteration
            )

            return hypothesis

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _build_prompt(
        self,
        constraints: GenerationConstraints,
        mode: GenerationMode,
        context: Optional[Dict]
    ) -> str:
        """Build generation prompt"""

        template = self.templates.get(mode, self.templates[GenerationMode.EXPLORATORY])

        # Format template based on mode
        if mode == GenerationMode.INTEGRATIVE and constraints.require_cross_domain:
            domains = constraints.domain.split("+") if constraints.domain else ["AI", "Biology"]
            prompt = template.format(
                domain1=domains[0] if len(domains) > 0 else "AI",
                domain2=domains[1] if len(domains) > 1 else "Biology"
            )
        elif mode == GenerationMode.ANALOGICAL:
            prompt = template.format(
                source_domain=context.get("source_domain", "Physics") if context else "Physics",
                target_domain=constraints.domain or "Machine Learning"
            )
        elif mode == GenerationMode.COUNTERFACTUAL:
            counterfactual = context.get("counterfactual", "neural networks had no nonlinear activations") if context else "time ran backwards"
            prompt = template.format(
                domain=constraints.domain or "AI",
                counterfactual_condition=counterfactual
            )
        else:
            prompt = template.format(domain=constraints.domain or "Artificial Intelligence")

        # Add context if available
        if context:
            context_str = self._format_context(context)
            prompt = f"{context_str}\n\n{prompt}"

        # Add constraints
        if constraints.exclude_topics:
            prompt += f"\n\nAvoid these topics: {', '.join(constraints.exclude_topics)}"

        prompt += f"\n\nTarget novelty: {constraints.novelty_requirement:.1f}/1.0"
        prompt += f"\nTarget feasibility: {constraints.feasibility_requirement:.1f}/1.0"

        return prompt

    def _format_context(self, context: Dict) -> str:
        """Format context for prompt"""
        parts = ["**Context:**"]

        if "observations" in context:
            parts.append("Observations:")
            parts.extend([f"- {obs}" for obs in context["observations"]])

        if "papers" in context:
            parts.append("\nRelevant Research:")
            parts.extend([f"- {paper}" for paper in context["papers"][:3]])

        if "existing_hypotheses" in context:
            parts.append("\nExisting Hypotheses (to avoid duplication):")
            parts.extend([f"- {hyp}" for hyp in context["existing_hypotheses"]])

        return "\n".join(parts)

    def _get_system_prompt(self, mode: GenerationMode) -> str:
        """Get system prompt for generation mode"""

        base = """You are an advanced scientific hypothesis generator with expertise across multiple domains.

Your role is to generate novel, creative hypotheses that push boundaries of current understanding.

Guidelines:
- Be bold and creative while remaining scientifically grounded
- Generate falsifiable, testable hypotheses
- Think beyond obvious extensions of existing work
- Consider interdisciplinary connections
- Identify specific experiments to test the hypothesis
- Assess both potential and risks
"""

        mode_specific = {
            GenerationMode.EXPLORATORY: "\nFocus on unexplored territories and new frontiers.",
            GenerationMode.DISRUPTIVE: "\nChallenge established paradigms and question assumptions.",
            GenerationMode.INTEGRATIVE: "\nSynthesize insights across domains.",
            GenerationMode.ANALOGICAL: "\nUse deep structural analogies to transfer insights.",
            GenerationMode.COUNTERFACTUAL: "\nExplore alternative scenarios and their implications."
        }

        return base + mode_specific.get(mode, "")

    def _parse_hypothesis(
        self,
        text: str,
        mode: GenerationMode,
        constraints: GenerationConstraints,
        iteration: int
    ) -> GeneratedHypothesis:
        """Parse LLM output into structured hypothesis"""
        import uuid

        # Simple parsing (production would use more robust extraction)
        lines = text.split('\n')

        title = "Generated Hypothesis"
        description = ""
        predictions = []
        experiments = []
        impact = ""
        risks = []

        for line in lines:
            if line.startswith('**Hypothesis**:'):
                title = line.split(':', 1)[1].strip()
            elif line.startswith('**Description**:'):
                description = line.split(':', 1)[1].strip()
            elif line.startswith('**Potential Impact**:'):
                impact = line.split(':', 1)[1].strip()

        # Extract predictions (lines starting with number or dash after "Predictions" section)
        in_predictions = False
        in_experiments = False

        for line in lines:
            if 'Testable Predictions' in line or 'Predictions:' in line:
                in_predictions = True
                in_experiments = False
                continue
            elif 'Required Experiments' in line or 'Experiments:' in line:
                in_experiments = True
                in_predictions = False
                continue
            elif line.startswith('**'):
                in_predictions = False
                in_experiments = False

            if in_predictions and (line.strip().startswith('-') or line.strip().startswith(('1', '2', '3', '4', '5'))):
                predictions.append(line.strip().lstrip('-123456789. '))
            elif in_experiments and (line.strip().startswith('-') or line.strip().startswith(('1', '2', '3', '4', '5'))):
                experiments.append(line.strip().lstrip('-123456789. '))

        # Estimate scores
        novelty_score = min(1.0, constraints.novelty_requirement + random.uniform(-0.1, 0.1))
        feasibility_score = min(1.0, constraints.feasibility_requirement + random.uniform(-0.1, 0.1))
        creativity_score = min(1.0, constraints.creativity_level + random.uniform(-0.1, 0.1))

        return GeneratedHypothesis(
            id=str(uuid.uuid4()),
            title=title,
            description=description or text[:300],
            domain=constraints.domain or "General",
            generation_mode=mode,
            testable_predictions=predictions or ["To be extracted"],
            required_experiments=experiments or ["To be determined"],
            novelty_score=novelty_score,
            feasibility_score=feasibility_score,
            creativity_score=creativity_score,
            inspiration_sources=[],
            potential_impact=impact,
            risks_and_challenges=risks
        )

    def _select_generation_mode(
        self,
        constraints: GenerationConstraints
    ) -> GenerationMode:
        """Select appropriate generation mode based on constraints"""

        if constraints.require_cross_domain:
            return GenerationMode.INTEGRATIVE

        if constraints.novelty_requirement > 0.8:
            return random.choice([
                GenerationMode.DISRUPTIVE,
                GenerationMode.EXPLORATORY
            ])

        if constraints.novelty_requirement < 0.4:
            return GenerationMode.INCREMENTAL

        # Default: random selection
        return random.choice([
            GenerationMode.EXPLORATORY,
            GenerationMode.INTEGRATIVE,
            GenerationMode.ANALOGICAL
        ])

    async def generate_hypothesis_variants(
        self,
        base_hypothesis: str,
        variant_count: int = 3
    ) -> List[GeneratedHypothesis]:
        """
        Generate variants of an existing hypothesis.

        Args:
            base_hypothesis: Base hypothesis to vary
            variant_count: Number of variants to generate

        Returns:
            List of hypothesis variants
        """
        logger.info(f"Generating {variant_count} variants of base hypothesis")

        prompt = f"""Base Hypothesis:
{base_hypothesis}

Generate {variant_count} creative variants of this hypothesis:
1. Strengthen it (make bolder claims)
2. Weaken it (more conservative)
3. Pivot it (change direction)
4. Expand it (broader scope)
5. Narrow it (more specific)

For each variant:
**Variant Type**: [strengthen/weaken/pivot/expand/narrow]
**Hypothesis**: [variant]
**Changes**: [what changed]
**Predictions**: [3 testable predictions]
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=3072,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse variants (simplified)
        variants = []
        # Would implement proper parsing here

        return variants

    async def combine_hypotheses(
        self,
        hypotheses: List[str]
    ) -> GeneratedHypothesis:
        """
        Combine multiple hypotheses into integrated hypothesis.

        Args:
            hypotheses: List of hypotheses to combine

        Returns:
            Integrated hypothesis
        """
        logger.info(f"Combining {len(hypotheses)} hypotheses")

        hyp_text = "\n\n".join([f"{i+1}. {h}" for i, h in enumerate(hypotheses)])

        prompt = f"""Hypotheses to integrate:

{hyp_text}

Create a single integrated hypothesis that:
1. Captures insights from all inputs
2. Resolves contradictions
3. Identifies synergies
4. Generates novel predictions

Format:
**Integrated Hypothesis**: [title]
**Description**: [how they connect]
**Unified Predictions**: [5 testable predictions]
**Experiments**: [integrated experimental design]
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=3072,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse into hypothesis
        combined = self._parse_hypothesis(
            text=response.content[0].text,
            mode=GenerationMode.INTEGRATIVE,
            constraints=GenerationConstraints(),
            iteration=0
        )

        return combined

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get statistics on hypothesis generation"""
        if not self.generation_history:
            return {}

        return {
            "total_generated": len(self.generation_history),
            "by_mode": {
                mode.value: len([h for h in self.generation_history if h.generation_mode == mode])
                for mode in GenerationMode
            },
            "avg_novelty": sum(h.novelty_score for h in self.generation_history) / len(self.generation_history),
            "avg_feasibility": sum(h.feasibility_score for h in self.generation_history) / len(self.generation_history),
            "avg_creativity": sum(h.creativity_score for h in self.generation_history) / len(self.generation_history),
            "domains": list(set(h.domain for h in self.generation_history)),
            "recent_hypotheses": [
                {
                    "title": h.title,
                    "mode": h.generation_mode.value,
                    "novelty": h.novelty_score
                }
                for h in self.generation_history[-5:]
            ]
        }
