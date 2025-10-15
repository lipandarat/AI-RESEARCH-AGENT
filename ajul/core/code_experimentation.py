"""
Code Experimentation & Iterative Refinement Module

Enables autonomous code improvement through:
- Automated test generation
- Code coverage analysis
- Iterative refinement cycles
- Quality assessment
- Benchmark evaluation

Inspired by Devin, AutoGPT, and gpt-engineer approaches.
Focuses on code quality improvement through experimentation.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import subprocess
import tempfile
import os
import json
import re
import hashlib

from anthropic import AsyncAnthropic
from loguru import logger


class RefinementGoal(str, Enum):
    """Code refinement objectives"""
    INCREASE_COVERAGE = "increase_coverage"
    IMPROVE_PERFORMANCE = "improve_performance"
    FIX_BUGS = "fix_bugs"
    ENHANCE_READABILITY = "enhance_readability"
    ADD_FEATURES = "add_features"
    REFACTOR = "refactor"


class CodeQuality(str, Enum):
    """Code quality levels"""
    EXCELLENT = "excellent"  # >90% coverage, all tests pass
    GOOD = "good"  # >70% coverage, most tests pass
    FAIR = "fair"  # >50% coverage, some tests pass
    POOR = "poor"  # <50% coverage or failing tests
    UNKNOWN = "unknown"


@dataclass
class CodeArtifact:
    """Code under experimentation"""
    id: str
    name: str
    code: str
    language: str = "python"
    version: int = 1
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TestSuite:
    """Test suite for code"""
    tests: List[str]  # Test code
    test_count: int
    passing: int = 0
    failing: int = 0
    coverage_percent: float = 0.0
    execution_time: float = 0.0


@dataclass
class CoverageReport:
    """Code coverage analysis"""
    total_lines: int
    covered_lines: int
    coverage_percent: float
    uncovered_regions: List[Dict[str, Any]]
    branch_coverage: float = 0.0


@dataclass
class RefinementCycle:
    """Single refinement iteration"""
    cycle_number: int
    goal: RefinementGoal
    original_code: CodeArtifact
    refined_code: CodeArtifact
    test_results: TestSuite
    coverage_report: CoverageReport
    improvements: List[str]
    quality_score: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BenchmarkResult:
    """Benchmark evaluation results"""
    benchmark_name: str
    tasks_attempted: int
    tasks_passed: int
    success_rate: float
    avg_execution_time: float
    errors: List[str] = field(default_factory=list)


class CodeExperimentationEngine:
    """
    Engine for iterative code improvement through experimentation.

    Workflow (inspired by Devin):
    1. Assess current code quality
    2. Run existing tests
    3. Analyze coverage
    4. Generate new tests for uncovered areas
    5. Refine code to improve quality
    6. Review and validate improvements
    7. Iterate until goal achieved
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        workspace_dir: str = "./code_experiments",
        max_refinement_cycles: int = 5,
        target_coverage: float = 0.80
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.workspace_dir = workspace_dir
        self.max_refinement_cycles = max_refinement_cycles
        self.target_coverage = target_coverage

        # Tracking
        self.artifacts: Dict[str, CodeArtifact] = {}
        self.refinement_history: List[RefinementCycle] = []
        self.benchmarks: List[BenchmarkResult] = []

        os.makedirs(workspace_dir, exist_ok=True)

        logger.info("Code experimentation engine initialized")

    async def assess_code_quality(
        self,
        code: CodeArtifact
    ) -> Dict[str, Any]:
        """
        Assess current code quality.

        Args:
            code: Code to assess

        Returns:
            Quality assessment
        """
        logger.info(f"Assessing code quality: {code.name}")

        prompt = f"""Assess this Python code's quality:

```python
{code.code}
```

Provide assessment:

1. **Code Quality** (excellent/good/fair/poor)
2. **Strengths** (what's done well)
3. **Weaknesses** (what needs improvement)
4. **Test Coverage Estimate** (0-100%)
5. **Complexity Score** (1-10, higher = more complex)
6. **Maintainability** (easy/moderate/difficult)
7. **Key Issues** (bugs, code smells, anti-patterns)
8. **Improvement Priorities** (what to focus on first)

Be specific and actionable.
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,
                system="You are a code quality expert. Provide objective, actionable assessments.",
                messages=[{"role": "user", "content": prompt}]
            )

            assessment_text = response.content[0].text

            # Parse quality level
            quality = CodeQuality.UNKNOWN
            if "excellent" in assessment_text.lower():
                quality = CodeQuality.EXCELLENT
            elif "good" in assessment_text.lower():
                quality = CodeQuality.GOOD
            elif "fair" in assessment_text.lower():
                quality = CodeQuality.FAIR
            elif "poor" in assessment_text.lower():
                quality = CodeQuality.POOR

            assessment = {
                "code_id": code.id,
                "quality": quality.value,
                "full_assessment": assessment_text,
                "timestamp": datetime.now().isoformat()
            }

            logger.success(f"Quality assessment complete: {quality.value}")
            return assessment

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {"error": str(e)}

    async def generate_tests(
        self,
        code: CodeArtifact,
        focus_areas: Optional[List[str]] = None
    ) -> TestSuite:
        """
        Generate comprehensive test suite for code.

        Args:
            code: Code to test
            focus_areas: Specific areas to focus testing on

        Returns:
            Generated test suite
        """
        logger.info(f"Generating tests for: {code.name}")

        focus_str = f"\nFocus on testing: {', '.join(focus_areas)}" if focus_areas else ""

        prompt = f"""Generate comprehensive pytest tests for this Python code:

