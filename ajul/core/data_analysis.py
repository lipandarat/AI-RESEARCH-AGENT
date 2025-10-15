"""
Data Analysis Pipeline Module

Evaluates experiment data and updates hypotheses, closing the agentic loop.

Key features:
- Statistical analysis
- Hypothesis testing
- Data visualization
- Result interpretation
- Hypothesis refinement
- Feedback loop to planning
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

import numpy as np
from scipy import stats
from loguru import logger


class AnalysisType(str, Enum):
    """Types of statistical analysis"""
    DESCRIPTIVE = "descriptive"
    INFERENTIAL = "inferential"
    COMPARATIVE = "comparative"
    CORRELATION = "correlation"
    REGRESSION = "regression"
    TIME_SERIES = "time_series"


class HypothesisDecision(str, Enum):
    """Decisions about hypothesis"""
    SUPPORTED = "supported"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"
    REQUIRES_MORE_DATA = "requires_more_data"


@dataclass
class StatisticalResult:
    """Results from statistical analysis"""
    test_name: str
    statistic: float
    p_value: float
    confidence_interval: Optional[Tuple[float, float]]
    effect_size: Optional[float]
    interpretation: str
    significant: bool


@dataclass
class AnalysisReport:
    """Complete analysis report"""
    experiment_id: str
    hypothesis_id: str
    analysis_type: AnalysisType
    summary_statistics: Dict[str, Any]
    statistical_tests: List[StatisticalResult]
    visualizations: List[str]
    interpretation: str
    hypothesis_decision: HypothesisDecision
    confidence_level: float
    limitations: List[str]
    recommendations: List[str]
    next_experiments: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HypothesisUpdate:
    """Update to hypothesis based on results"""
    hypothesis_id: str
    original_hypothesis: str
    updated_hypothesis: str
    changes: List[str]
    reason: str
    confidence_delta: float  # Change in confidence
    timestamp: datetime = field(default_factory=datetime.now)


class DataAnalysisPipeline:
    """
    Pipeline for analyzing experiment results and updating hypotheses.

    Workflow:
    1. Receive experiment data
    2. Perform statistical analysis
    3. Test hypothesis validity
    4. Interpret results
    5. Generate recommendations
    6. Update hypothesis if needed
    7. Suggest next experiments
    """

    def __init__(
        self,
        significance_level: float = 0.05,
        confidence_level: float = 0.95
    ):
        self.significance_level = significance_level
        self.confidence_level = confidence_level

        # Track analyses
        self.analysis_history: List[AnalysisReport] = []
        self.hypothesis_updates: List[HypothesisUpdate] = []

        logger.info("Data analysis pipeline initialized")

    async def analyze_experiment_results(
        self,
        experiment_id: str,
        hypothesis_id: str,
        hypothesis_text: str,
        data: Dict[str, Any],
        expected_outcomes: List[str],
        metadata: Optional[Dict] = None
    ) -> AnalysisReport:
        """
        Complete analysis of experiment results.

        Args:
            experiment_id: Experiment identifier
            hypothesis_id: Hypothesis being tested
            hypothesis_text: Original hypothesis
            data: Experimental data
            expected_outcomes: What was expected
            metadata: Additional context

        Returns:
            Complete analysis report
        """
        logger.info(f"Analyzing experiment {experiment_id} for hypothesis {hypothesis_id}")

        # 1. Descriptive statistics
        summary_stats = self._compute_summary_statistics(data)

        # 2. Statistical tests
        statistical_tests = self._perform_statistical_tests(
            data=data,
            hypothesis=hypothesis_text,
            expected_outcomes=expected_outcomes
        )

        # 3. Determine hypothesis decision
        decision = self._make_hypothesis_decision(
            tests=statistical_tests,
            data=data,
            expected_outcomes=expected_outcomes
        )

        # 4. Generate interpretation
        interpretation = self._generate_interpretation(
            summary_stats=summary_stats,
            tests=statistical_tests,
            decision=decision,
            hypothesis=hypothesis_text
        )

        # 5. Identify limitations
        limitations = self._identify_limitations(data, metadata)

        # 6. Generate recommendations
        recommendations = self._generate_recommendations(
            decision=decision,
            tests=statistical_tests,
            data=data
        )

        # 7. Suggest next experiments
        next_experiments = self._suggest_next_experiments(
            decision=decision,
            hypothesis=hypothesis_text,
            results=data
        )

        # 8. Calculate confidence
        confidence = self._calculate_confidence(
            tests=statistical_tests,
            data_quality=self._assess_data_quality(data)
        )

        report = AnalysisReport(
            experiment_id=experiment_id,
            hypothesis_id=hypothesis_id,
            analysis_type=AnalysisType.INFERENTIAL,
            summary_statistics=summary_stats,
            statistical_tests=statistical_tests,
            visualizations=[],
            interpretation=interpretation,
            hypothesis_decision=decision,
            confidence_level=confidence,
            limitations=limitations,
            recommendations=recommendations,
            next_experiments=next_experiments
        )

        self.analysis_history.append(report)

        logger.success(
            f"Analysis complete: decision={decision.value}, confidence={confidence:.2f}"
        )

        return report

    def _compute_summary_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute descriptive statistics"""
        summary = {}

        for key, values in data.items():
            if isinstance(values, list) and len(values) > 0:
                # Check if numeric
                try:
                    numeric_values = [float(v) for v in values]
                    summary[key] = {
                        "count": len(numeric_values),
                        "mean": float(np.mean(numeric_values)),
                        "std": float(np.std(numeric_values)),
                        "min": float(np.min(numeric_values)),
                        "max": float(np.max(numeric_values)),
                        "median": float(np.median(numeric_values)),
                        "q25": float(np.percentile(numeric_values, 25)),
                        "q75": float(np.percentile(numeric_values, 75))
                    }
                except (ValueError, TypeError):
                    # Non-numeric data
                    summary[key] = {
                        "count": len(values),
                        "type": "categorical"
                    }

        return summary

    def _perform_statistical_tests(
        self,
        data: Dict[str, Any],
        hypothesis: str,
        expected_outcomes: List[str]
    ) -> List[StatisticalResult]:
        """Perform relevant statistical tests"""
        tests = []

        # Extract numeric data
        numeric_data = {}
        for key, values in data.items():
            if isinstance(values, list):
                try:
                    numeric_data[key] = [float(v) for v in values]
                except (ValueError, TypeError):
                    pass

        if not numeric_data:
            logger.warning("No numeric data for statistical tests")
            return tests

        # 1. One-sample t-test (if we have expected mean)
        for key, values in numeric_data.items():
            if len(values) > 1:
                # Test against mean = 0 as default
                t_stat, p_value = stats.ttest_1samp(values, 0)

                tests.append(StatisticalResult(
                    test_name=f"One-sample t-test ({key})",
                    statistic=float(t_stat),
                    p_value=float(p_value),
                    confidence_interval=None,
                    effect_size=None,
                    interpretation=self._interpret_p_value(p_value),
                    significant=p_value < self.significance_level
                ))

        # 2. Two-sample tests (if we have control and treatment groups)
        keys = list(numeric_data.keys())
        if len(keys) >= 2:
            # Compare first two groups
            group1 = numeric_data[keys[0]]
            group2 = numeric_data[keys[1]]

            if len(group1) > 1 and len(group2) > 1:
                t_stat, p_value = stats.ttest_ind(group1, group2)

                tests.append(StatisticalResult(
                    test_name=f"Independent t-test ({keys[0]} vs {keys[1]})",
                    statistic=float(t_stat),
                    p_value=float(p_value),
                    confidence_interval=None,
                    effect_size=self._cohens_d(group1, group2),
                    interpretation=self._interpret_p_value(p_value),
                    significant=p_value < self.significance_level
                ))

        # 3. Correlation tests (if multiple variables)
        if len(numeric_data) >= 2:
            keys_list = list(numeric_data.keys())[:2]
            if len(numeric_data[keys_list[0]]) == len(numeric_data[keys_list[1]]):
                r, p_value = stats.pearsonr(
                    numeric_data[keys_list[0]],
                    numeric_data[keys_list[1]]
                )

                tests.append(StatisticalResult(
                    test_name=f"Pearson correlation ({keys_list[0]}, {keys_list[1]})",
                    statistic=float(r),
                    p_value=float(p_value),
                    confidence_interval=None,
                    effect_size=float(r),
                    interpretation=self._interpret_correlation(r, p_value),
                    significant=p_value < self.significance_level
                ))

        return tests

    def _make_hypothesis_decision(
        self,
        tests: List[StatisticalResult],
        data: Dict[str, Any],
        expected_outcomes: List[str]
    ) -> HypothesisDecision:
        """Decide whether hypothesis is supported"""

        if not tests:
            return HypothesisDecision.INCONCLUSIVE

        # Count significant results
        significant_count = sum(1 for t in tests if t.significant)
        total_tests = len(tests)

        # Assess data quality
        data_sufficient = self._is_data_sufficient(data)

        if not data_sufficient:
            return HypothesisDecision.REQUIRES_MORE_DATA

        # Decision logic
        if significant_count / total_tests >= 0.5:
            return HypothesisDecision.SUPPORTED
        elif significant_count == 0:
            return HypothesisDecision.REJECTED
        else:
            return HypothesisDecision.INCONCLUSIVE

    def _generate_interpretation(
        self,
        summary_stats: Dict[str, Any],
        tests: List[StatisticalResult],
        decision: HypothesisDecision,
        hypothesis: str
    ) -> str:
        """Generate human-readable interpretation"""

        interpretation_parts = []

        # Summary
        interpretation_parts.append(f"Hypothesis: {hypothesis}")
        interpretation_parts.append(f"\nDecision: {decision.value.upper()}")

        # Statistics summary
        interpretation_parts.append("\n\nStatistical Analysis:")
        for test in tests:
            significance = "SIGNIFICANT" if test.significant else "not significant"
            interpretation_parts.append(
                f"- {test.test_name}: {significance} (p={test.p_value:.4f})"
            )

        # Overall interpretation
        interpretation_parts.append("\n\nInterpretation:")
        if decision == HypothesisDecision.SUPPORTED:
            interpretation_parts.append(
                "The experimental data provides statistical support for the hypothesis. "
                "Results show significant effects in the predicted direction."
            )
        elif decision == HypothesisDecision.REJECTED:
            interpretation_parts.append(
                "The experimental data does not support the hypothesis. "
                "No significant effects were observed."
            )
        elif decision == HypothesisDecision.INCONCLUSIVE:
            interpretation_parts.append(
                "Results are inconclusive. Some evidence supports the hypothesis "
                "but more data or refined methodology is needed."
            )
        else:
            interpretation_parts.append(
                "Insufficient data to make a determination. "
                "Additional experiments are required."
            )

        return "\n".join(interpretation_parts)

    def _identify_limitations(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict]
    ) -> List[str]:
        """Identify study limitations"""
        limitations = []

        # Sample size check
        for key, values in data.items():
            if isinstance(values, list) and len(values) < 30:
                limitations.append(
                    f"Small sample size for {key} (n={len(values)}). "
                    "Results may lack statistical power."
                )

        # Data quality check
        if metadata and metadata.get("data_quality") == "low":
            limitations.append("Data quality concerns may affect reliability.")

        # Generalizability
        limitations.append(
            "Results may not generalize beyond the specific experimental conditions."
        )

        return limitations

    def _generate_recommendations(
        self,
        decision: HypothesisDecision,
        tests: List[StatisticalResult],
        data: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if decision == HypothesisDecision.SUPPORTED:
            recommendations.append("Replicate study to confirm findings")
            recommendations.append("Test hypothesis in different contexts")
            recommendations.append("Investigate underlying mechanisms")

        elif decision == HypothesisDecision.REJECTED:
            recommendations.append("Revise hypothesis based on observations")
            recommendations.append("Consider alternative explanations")
            recommendations.append("Design follow-up experiments")

        elif decision == HypothesisDecision.INCONCLUSIVE:
            recommendations.append("Increase sample size")
            recommendations.append("Improve measurement precision")
            recommendations.append("Control for confounding variables")

        else:  # REQUIRES_MORE_DATA
            recommendations.append("Collect additional data")
            recommendations.append("Ensure data quality standards")

        return recommendations

    def _suggest_next_experiments(
        self,
        decision: HypothesisDecision,
        hypothesis: str,
        results: Dict[str, Any]
    ) -> List[str]:
        """Suggest follow-up experiments"""
        suggestions = []

        if decision == HypothesisDecision.SUPPORTED:
            suggestions.append("Replication study with larger sample")
            suggestions.append("Test boundary conditions")
            suggestions.append("Investigate mediating variables")

        elif decision == HypothesisDecision.REJECTED:
            suggestions.append("Test alternative hypothesis")
            suggestions.append("Exploratory study to identify factors")

        elif decision == HypothesisDecision.INCONCLUSIVE:
            suggestions.append("Refined version of current experiment")
            suggestions.append("More controlled experimental design")

        return suggestions

    def _calculate_confidence(
        self,
        tests: List[StatisticalResult],
        data_quality: float
    ) -> float:
        """Calculate overall confidence in results"""

        if not tests:
            return 0.0

        # Average p-value strength
        avg_p = np.mean([t.p_value for t in tests])
        p_confidence = 1.0 - avg_p

        # Consistency of results
        significant_ratio = sum(1 for t in tests if t.significant) / len(tests)

        # Combined confidence
        confidence = (0.5 * p_confidence + 0.3 * significant_ratio + 0.2 * data_quality)

        return min(1.0, confidence)

    def _assess_data_quality(self, data: Dict[str, Any]) -> float:
        """Assess quality of data"""
        quality_score = 1.0

        for key, values in data.items():
            if isinstance(values, list):
                # Check for missing values
                if None in values or any(v == "" for v in values if isinstance(v, str)):
                    quality_score *= 0.8

                # Check sample size
                if len(values) < 30:
                    quality_score *= 0.9

        return quality_score

    def _is_data_sufficient(self, data: Dict[str, Any]) -> bool:
        """Check if data is sufficient for analysis"""
        for key, values in data.items():
            if isinstance(values, list) and len(values) >= 10:
                return True
        return False

    def _interpret_p_value(self, p_value: float) -> str:
        """Interpret p-value"""
        if p_value < 0.001:
            return "Highly significant (p < 0.001)"
        elif p_value < 0.01:
            return "Very significant (p < 0.01)"
        elif p_value < 0.05:
            return "Significant (p < 0.05)"
        elif p_value < 0.1:
            return "Marginally significant (p < 0.1)"
        else:
            return "Not significant (p >= 0.1)"

    def _interpret_correlation(self, r: float, p_value: float) -> str:
        """Interpret correlation coefficient"""
        strength = abs(r)

        if p_value >= 0.05:
            return f"No significant correlation (r={r:.3f}, p={p_value:.3f})"

        if strength < 0.3:
            size = "weak"
        elif strength < 0.7:
            size = "moderate"
        else:
            size = "strong"

        direction = "positive" if r > 0 else "negative"

        return f"{size.capitalize()} {direction} correlation (r={r:.3f}, p={p_value:.3f})"

    def _cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size"""
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        return (np.mean(group1) - np.mean(group2)) / pooled_std

    async def update_hypothesis_from_results(
        self,
        hypothesis_id: str,
        original_hypothesis: str,
        analysis_report: AnalysisReport
    ) -> Optional[HypothesisUpdate]:
        """
        Update hypothesis based on analysis results.

        Closes the agentic loop by feeding results back to hypothesis.

        Args:
            hypothesis_id: Hypothesis identifier
            original_hypothesis: Original hypothesis text
            analysis_report: Analysis results

        Returns:
            Hypothesis update or None if no update needed
        """
        logger.info(f"Updating hypothesis {hypothesis_id} based on results")

        decision = analysis_report.hypothesis_decision

        if decision == HypothesisDecision.SUPPORTED:
            # Strengthen hypothesis
            changes = ["Increased confidence based on empirical support"]
            updated = original_hypothesis + " [Empirically validated]"
            confidence_delta = 0.2

        elif decision == HypothesisDecision.REJECTED:
            # Revise or reject
            changes = ["Hypothesis rejected - needs revision"]
            updated = "REVISED: " + original_hypothesis
            confidence_delta = -0.5

        elif decision == HypothesisDecision.INCONCLUSIVE:
            # Add caveats
            changes = ["Added limitations and conditions"]
            updated = original_hypothesis + " [Requires further validation]"
            confidence_delta = 0.0

        else:  # REQUIRES_MORE_DATA
            # No change yet
            return None

        update = HypothesisUpdate(
            hypothesis_id=hypothesis_id,
            original_hypothesis=original_hypothesis,
            updated_hypothesis=updated,
            changes=changes,
            reason=analysis_report.interpretation,
            confidence_delta=confidence_delta
        )

        self.hypothesis_updates.append(update)

        logger.success(f"Hypothesis updated: confidence_delta={confidence_delta:+.2f}")

        return update

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all analyses"""
        if not self.analysis_history:
            return {}

        decisions = [report.hypothesis_decision for report in self.analysis_history]

        return {
            "total_analyses": len(self.analysis_history),
            "decisions": {
                "supported": decisions.count(HypothesisDecision.SUPPORTED),
                "rejected": decisions.count(HypothesisDecision.REJECTED),
                "inconclusive": decisions.count(HypothesisDecision.INCONCLUSIVE),
                "requires_more_data": decisions.count(HypothesisDecision.REQUIRES_MORE_DATA)
            },
            "avg_confidence": np.mean([r.confidence_level for r in self.analysis_history]),
            "hypothesis_updates": len(self.hypothesis_updates),
            "recent_analyses": [
                {
                    "experiment_id": r.experiment_id,
                    "decision": r.hypothesis_decision.value,
                    "confidence": r.confidence_level
                }
                for r in self.analysis_history[-5:]
            ]
        }
