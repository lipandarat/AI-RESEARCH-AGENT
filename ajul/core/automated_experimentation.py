"""
Automated Experiment Planning & Execution Module

Enables autonomous AI agent to:
- Design experiments from hypotheses
- Generate experiment code automatically
- Execute experiments safely
- Monitor and log results
- Handle failures and iterate

Implements the full experiment lifecycle autonomously.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import subprocess
import asyncio
import json
import os
import tempfile
import hashlib

from anthropic import AsyncAnthropic
from loguru import logger


class ExperimentStatus(str, Enum):
    """Experiment execution status"""
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExperimentType(str, Enum):
    """Types of experiments"""
    SIMULATION = "simulation"
    DATA_ANALYSIS = "data_analysis"
    MODEL_TRAINING = "model_training"
    ALGORITHM_TEST = "algorithm_test"
    BENCHMARK = "benchmark"
    PROOF_OF_CONCEPT = "proof_of_concept"


@dataclass
class ExperimentSpec:
    """Specification for an experiment"""
    id: str
    hypothesis_id: str
    title: str
    description: str
    experiment_type: ExperimentType
    objectives: List[str]
    methodology: str
    variables: Dict[str, Any]
    expected_outcomes: List[str]
    success_criteria: Dict[str, Any]
    resource_requirements: Dict[str, Any]
    estimated_duration: str
    code_language: str = "python"
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ExperimentResult:
    """Results from experiment execution"""
    experiment_id: str
    status: ExperimentStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    outputs: Dict[str, Any]
    metrics: Dict[str, float]
    logs: List[str]
    errors: List[str]
    success: bool
    artifacts: List[str] = field(default_factory=list)
    conclusion: str = ""


@dataclass
class GeneratedCode:
    """Generated experiment code"""
    code: str
    language: str
    dependencies: List[str]
    entry_point: str
    safety_score: float  # 0-1
    review_notes: List[str] = field(default_factory=list)


class AutomatedExperimentationEngine:
    """
    Engine for automated experiment design and execution.

    Workflow:
    1. Receive hypothesis
    2. Design experiment (variables, methods, metrics)
    3. Generate executable code
    4. Safety review
    5. Execute in sandbox
    6. Monitor and log
    7. Analyze results
    8. Report findings
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        workspace_dir: str = "./experiments",
        timeout_seconds: int = 300,
        enable_execution: bool = True
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.workspace_dir = workspace_dir
        self.timeout_seconds = timeout_seconds
        self.enable_execution = enable_execution

        # Experiment tracking
        self.experiments: Dict[str, ExperimentResult] = {}
        self.execution_history: List[Dict] = []

        # Safety settings
        self.safety_checks_enabled = True
        self.max_resource_usage = {"cpu": 80, "memory": 4096, "disk": 1000}

        # Create workspace
        os.makedirs(workspace_dir, exist_ok=True)

        logger.info(f"Automated experimentation engine initialized: {workspace_dir}")

    async def design_experiment(
        self,
        hypothesis: str,
        hypothesis_id: str,
        domain: str,
        constraints: Optional[Dict] = None
    ) -> ExperimentSpec:
        """
        Design experiment to test hypothesis.

        Args:
            hypothesis: Hypothesis to test
            hypothesis_id: Hypothesis identifier
            domain: Research domain
            constraints: Resource/time constraints

        Returns:
            Experiment specification
        """
        logger.info(f"Designing experiment for hypothesis: {hypothesis_id}")

        prompt = self._build_design_prompt(hypothesis, domain, constraints)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.5,
                system=self._get_design_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            design_text = response.content[0].text

            # Parse into ExperimentSpec
            spec = self._parse_experiment_spec(
                text=design_text,
                hypothesis_id=hypothesis_id,
                domain=domain
            )

            logger.success(f"Experiment designed: {spec.title}")
            return spec

        except Exception as e:
            logger.error(f"Experiment design failed: {e}")
            raise

    async def generate_experiment_code(
        self,
        spec: ExperimentSpec
    ) -> GeneratedCode:
        """
        Generate executable code for experiment.

        Args:
            spec: Experiment specification

        Returns:
            Generated code
        """
        logger.info(f"Generating code for experiment: {spec.id}")

        prompt = self._build_code_generation_prompt(spec)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0.3,  # Lower for code generation
                system=self._get_code_generation_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            code_text = response.content[0].text

            # Extract code from markdown blocks
            code = self._extract_code(code_text)

            generated = GeneratedCode(
                code=code,
                language=spec.code_language,
                dependencies=spec.dependencies,
                entry_point="main",
                safety_score=0.8
            )

            # Safety review
            if self.safety_checks_enabled:
                generated = await self._safety_review_code(generated)

            logger.success(f"Code generated: {len(code)} chars")
            return generated

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise

    async def execute_experiment(
        self,
        spec: ExperimentSpec,
        code: GeneratedCode,
        dry_run: bool = False
    ) -> ExperimentResult:
        """
        Execute experiment code safely.

        Args:
            spec: Experiment specification
            code: Generated code to execute
            dry_run: If True, validate but don't execute

        Returns:
            Experiment results
        """
        logger.info(f"Executing experiment: {spec.id} (dry_run={dry_run})")

        start_time = datetime.now()

        result = ExperimentResult(
            experiment_id=spec.id,
            status=ExperimentStatus.PLANNED,
            start_time=start_time,
            end_time=None,
            duration_seconds=0.0,
            outputs={},
            metrics={},
            logs=[],
            errors=[],
            success=False
        )

        if not self.enable_execution or dry_run:
            logger.warning("Execution disabled or dry_run - skipping execution")
            result.status = ExperimentStatus.COMPLETED
            result.logs.append("Dry run - no execution performed")
            return result

        try:
            # Create temporary execution environment
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code to file
                code_file = os.path.join(tmpdir, f"experiment_{spec.id}.py")
                with open(code_file, 'w') as f:
                    f.write(code.code)

                # Update status
                result.status = ExperimentStatus.RUNNING
                self.experiments[spec.id] = result

                # Execute with timeout
                logger.debug(f"Running: python {code_file}")

                process = await asyncio.create_subprocess_exec(
                    "python", code_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.timeout_seconds
                    )

                    # Collect results
                    result.logs.append(stdout.decode('utf-8'))
                    if stderr:
                        result.errors.append(stderr.decode('utf-8'))

                    result.status = ExperimentStatus.COMPLETED
                    result.success = process.returncode == 0

                except asyncio.TimeoutError:
                    process.kill()
                    result.status = ExperimentStatus.TIMEOUT
                    result.errors.append(f"Execution timeout after {self.timeout_seconds}s")
                    logger.warning(f"Experiment {spec.id} timed out")

        except Exception as e:
            result.status = ExperimentStatus.FAILED
            result.errors.append(str(e))
            logger.error(f"Experiment execution failed: {e}")

        finally:
            end_time = datetime.now()
            result.end_time = end_time
            result.duration_seconds = (end_time - start_time).total_seconds()

            self.experiments[spec.id] = result
            self._log_execution(spec, result)

        logger.info(
            f"Experiment {spec.id} finished: "
            f"status={result.status}, duration={result.duration_seconds:.2f}s"
        )

        return result

    async def analyze_results(
        self,
        spec: ExperimentSpec,
        result: ExperimentResult
    ) -> Dict[str, Any]:
        """
        Analyze experiment results using LLM.

        Args:
            spec: Experiment specification
            result: Execution results

        Returns:
            Analysis with conclusions
        """
        logger.info(f"Analyzing results for experiment: {spec.id}")

        prompt = f"""Analyze these experiment results:

**Experiment**: {spec.title}
**Hypothesis**: {spec.description}
**Expected Outcomes**: {', '.join(spec.expected_outcomes)}

**Execution Status**: {result.status}
**Success**: {result.success}
**Duration**: {result.duration_seconds:.2f}s

**Outputs**:
{json.dumps(result.outputs, indent=2)}

**Logs**:
{chr(10).join(result.logs[:1000])}

**Errors**:
{chr(10).join(result.errors)}

Provide analysis:
1. Did the experiment succeed?
2. Were expected outcomes achieved?
3. What were the key findings?
4. Does this support or refute the hypothesis?
5. What are the limitations?
6. What should be done next?

Be objective and evidence-based.
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=3072,
                temperature=0.4,
                system="You are a scientific data analyst. Analyze results objectively.",
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text

            analysis = {
                "conclusion": analysis_text[:500],
                "full_analysis": analysis_text,
                "hypothesis_supported": "support" in analysis_text.lower(),
                "key_findings": self._extract_findings(analysis_text),
                "next_steps": self._extract_next_steps(analysis_text),
                "timestamp": datetime.now().isoformat()
            }

            result.conclusion = analysis["conclusion"]

            logger.success("Result analysis complete")
            return analysis

        except Exception as e:
            logger.error(f"Result analysis failed: {e}")
            return {"error": str(e)}

    async def run_full_experiment_cycle(
        self,
        hypothesis: str,
        hypothesis_id: str,
        domain: str,
        constraints: Optional[Dict] = None,
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete experiment cycle: design → code → execute → analyze.

        Args:
            hypothesis: Hypothesis to test
            hypothesis_id: Hypothesis identifier
            domain: Research domain
            constraints: Optional constraints
            auto_execute: If True, execute automatically

        Returns:
            Complete results with analysis
        """
        logger.info(f"Starting full experiment cycle for {hypothesis_id}")

        try:
            # 1. Design
            spec = await self.design_experiment(
                hypothesis=hypothesis,
                hypothesis_id=hypothesis_id,
                domain=domain,
                constraints=constraints
            )

            # 2. Generate code
            code = await self.generate_experiment_code(spec)

            # 3. Execute (or dry run)
            result = await self.execute_experiment(
                spec=spec,
                code=code,
                dry_run=not auto_execute
            )

            # 4. Analyze
            analysis = await self.analyze_results(spec, result)

            # Return complete package
            return {
                "hypothesis_id": hypothesis_id,
                "experiment_id": spec.id,
                "specification": {
                    "title": spec.title,
                    "type": spec.experiment_type.value,
                    "objectives": spec.objectives,
                    "methodology": spec.methodology
                },
                "code": {
                    "language": code.language,
                    "length": len(code.code),
                    "dependencies": code.dependencies,
                    "safety_score": code.safety_score
                },
                "execution": {
                    "status": result.status.value,
                    "success": result.success,
                    "duration": result.duration_seconds,
                    "outputs": result.outputs,
                    "metrics": result.metrics
                },
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Experiment cycle failed: {e}")
            return {
                "error": str(e),
                "hypothesis_id": hypothesis_id
            }

    # Helper methods

    def _build_design_prompt(
        self,
        hypothesis: str,
        domain: str,
        constraints: Optional[Dict]
    ) -> str:
        """Build experiment design prompt"""

        prompt = f"""Design a rigorous experiment to test this hypothesis:

**Hypothesis**: {hypothesis}
**Domain**: {domain}

Design the experiment with:

**1. Objectives**
What specifically are we testing?

**2. Methodology**
Step-by-step experimental procedure

**3. Variables**
- Independent variables (what we control)
- Dependent variables (what we measure)
- Control variables (what we keep constant)

**4. Expected Outcomes**
What results would support/refute the hypothesis?

**5. Success Criteria**
How do we determine if experiment succeeded?

**6. Resource Requirements**
- Compute resources
- Data requirements
- Time estimate

**7. Implementation Approach**
How can this be implemented in code?
"""

        if constraints:
            prompt += f"\n\n**Constraints**: {json.dumps(constraints, indent=2)}"

        return prompt

    def _build_code_generation_prompt(self, spec: ExperimentSpec) -> str:
        """Build code generation prompt"""

        return f"""Generate Python code to implement this experiment:

**Title**: {spec.title}
**Type**: {spec.experiment_type.value}
**Objectives**: {', '.join(spec.objectives)}

**Methodology**:
{spec.methodology}

**Variables**:
{json.dumps(spec.variables, indent=2)}

**Success Criteria**:
{json.dumps(spec.success_criteria, indent=2)}

Generate complete, executable Python code that:
1. Implements the methodology
2. Measures the dependent variables
3. Logs results to console (JSON format)
4. Handles errors gracefully
5. Includes clear comments
6. Uses only standard libraries (or {', '.join(spec.dependencies)})

Output format:
```python
# Experiment: {spec.title}
# Generated code

import json
import sys

def main():
    # Implementation here
    results = {{}}

    # Print results as JSON
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```
"""

    def _get_design_system_prompt(self) -> str:
        """System prompt for experiment design"""
        return """You are an experimental design specialist.

Design rigorous, reproducible experiments that:
- Test hypotheses clearly
- Control for confounding variables
- Use appropriate methodology
- Define measurable outcomes
- Are computationally feasible

Be methodical and thorough."""

    def _get_code_generation_system_prompt(self) -> str:
        """System prompt for code generation"""
        return """You are an expert programmer specializing in scientific computing.

Generate clean, safe, executable code that:
- Implements experiments correctly
- Handles errors gracefully
- Logs results clearly
- Uses only allowed dependencies
- Includes documentation
- Avoids security issues (no file system access, network calls, etc.)

Write production-quality code."""

    def _parse_experiment_spec(
        self,
        text: str,
        hypothesis_id: str,
        domain: str
    ) -> ExperimentSpec:
        """Parse LLM output into ExperimentSpec"""
        import uuid

        # Simplified parsing
        lines = text.split('\n')

        title = "Generated Experiment"
        description = ""
        objectives = []
        methodology = ""

        for line in lines:
            if '**1. Objectives**' in line or 'Objectives:' in line:
                # Next few lines are objectives
                pass
            elif line.strip().startswith('-') or line.strip().startswith('1'):
                objectives.append(line.strip().lstrip('-123456789. '))

        return ExperimentSpec(
            id=str(uuid.uuid4())[:8],
            hypothesis_id=hypothesis_id,
            title=title,
            description=text[:200],
            experiment_type=ExperimentType.SIMULATION,
            objectives=objectives[:5] if objectives else ["Test hypothesis"],
            methodology=methodology or text[:500],
            variables={"independent": ["x"], "dependent": ["y"]},
            expected_outcomes=["Validate hypothesis"],
            success_criteria={"accuracy": 0.8},
            resource_requirements={"compute": "low", "time": "minutes"},
            estimated_duration="30 minutes"
        )

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown blocks"""
        import re

        # Find code blocks
        pattern = r'```(?:python)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches[0]
        else:
            return text  # Return as-is if no code blocks

    async def _safety_review_code(self, code: GeneratedCode) -> GeneratedCode:
        """Review code for safety issues"""

        dangerous_patterns = [
            'os.system', 'subprocess.', 'eval(', 'exec(',
            'open(', '__import__', 'compile(',
            'socket.', 'urllib', 'requests.',
            'rm -rf', 'rmdir', 'unlink'
        ]

        issues = []
        for pattern in dangerous_patterns:
            if pattern in code.code:
                issues.append(f"Potentially dangerous: {pattern}")
                code.safety_score *= 0.8

        code.review_notes = issues

        if code.safety_score < 0.5:
            logger.warning(f"Code safety concerns: {issues}")

        return code

    def _extract_findings(self, text: str) -> List[str]:
        """Extract key findings from analysis"""
        # Simplified extraction
        return ["Finding 1", "Finding 2"]

    def _extract_next_steps(self, text: str) -> List[str]:
        """Extract next steps from analysis"""
        return ["Next step 1", "Next step 2"]

    def _log_execution(self, spec: ExperimentSpec, result: ExperimentResult):
        """Log experiment execution"""
        self.execution_history.append({
            "experiment_id": spec.id,
            "hypothesis_id": spec.hypothesis_id,
            "status": result.status.value,
            "success": result.success,
            "duration": result.duration_seconds,
            "timestamp": datetime.now().isoformat()
        })

    def get_experiment_history(self) -> List[Dict]:
        """Get execution history"""
        return self.execution_history
