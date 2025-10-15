"""
Self-Evaluation & Strategy Update Module

Enables agent to assess its own performance and update strategies.

Key capabilities:
- Evaluate prediction accuracy and quality
- Assess hypothesis generation effectiveness
- Measure experiment success rates
- Analyze learning progress
- Identify improvement areas
- Update strategies based on performance
- Track performance trends over time

Integrates with:
- evolution_optimizer.py for strategy evolution
- expert_feedback.py for external validation
- All core modules for performance metrics
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

from loguru import logger


class PerformanceMetric(str, Enum):
    """Performance metrics"""
    PREDICTION_ACCURACY = "prediction_accuracy"
    HYPOTHESIS_QUALITY = "hypothesis_quality"
    EXPERIMENT_SUCCESS_RATE = "experiment_success_rate"
    ANALYSIS_CORRECTNESS = "analysis_correctness"
    EXPERT_APPROVAL_RATE = "expert_approval_rate"
    LEARNING_RATE = "learning_rate"
    EFFICIENCY = "efficiency"


class EvaluationPeriod(str, Enum):
    """Evaluation time periods"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class PerformanceLevel(str, Enum):
    """Performance level classifications"""
    EXCELLENT = "excellent"  # >90%
    GOOD = "good"  # 70-90%
    FAIR = "fair"  # 50-70%
    POOR = "poor"  # <50%