```python
{code.code}
```
{focus_str}

Generate tests that:
1. Cover all functions/methods
2. Test edge cases and boundary conditions
3. Test error handling
4. Test typical use cases
5. Are independent and isolated
6. Use clear, descriptive names

Output complete pytest code:
```python
import pytest
# Generated tests
```
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.4,
                system="You are a test generation expert. Write thorough, realistic tests.",
                messages=[{"role": "user", "content": prompt}]
            )

            test_code = self._extract_code(response.content[0].text)

            # Count test functions
            test_count = len(re.findall(r'def test_\w+', test_code))

            test_suite = TestSuite(
                tests=[test_code],
                test_count=test_count
            )

            logger.success(f"Generated {test_count} tests")
            return test_suite

        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return TestSuite(tests=[], test_count=0)

    async def run_tests(
        self,
        code: CodeArtifact,
        test_suite: TestSuite
    ) -> TestSuite:
        """
        Execute test suite against code.

        Args:
            code: Code to test
            test_suite: Tests to run

        Returns:
            Updated test suite with results
        """
        logger.info(f"Running {test_suite.test_count} tests")

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code
                code_file = os.path.join(tmpdir, f"{code.name}.py")
                with open(code_file, 'w') as f:
                    f.write(code.code)

                # Write tests
                test_file = os.path.join(tmpdir, f"test_{code.name}.py")
                with open(test_file, 'w') as f:
                    # Add import of code module
                    test_code = test_suite.tests[0]
                    test_code = f"import {code.name}\n{test_code}"
                    f.write(test_code)

                # Run pytest
                start_time = datetime.now()

                process = await asyncio.create_subprocess_exec(
                    "pytest", test_file, "-v", "--tb=short",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir
                )

                stdout, stderr = await process.communicate()

                execution_time = (datetime.now() - start_time).total_seconds()

                # Parse results
                output = stdout.decode('utf-8')

                # Count passed/failed (simplified)
                passed = len(re.findall(r'PASSED', output))
                failed = len(re.findall(r'FAILED', output))

                test_suite.passing = passed
                test_suite.failing = failed
                test_suite.execution_time = execution_time

                logger.info(f"Tests complete: {passed} passed, {failed} failed")

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            test_suite.failing = test_suite.test_count

        return test_suite

    async def analyze_coverage(
        self,
        code: CodeArtifact,
        test_suite: TestSuite
    ) -> CoverageReport:
        """
        Analyze code coverage from tests.

        Args:
            code: Code being tested
            test_suite: Test suite

        Returns:
            Coverage report
        """
        logger.info("Analyzing code coverage")

        # Simplified coverage analysis
        # In production, use coverage.py library

        total_lines = len([l for l in code.code.split('\n') if l.strip() and not l.strip().startswith('#')])

        # Estimate coverage based on test count vs function count
        func_count = len(re.findall(r'def \w+', code.code))
        coverage_estimate = min(1.0, test_suite.test_count / max(func_count, 1)) if func_count > 0 else 0.0

        covered_lines = int(total_lines * coverage_estimate)

        report = CoverageReport(
            total_lines=total_lines,
            covered_lines=covered_lines,
            coverage_percent=coverage_estimate * 100,
            uncovered_regions=[],
            branch_coverage=coverage_estimate * 90  # Estimate
        )

        logger.info(f"Coverage: {report.coverage_percent:.1f}%")
        return report

    async def refine_code(
        self,
        code: CodeArtifact,
        goal: RefinementGoal,
        context: Dict[str, Any]
    ) -> CodeArtifact:
        """
        Refine code to achieve goal.

        Args:
            code: Code to refine
            goal: Refinement objective
            context: Context (test results, coverage, etc.)

        Returns:
            Refined code
        """
        logger.info(f"Refining code: goal={goal.value}")

        prompt = self._build_refinement_prompt(code, goal, context)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0.3,
                system=self._get_refinement_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            refined_code_text = self._extract_code(response.content[0].text)

            refined = CodeArtifact(
                id=self._generate_id(refined_code_text),
                name=code.name,
                code=refined_code_text,
                language=code.language,
                version=code.version + 1,
                parent_id=code.id
            )

            self.artifacts[refined.id] = refined

            logger.success(f"Code refined: v{refined.version}")
            return refined

        except Exception as e:
            logger.error(f"Code refinement failed: {e}")
            return code  # Return original on failure

    async def run_refinement_cycle(
        self,
        code: CodeArtifact,
        goal: RefinementGoal = RefinementGoal.INCREASE_COVERAGE
    ) -> RefinementCycle:
        """
        Execute one complete refinement cycle.

        Args:
            code: Code to improve
            goal: Refinement goal

        Returns:
            Refinement cycle results
        """
        cycle_num = len([c for c in self.refinement_history if c.original_code.name == code.name]) + 1

        logger.info(f"Starting refinement cycle {cycle_num} for {code.name}")

        # 1. Generate tests
        test_suite = await self.generate_tests(code)

        # 2. Run tests
        test_suite = await self.run_tests(code, test_suite)

        # 3. Analyze coverage
        coverage = await self.analyze_coverage(code, test_suite)

        # 4. Refine code
        context = {
            "test_results": {
                "passing": test_suite.passing,
                "failing": test_suite.failing,
                "coverage": coverage.coverage_percent
            },
            "uncovered_areas": coverage.uncovered_regions
        }

        refined = await self.refine_code(code, goal, context)

        # 5. Calculate quality score
        quality_score = self._calculate_quality_score(test_suite, coverage)

        # 6. Identify improvements
        improvements = self._identify_improvements(code, refined, test_suite, coverage)

        cycle = RefinementCycle(
            cycle_number=cycle_num,
            goal=goal,
            original_code=code,
            refined_code=refined,
            test_results=test_suite,
            coverage_report=coverage,
            improvements=improvements,
            quality_score=quality_score
        )

        self.refinement_history.append(cycle)

        logger.success(
            f"Cycle {cycle_num} complete: "
            f"coverage={coverage.coverage_percent:.1f}%, "
            f"quality={quality_score:.2f}"
        )

        return cycle

    async def iterative_improvement(
        self,
        code: CodeArtifact,
        goal: RefinementGoal = RefinementGoal.INCREASE_COVERAGE,
        max_cycles: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run iterative improvement until goal achieved.

        Args:
            code: Initial code
            goal: Refinement goal
            max_cycles: Maximum cycles (defaults to engine setting)

        Returns:
            Complete improvement results
        """
        max_cycles = max_cycles or self.max_refinement_cycles

        logger.info(
            f"Starting iterative improvement: "
            f"goal={goal.value}, max_cycles={max_cycles}"
        )

        current_code = code
        cycles = []

        for i in range(max_cycles):
            cycle = await self.run_refinement_cycle(current_code, goal)
            cycles.append(cycle)

            # Check if goal achieved
            if goal == RefinementGoal.INCREASE_COVERAGE:
                if cycle.coverage_report.coverage_percent >= self.target_coverage * 100:
                    logger.success(
                        f"Target coverage achieved: "
                        f"{cycle.coverage_report.coverage_percent:.1f}%"
                    )
                    break

            # Use refined code for next cycle
            current_code = cycle.refined_code

        # Summary
        initial_coverage = cycles[0].coverage_report.coverage_percent if cycles else 0
        final_coverage = cycles[-1].coverage_report.coverage_percent if cycles else 0
        improvement = final_coverage - initial_coverage

        return {
            "code_name": code.name,
            "goal": goal.value,
            "cycles_run": len(cycles),
            "initial_coverage": initial_coverage,
            "final_coverage": final_coverage,
            "improvement": improvement,
            "final_code_id": cycles[-1].refined_code.id if cycles else code.id,
            "quality_progression": [c.quality_score for c in cycles],
            "timestamp": datetime.now().isoformat()
        }

    async def run_benchmark(
        self,
        benchmark_name: str,
        tasks: List[Dict[str, Any]]
    ) -> BenchmarkResult:
        """
        Run code against benchmark tasks.

        Inspired by gpt-engineer's APPS and MBPP benchmarks.

        Args:
            benchmark_name: Name of benchmark
            tasks: List of benchmark tasks

        Returns:
            Benchmark results
        """
        logger.info(f"Running benchmark: {benchmark_name} ({len(tasks)} tasks)")

        passed = 0
        total_time = 0.0
        errors = []

        for i, task in enumerate(tasks[:10]):  # Limit for demo
            try:
                # Generate code for task
                code = await self._generate_code_for_task(task)

                # Test code
                start = datetime.now()
                success = await self._test_benchmark_task(code, task)
                duration = (datetime.now() - start).total_seconds()

                total_time += duration

                if success:
                    passed += 1
                else:
                    errors.append(f"Task {i+1} failed")

            except Exception as e:
                errors.append(f"Task {i+1} error: {e}")

        result = BenchmarkResult(
            benchmark_name=benchmark_name,
            tasks_attempted=len(tasks[:10]),
            tasks_passed=passed,
            success_rate=passed / len(tasks[:10]) if tasks else 0,
            avg_execution_time=total_time / len(tasks[:10]) if tasks else 0,
            errors=errors
        )

        self.benchmarks.append(result)

        logger.success(
            f"Benchmark complete: {passed}/{len(tasks[:10])} passed "
            f"({result.success_rate*100:.1f}%)"
        )

        return result

    # Helper methods

    def _build_refinement_prompt(
        self,
        code: CodeArtifact,
        goal: RefinementGoal,
        context: Dict[str, Any]
    ) -> str:
        """Build refinement prompt"""

        base = f"""Refine this Python code to {goal.value.replace('_', ' ')}:

```python
{code.code}
```

**Current Status**:
- Tests passing: {context.get('test_results', {}).get('passing', 0)}
- Tests failing: {context.get('test_results', {}).get('failing', 0)}
- Coverage: {context.get('test_results', {}).get('coverage', 0):.1f}%

"""

        if goal == RefinementGoal.INCREASE_COVERAGE:
            base += """**Refinement Goal**: Increase test coverage

Improve the code to be more testable:
1. Break down complex functions
2. Add clear error handling
3. Make dependencies explicit
4. Reduce coupling
5. Add docstrings

Output improved code:
"""
        elif goal == RefinementGoal.FIX_BUGS:
            base += """**Refinement Goal**: Fix bugs and issues

Fix identified bugs:
1. Handle edge cases
2. Fix logic errors
3. Improve error handling
4. Validate inputs

Output corrected code:
"""

        return base

    def _get_refinement_system_prompt(self) -> str:
        """System prompt for code refinement"""
        return """You are a senior software engineer specialized in code improvement.

Refine code to be:
- More maintainable and readable
- Better tested and testable
- More robust and error-tolerant
- Well-documented
- Following best practices

Make incremental, focused improvements. Don't over-engineer."""

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown blocks"""
        pattern = r'```(?:python)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        return matches[0] if matches else text

    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text"""
        return hashlib.sha256(text.encode()).hexdigest()[:12]

    def _calculate_quality_score(
        self,
        test_suite: TestSuite,
        coverage: CoverageReport
    ) -> float:
        """Calculate overall quality score"""

        # Test pass rate
        pass_rate = test_suite.passing / max(test_suite.test_count, 1)

        # Coverage
        coverage_score = coverage.coverage_percent / 100

        # Weighted combination
        score = (0.6 * pass_rate) + (0.4 * coverage_score)

        return score

    def _identify_improvements(
        self,
        original: CodeArtifact,
        refined: CodeArtifact,
        test_suite: TestSuite,
        coverage: CoverageReport
    ) -> List[str]:
        """Identify what improved"""

        improvements = []

        if refined.code != original.code:
            improvements.append("Code structure improved")

        if test_suite.passing > 0:
            improvements.append(f"{test_suite.passing} tests passing")

        if coverage.coverage_percent > 50:
            improvements.append(f"Coverage at {coverage.coverage_percent:.1f}%")

        return improvements or ["Initial iteration"]

    async def _generate_code_for_task(self, task: Dict[str, Any]) -> str:
        """Generate code for benchmark task"""
        # Simplified - in production, use full generation
        return "def solution(): pass"

    async def _test_benchmark_task(self, code: str, task: Dict[str, Any]) -> bool:
        """Test code against benchmark task"""
        # Simplified - in production, run actual tests
        return True

    def get_improvement_summary(self) -> Dict[str, Any]:
        """Get summary of all improvements"""

        if not self.refinement_history:
            return {}

        return {
            "total_cycles": len(self.refinement_history),
            "codes_improved": len(set(c.original_code.name for c in self.refinement_history)),
            "avg_coverage_improvement": sum(
                c.coverage_report.coverage_percent for c in self.refinement_history
            ) / len(self.refinement_history),
            "avg_quality_score": sum(
                c.quality_score for c in self.refinement_history
            ) / len(self.refinement_history),
            "recent_cycles": [
                {
                    "code": c.original_code.name,
                    "cycle": c.cycle_number,
                    "coverage": c.coverage_report.coverage_percent,
                    "quality": c.quality_score
                }
                for c in self.refinement_history[-5:]
            ]
        }
