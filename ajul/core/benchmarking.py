"""
Prediction Benchmarking Module

Measures agent prediction quality against:
- Existing scientific results
- Novel pattern detection
- Prediction accuracy metrics
- Autonomous system evaluation

Critical for evaluating AI-Researcher system performance.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import statistics

from loguru import logger


class BenchmarkType(str, Enum):
    """Types of benchmarks"""
    PREDICTION_ACCURACY = "prediction_accuracy"
    HYPOTHESIS_QUALITY = "hypothesis_quality"
    NOVELTY_DETECTION = "novelty_detection"
    SCIENTIFIC_VALIDITY = "scientific_validity"
    REPRODUCIBILITY = "reproducibility"


class ResultCategory(str, Enum):
    """Benchmark result categories"""
    EXCELLENT = "excellent"  # >90%
    GOOD = "good"  # 70-90%
    FAIR = "fair"  # 50-70%
    POOR = "poor"  # <50%


@dataclass
class BenchmarkTask:
    """Single benchmark task"""
    id: str
    type: BenchmarkType
    name: str
    description: str
    ground_truth: Any
    difficulty: float  # 0-1


@dataclass
class BenchmarkResult:
    """Result from benchmark evaluation"""
    task_id: str
    prediction: Any
    ground_truth: Any
    score: float  # 0-1
    correct: bool
    error_analysis: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BenchmarkReport:
    """Comprehensive benchmark report"""
    id: str
    benchmark_name: str
    total_tasks: int
    tasks_completed: int
    overall_score: float
    category: ResultCategory
    results_by_type: Dict[BenchmarkType, float]
    strengths: List[str]
    weaknesses: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class BenchmarkingEngine:
    """
    Engine for benchmarking agent predictions.

    Evaluates:
    - Prediction accuracy
    - Hypothesis quality
    - Novel pattern detection
    - Scientific validity
    """

    def __init__(self):
        self.tasks: Dict[str, BenchmarkTask] = {}
        self.results: List[BenchmarkResult] = []
        self.reports: List[BenchmarkReport] = []

        logger.info("Benchmarking engine initialized")

    def add_benchmark_task(
        self,
        task_id: str,
        task_type: BenchmarkType,
        name: str,
        description: str,
        ground_truth: Any,
        difficulty: float = 0.5
    ) -> BenchmarkTask:
        """Add benchmark task."""

        task = BenchmarkTask(
            id=task_id,
            type=task_type,
            name=name,
            description=description,
            ground_truth=ground_truth,
            difficulty=difficulty
        )

        self.tasks[task_id] = task
        logger.info(f"Benchmark task added: {name}")
        return task

    def evaluate_prediction(
        self,
        task_id: str,
        prediction: Any
    ) -> BenchmarkResult:
        """Evaluate prediction against ground truth."""

        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Calculate score
        score = self._calculate_score(prediction, task.ground_truth, task.type)
        correct = score >= 0.7

        result = BenchmarkResult(
            task_id=task_id,
            prediction=prediction,
            ground_truth=task.ground_truth,
            score=score,
            correct=correct,
            error_analysis=self._analyze_error(prediction, task.ground_truth)
        )

        self.results.append(result)
        logger.success(f"Prediction evaluated: {score:.2f}")
        return result

    def generate_benchmark_report(
        self,
        benchmark_name: str,
        task_ids: Optional[List[str]] = None
    ) -> BenchmarkReport:
        """Generate comprehensive benchmark report."""

        # Filter results
        if task_ids:
            relevant_results = [r for r in self.results if r.task_id in task_ids]
        else:
            relevant_results = self.results

        if not relevant_results:
            raise ValueError("No results to report")

        # Calculate metrics
        total_tasks = len(relevant_results)
        overall_score = statistics.mean([r.score for r in relevant_results])

        # Score by type
        results_by_type = {}
        for btype in BenchmarkType:
            type_results = [r for r in relevant_results
                          if self.tasks[r.task_id].type == btype]
            if type_results:
                results_by_type[btype] = statistics.mean([r.score for r in type_results])

        # Categorize
        category = self._categorize_performance(overall_score)

        # Identify strengths/weaknesses
        strengths = [
            f"{k.value}: {v*100:.1f}%"
            for k, v in results_by_type.items() if v >= 0.8
        ]
        weaknesses = [
            f"{k.value}: {v*100:.1f}%"
            for k, v in results_by_type.items() if v < 0.6
        ]

        report = BenchmarkReport(
            id=f"report_{datetime.now().timestamp()}",
            benchmark_name=benchmark_name,
            total_tasks=total_tasks,
            tasks_completed=total_tasks,
            overall_score=overall_score,
            category=category,
            results_by_type=results_by_type,
            strengths=strengths,
            weaknesses=weaknesses
        )

        self.reports.append(report)
        logger.success(f"Benchmark report: {category.value} ({overall_score*100:.1f}%)")
        return report

    def _calculate_score(
        self,
        prediction: Any,
        ground_truth: Any,
        task_type: BenchmarkType
    ) -> float:
        """Calculate prediction score."""

        # Simple equality check (in production, use domain-specific metrics)
        if prediction == ground_truth:
            return 1.0

        # Partial credit for similar predictions
        try:
            if isinstance(prediction, (int, float)) and isinstance(ground_truth, (int, float)):
                error = abs(prediction - ground_truth) / max(abs(ground_truth), 1)
                return max(0.0, 1.0 - error)
        except:
            pass

        return 0.0

    def _analyze_error(self, prediction: Any, ground_truth: Any) -> str:
        """Analyze prediction error."""

        if prediction == ground_truth:
            return "Perfect match"

        return f"Predicted {prediction}, expected {ground_truth}"

    def _categorize_performance(self, score: float) -> ResultCategory:
        """Categorize performance level."""

        if score >= 0.9:
            return ResultCategory.EXCELLENT
        elif score >= 0.7:
            return ResultCategory.GOOD
        elif score >= 0.5:
            return ResultCategory.FAIR
        else:
            return ResultCategory.POOR

    def get_benchmark_summary(self) -> Dict[str, Any]:
        """Get benchmarking summary."""

        return {
            "total_tasks": len(self.tasks),
            "total_results": len(self.results),
            "total_reports": len(self.reports),
            "latest_report": self.reports[-1].category.value if self.reports else None,
            "overall_accuracy": statistics.mean([r.score for r in self.results]) if self.results else 0.0
        }