@dataclass
class PerformanceRecord:
    """Single performance record"""
    metric: PerformanceMetric
    value: float  # 0-1
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Comprehensive evaluation report"""
    id: str
    period: EvaluationPeriod
    start_date: datetime
    end_date: datetime
    metrics: Dict[PerformanceMetric, float]
    performance_level: PerformanceLevel
    strengths: List[str]
    weaknesses: List[str]
    trends: Dict[str, str]  # improving, declining, stable
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyUpdate:
    """Strategy update decision"""
    id: str
    trigger: str  # What triggered the update
    current_strategy: Dict[str, Any]
    proposed_changes: Dict[str, Any]
    expected_improvement: float
    rationale: str
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False


@dataclass
class ImprovementPlan:
    """Action plan for improvement"""
    id: str
    focus_areas: List[str]
    actions: List[Dict[str, Any]]
    target_metrics: Dict[PerformanceMetric, float]
    timeline: str
    priority: int
    created_at: datetime = field(default_factory=datetime.now)


class SelfEvaluationEngine:
    """
    Engine for agent self-evaluation and strategy updates.

    Workflow:
    1. Continuously collect performance data
    2. Periodically evaluate performance
    3. Identify trends and patterns
    4. Compare against targets and benchmarks
    5. Generate improvement recommendations
    6. Propose strategy updates
    7. Apply approved updates
    8. Monitor impact of changes
    """

    def __init__(
        self,
        evaluation_frequency: EvaluationPeriod = EvaluationPeriod.WEEKLY,
        performance_targets: Optional[Dict[PerformanceMetric, float]] = None,
        auto_update_threshold: float = 0.8,  # Auto-apply if confidence > threshold
        enable_auto_updates: bool = False
    ):
        self.evaluation_frequency = evaluation_frequency
        self.performance_targets = performance_targets or self._default_targets()
        self.auto_update_threshold = auto_update_threshold
        self.enable_auto_updates = enable_auto_updates

        # Storage
        self.performance_records: List[PerformanceRecord] = []
        self.evaluation_reports: List[EvaluationReport] = []
        self.strategy_updates: List[StrategyUpdate] = []
        self.improvement_plans: List[ImprovementPlan] = []

        # Current state
        self.current_strategy: Dict[str, Any] = {}
        self.last_evaluation_date: Optional[datetime] = None

        logger.info("Self-evaluation engine initialized")

    def _default_targets(self) -> Dict[PerformanceMetric, float]:
        """Default performance targets"""
        return {
            PerformanceMetric.PREDICTION_ACCURACY: 0.80,
            PerformanceMetric.HYPOTHESIS_QUALITY: 0.75,
            PerformanceMetric.EXPERIMENT_SUCCESS_RATE: 0.70,
            PerformanceMetric.ANALYSIS_CORRECTNESS: 0.85,
            PerformanceMetric.EXPERT_APPROVAL_RATE: 0.75,
            PerformanceMetric.LEARNING_RATE: 0.60,
            PerformanceMetric.EFFICIENCY: 0.70
        }

    def record_performance(
        self,
        metric: PerformanceMetric,
        value: float,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Record performance metric.

        Args:
            metric: Performance metric
            value: Metric value (0-1)
            context: Additional context
        """
        record = PerformanceRecord(
            metric=metric,
            value=value,
            timestamp=datetime.now(),
            context=context or {}
        )

        self.performance_records.append(record)

        logger.debug(f"Performance recorded: {metric.value}={value:.3f}")

    def evaluate_performance(
        self,
        period: Optional[EvaluationPeriod] = None
    ) -> EvaluationReport:
        """
        Evaluate performance over period.

        Args:
            period: Evaluation period (defaults to engine frequency)

        Returns:
            Evaluation report
        """
        period = period or self.evaluation_frequency

        logger.info(f"Evaluating performance for period: {period.value}")

        # Determine time range
        end_date = datetime.now()
        start_date = self._get_period_start(end_date, period)

        # Filter records for period
        period_records = [
            r for r in self.performance_records
            if start_date <= r.timestamp <= end_date
        ]

        if not period_records:
            logger.warning("No performance records for period")
            return self._create_empty_report(period, start_date, end_date)

        # Calculate metrics
        metrics = self._calculate_period_metrics(period_records)

        # Determine performance level
        avg_performance = statistics.mean(metrics.values())
        performance_level = self._classify_performance(avg_performance)

        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(metrics)

        # Analyze trends
        trends = self._analyze_trends(period_records)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics,
            weaknesses,
            trends
        )

        # Create report
        report = EvaluationReport(
            id=self._generate_id(f"eval_{datetime.now()}"),
            period=period,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            performance_level=performance_level,
            strengths=strengths,
            weaknesses=weaknesses,
            trends=trends,
            recommendations=recommendations
        )

        self.evaluation_reports.append(report)
        self.last_evaluation_date = end_date

        logger.success(
            f"Evaluation complete: {performance_level.value} "
            f"({avg_performance*100:.1f}%)"
        )

        return report

    def propose_strategy_update(
        self,
        trigger: str,
        proposed_changes: Dict[str, Any],
        rationale: str,
        expected_improvement: float = 0.1
    ) -> StrategyUpdate:
        """
        Propose strategy update.

        Args:
            trigger: What triggered this update
            proposed_changes: Changes to strategy
            rationale: Why these changes
            expected_improvement: Expected improvement (0-1)

        Returns:
            Strategy update proposal
        """
        logger.info(f"Proposing strategy update: {trigger}")

        update = StrategyUpdate(
            id=self._generate_id(f"update_{datetime.now()}"),
            trigger=trigger,
            current_strategy=self.current_strategy.copy(),
            proposed_changes=proposed_changes,
            expected_improvement=expected_improvement,
            rationale=rationale
        )

        self.strategy_updates.append(update)

        # Auto-apply if enabled and confidence high
        if self.enable_auto_updates and expected_improvement > self.auto_update_threshold:
            self.apply_strategy_update(update.id)

        logger.success(f"Strategy update proposed: {update.id}")
        return update

    def apply_strategy_update(self, update_id: str) -> bool:
        """
        Apply strategy update.

        Args:
            update_id: Update to apply

        Returns:
            Success status
        """
        logger.info(f"Applying strategy update: {update_id}")

        update = next(
            (u for u in self.strategy_updates if u.id == update_id),
            None
        )

        if not update:
            logger.error(f"Update not found: {update_id}")
            return False

        # Apply changes
        for key, value in update.proposed_changes.items():
            self.current_strategy[key] = value

        update.applied = True

        logger.success(f"Strategy updated: {len(update.proposed_changes)} changes applied")
        return True

    def create_improvement_plan(
        self,
        report: EvaluationReport
    ) -> ImprovementPlan:
        """
        Create improvement plan from evaluation.

        Args:
            report: Evaluation report

        Returns:
            Improvement plan
        """
        logger.info("Creating improvement plan")

        # Focus on weaknesses
        focus_areas = report.weaknesses[:3]  # Top 3 weaknesses

        # Generate actions
        actions = []
        for weakness in focus_areas:
            action = self._generate_improvement_action(weakness, report)
            actions.append(action)

        # Set target metrics
        target_metrics = {}
        for metric, current_value in report.metrics.items():
            # Target 10-20% improvement
            target_value = min(1.0, current_value * 1.15)
            target_metrics[metric] = target_value

        plan = ImprovementPlan(
            id=self._generate_id(f"plan_{datetime.now()}"),
            focus_areas=focus_areas,
            actions=actions,
            target_metrics=target_metrics,
            timeline=self._determine_timeline(report.period),
            priority=self._calculate_priority(report.performance_level)
        )

        self.improvement_plans.append(plan)

        logger.success(f"Improvement plan created: {len(actions)} actions")
        return plan

    def check_if_evaluation_due(self) -> bool:
        """Check if evaluation is due based on frequency"""

        if not self.last_evaluation_date:
            return True

        time_since_last = datetime.now() - self.last_evaluation_date

        if self.evaluation_frequency == EvaluationPeriod.DAILY:
            return time_since_last >= timedelta(days=1)
        elif self.evaluation_frequency == EvaluationPeriod.WEEKLY:
            return time_since_last >= timedelta(weeks=1)
        elif self.evaluation_frequency == EvaluationPeriod.MONTHLY:
            return time_since_last >= timedelta(days=30)
        elif self.evaluation_frequency == EvaluationPeriod.QUARTERLY:
            return time_since_last >= timedelta(days=90)

        return False

    def auto_evaluate_and_improve(self) -> Optional[Tuple[EvaluationReport, ImprovementPlan]]:
        """
        Automatically evaluate and create improvement plan if due.

        Returns:
            (report, plan) if evaluation performed, None otherwise
        """
        if not self.check_if_evaluation_due():
            return None

        logger.info("Performing automatic evaluation")

        report = self.evaluate_performance()
        plan = self.create_improvement_plan(report)

        # Propose updates if performance is poor
        if report.performance_level in [PerformanceLevel.POOR, PerformanceLevel.FAIR]:
            for recommendation in report.recommendations[:2]:
                self.propose_strategy_update(
                    trigger="automatic_evaluation",
                    proposed_changes={"focus": recommendation},
                    rationale=f"Performance is {report.performance_level.value}",
                    expected_improvement=0.15
                )

        return report, plan

    # Helper methods

    def _get_period_start(self, end_date: datetime, period: EvaluationPeriod) -> datetime:
        """Get start date for period"""
        if period == EvaluationPeriod.DAILY:
            return end_date - timedelta(days=1)
        elif period == EvaluationPeriod.WEEKLY:
            return end_date - timedelta(weeks=1)
        elif period == EvaluationPeriod.MONTHLY:
            return end_date - timedelta(days=30)
        elif period == EvaluationPeriod.QUARTERLY:
            return end_date - timedelta(days=90)
        return end_date - timedelta(days=7)

    def _calculate_period_metrics(
        self,
        records: List[PerformanceRecord]
    ) -> Dict[PerformanceMetric, float]:
        """Calculate average metrics for period"""

        metrics = {}
        for metric_type in PerformanceMetric:
            metric_records = [r for r in records if r.metric == metric_type]
            if metric_records:
                avg = statistics.mean([r.value for r in metric_records])
                metrics[metric_type] = avg

        return metrics

    def _classify_performance(self, avg: float) -> PerformanceLevel:
        """Classify overall performance"""
        if avg >= 0.9:
            return PerformanceLevel.EXCELLENT
        elif avg >= 0.7:
            return PerformanceLevel.GOOD
        elif avg >= 0.5:
            return PerformanceLevel.FAIR
        else:
            return PerformanceLevel.POOR

    def _identify_strengths_weaknesses(
        self,
        metrics: Dict[PerformanceMetric, float]
    ) -> Tuple[List[str], List[str]]:
        """Identify strengths and weaknesses"""

        strengths = []
        weaknesses = []

        for metric, value in metrics.items():
            target = self.performance_targets.get(metric, 0.7)

            if value >= target * 1.1:  # 10% above target
                strengths.append(f"{metric.value}: {value*100:.1f}%")
            elif value < target * 0.9:  # 10% below target
                weaknesses.append(f"{metric.value}: {value*100:.1f}% (target: {target*100:.1f}%)")

        return strengths, weaknesses

    def _analyze_trends(self, records: List[PerformanceRecord]) -> Dict[str, str]:
        """Analyze performance trends"""

        trends = {}

        for metric_type in PerformanceMetric:
            metric_records = [r for r in records if r.metric == metric_type]

            if len(metric_records) < 2:
                continue

            # Sort by time
            metric_records.sort(key=lambda r: r.timestamp)

            # Compare first half vs second half
            mid = len(metric_records) // 2
            first_half_avg = statistics.mean([r.value for r in metric_records[:mid]])
            second_half_avg = statistics.mean([r.value for r in metric_records[mid:]])

            diff = second_half_avg - first_half_avg

            if diff > 0.05:
                trends[metric_type.value] = "improving"
            elif diff < -0.05:
                trends[metric_type.value] = "declining"
            else:
                trends[metric_type.value] = "stable"

        return trends

    def _generate_recommendations(
        self,
        metrics: Dict[PerformanceMetric, float],
        weaknesses: List[str],
        trends: Dict[str, str]
    ) -> List[str]:
        """Generate actionable recommendations"""

        recommendations = []

        # Address weaknesses
        for weakness in weaknesses[:3]:
            if "prediction_accuracy" in weakness:
                recommendations.append("Improve prediction models with more training data")
            elif "hypothesis_quality" in weakness:
                recommendations.append("Enhance hypothesis generation with domain knowledge")
            elif "experiment_success" in weakness:
                recommendations.append("Refine experiment design methodology")
            elif "expert_approval" in weakness:
                recommendations.append("Align predictions with expert feedback patterns")

        # Address declining trends
        for metric, trend in trends.items():
            if trend == "declining":
                recommendations.append(f"Investigate cause of declining {metric}")

        return recommendations[:5]  # Top 5

    def _generate_improvement_action(
        self,
        weakness: str,
        report: EvaluationReport
    ) -> Dict[str, Any]:
        """Generate specific improvement action"""

        return {
            "weakness": weakness,
            "action": f"Address {weakness}",
            "timeline": "1-2 weeks",
            "expected_impact": "15-20% improvement"
        }

    def _determine_timeline(self, period: EvaluationPeriod) -> str:
        """Determine improvement timeline"""
        if period == EvaluationPeriod.DAILY:
            return "1-2 days"
        elif period == EvaluationPeriod.WEEKLY:
            return "1-2 weeks"
        elif period == EvaluationPeriod.MONTHLY:
            return "2-4 weeks"
        else:
            return "1-2 months"

    def _calculate_priority(self, level: PerformanceLevel) -> int:
        """Calculate improvement priority"""
        if level == PerformanceLevel.POOR:
            return 5  # Highest
        elif level == PerformanceLevel.FAIR:
            return 4
        elif level == PerformanceLevel.GOOD:
            return 2
        else:
            return 1

    def _create_empty_report(
        self,
        period: EvaluationPeriod,
        start: datetime,
        end: datetime
    ) -> EvaluationReport:
        """Create empty report when no data"""
        return EvaluationReport(
            id=self._generate_id(f"eval_{datetime.now()}"),
            period=period,
            start_date=start,
            end_date=end,
            metrics={},
            performance_level=PerformanceLevel.POOR,
            strengths=[],
            weaknesses=["No performance data available"],
            trends={},
            recommendations=["Collect performance data"]
        )

    def _generate_id(self, text: str) -> str:
        """Generate unique ID"""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary of evaluations"""

        if not self.evaluation_reports:
            return {"message": "No evaluations yet"}

        latest = self.evaluation_reports[-1]

        return {
            "total_evaluations": len(self.evaluation_reports),
            "latest_evaluation": {
                "period": latest.period.value,
                "performance_level": latest.performance_level.value,
                "metrics": {k.value: v for k, v in latest.metrics.items()},
                "strengths_count": len(latest.strengths),
                "weaknesses_count": len(latest.weaknesses)
            },
            "strategy_updates": {
                "total": len(self.strategy_updates),
                "applied": len([u for u in self.strategy_updates if u.applied]),
                "pending": len([u for u in self.strategy_updates if not u.applied])
            },
            "improvement_plans": len(self.improvement_plans),
            "performance_trend": self._calculate_overall_trend(),
            "next_evaluation_due": not self.check_if_evaluation_due()
        }

    def _calculate_overall_trend(self) -> str:
        """Calculate overall performance trend"""

        if len(self.evaluation_reports) < 2:
            return "insufficient_data"

        recent = self.evaluation_reports[-3:]  # Last 3 evaluations

        # Calculate average performance for each
        avgs = []
        for report in recent:
            if report.metrics:
                avg = statistics.mean(report.metrics.values())
                avgs.append(avg)

        if len(avgs) < 2:
            return "stable"

        # Compare first and last
        diff = avgs[-1] - avgs[0]

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"
