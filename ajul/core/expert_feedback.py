"""
Expert Feedback Interface Module

Enables human-in-the-loop review and feedback for agent predictions.

Key capabilities:
- Present agent predictions/hypotheses to experts
- Collect structured feedback (ratings, corrections, comments)
- Track review history and expert consensus
- Integrate feedback into agent learning
- Support asynchronous review workflows
- Enable active learning (request feedback on uncertain items)

Inspired by LangGraph HITL, RLHF, and interactive ML approaches.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
from collections import defaultdict

from loguru import logger


class ReviewStatus(str, Enum):
    """Status of expert review"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    UNCERTAIN = "uncertain"


class FeedbackType(str, Enum):
    """Types of feedback"""
    RATING = "rating"  # Numeric rating
    CORRECTION = "correction"  # Suggested corrections
    COMMENT = "comment"  # Textual feedback
    VALIDATION = "validation"  # Validation of results
    PRIORITY = "priority"  # Priority/importance rating


class PredictionConfidence(str, Enum):
    """Agent confidence in predictions"""
    HIGH = "high"  # >0.8
    MEDIUM = "medium"  # 0.5-0.8
    LOW = "low"  # <0.5
    UNCERTAIN = "uncertain"  # Needs expert input


@dataclass
class Prediction:
    """Agent prediction requiring review"""
    id: str
    type: str  # hypothesis, experiment_design, result_analysis, etc.
    content: str
    structured_data: Dict[str, Any]
    confidence: float  # 0-1
    confidence_level: PredictionConfidence
    evidence: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpertFeedback:
    """Feedback from expert reviewer"""
    id: str
    prediction_id: str
    expert_id: str
    expert_name: str
    status: ReviewStatus
    rating: Optional[float] = None  # 0-1 or 1-5
    corrections: Dict[str, Any] = field(default_factory=dict)
    comments: str = ""
    confidence_in_feedback: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    review_duration_seconds: float = 0.0


@dataclass
class ReviewRequest:
    """Request for expert review"""
    id: str
    prediction: Prediction
    assigned_to: List[str]  # Expert IDs
    priority: int  # 1-5, higher = more urgent
    context: str
    questions: List[str]  # Specific questions for experts
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackSummary:
    """Aggregated feedback summary"""
    prediction_id: str
    total_reviews: int
    avg_rating: float
    consensus_status: ReviewStatus
    common_corrections: List[Dict[str, Any]]
    expert_agreement: float  # 0-1, how much experts agree
    recommendation: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExpertProfile:
    """Expert reviewer profile"""
    id: str
    name: str
    expertise_domains: List[str]
    review_count: int = 0
    avg_review_quality: float = 0.0  # Measured by consistency
    specializations: List[str] = field(default_factory=list)


class ExpertFeedbackEngine:
    """
    Engine for human-in-the-loop expert feedback.

    Workflow:
    1. Agent creates prediction
    2. System determines if expert review needed
    3. Create review request and assign to experts
    4. Experts provide feedback asynchronously
    5. Aggregate feedback into summary
    6. Integrate feedback into agent learning
    7. Track feedback quality and expert performance
    """

    def __init__(
        self,
        auto_request_threshold: float = 0.7,  # Request review if confidence < threshold
        min_reviewers: int = 2,
        enable_active_learning: bool = True
    ):
        self.auto_request_threshold = auto_request_threshold
        self.min_reviewers = min_reviewers
        self.enable_active_learning = enable_active_learning

        # Storage
        self.predictions: Dict[str, Prediction] = {}
        self.review_requests: Dict[str, ReviewRequest] = {}
        self.feedbacks: Dict[str, List[ExpertFeedback]] = defaultdict(list)
        self.experts: Dict[str, ExpertProfile] = {}
        self.summaries: Dict[str, FeedbackSummary] = {}

        # Metrics
        self.metrics = {
            "total_predictions": 0,
            "predictions_reviewed": 0,
            "avg_review_time": 0.0,
            "approval_rate": 0.0
        }

        logger.info("Expert feedback engine initialized")

    def register_expert(
        self,
        expert_id: str,
        name: str,
        expertise_domains: List[str],
        specializations: Optional[List[str]] = None
    ) -> ExpertProfile:
        """
        Register an expert reviewer.

        Args:
            expert_id: Unique identifier
            name: Expert name
            expertise_domains: Areas of expertise
            specializations: Specific specializations

        Returns:
            Expert profile
        """
        logger.info(f"Registering expert: {name}")

        expert = ExpertProfile(
            id=expert_id,
            name=name,
            expertise_domains=expertise_domains,
            specializations=specializations or []
        )

        self.experts[expert_id] = expert

        logger.success(f"Expert registered: {name}")
        return expert

    def submit_prediction_for_review(
        self,
        prediction: Prediction,
        force_review: bool = False,
        assigned_experts: Optional[List[str]] = None,
        priority: int = 3,
        context: str = "",
        questions: Optional[List[str]] = None
    ) -> Optional[ReviewRequest]:
        """
        Submit prediction for expert review.

        Args:
            prediction: Prediction to review
            force_review: Force review regardless of confidence
            assigned_experts: Specific experts to assign
            priority: Review priority 1-5
            context: Additional context for reviewers
            questions: Specific questions

        Returns:
            Review request if created, None if review not needed
        """
        logger.info(f"Submitting prediction for review: {prediction.id}")

        self.predictions[prediction.id] = prediction
        self.metrics["total_predictions"] += 1

        # Determine if review needed
        needs_review = force_review or (
            self.enable_active_learning and
            prediction.confidence < self.auto_request_threshold
        )

        if not needs_review:
            logger.info("Review not needed (high confidence)")
            return None

        # Select experts
        if not assigned_experts:
            assigned_experts = self._select_experts(prediction)

        # Create review request
        request_id = self._generate_id(prediction.id + str(datetime.now()))

        request = ReviewRequest(
            id=request_id,
            prediction=prediction,
            assigned_to=assigned_experts,
            priority=priority,
            context=context,
            questions=questions or self._generate_review_questions(prediction)
        )

        self.review_requests[request_id] = request

        logger.success(
            f"Review request created: {request_id}, "
            f"assigned to {len(assigned_experts)} experts"
        )

        return request

    def get_pending_reviews(
        self,
        expert_id: Optional[str] = None,
        priority_threshold: int = 0
    ) -> List[ReviewRequest]:
        """
        Get pending review requests.

        Args:
            expert_id: Filter by expert
            priority_threshold: Minimum priority

        Returns:
            List of pending requests
        """
        pending = []

        for request in self.review_requests.values():
            # Check if already reviewed
            feedbacks = self.feedbacks.get(request.prediction.id, [])
            reviewed_by = {f.expert_id for f in feedbacks}

            # Check if this expert needs to review
            if expert_id:
                if expert_id not in request.assigned_to:
                    continue
                if expert_id in reviewed_by:
                    continue

            # Check priority
            if request.priority < priority_threshold:
                continue

            pending.append(request)

        # Sort by priority
        pending.sort(key=lambda r: r.priority, reverse=True)

        return pending

    def submit_feedback(
        self,
        prediction_id: str,
        expert_id: str,
        status: ReviewStatus,
        rating: Optional[float] = None,
        corrections: Optional[Dict[str, Any]] = None,
        comments: str = "",
        confidence: float = 1.0,
        review_duration: float = 0.0
    ) -> ExpertFeedback:
        """
        Submit expert feedback on prediction.

        Args:
            prediction_id: Prediction being reviewed
            expert_id: Expert providing feedback
            status: Review status
            rating: Numeric rating
            corrections: Suggested corrections
            comments: Textual feedback
            confidence: Expert's confidence in feedback
            review_duration: Time spent reviewing (seconds)

        Returns:
            Feedback record
        """
        logger.info(f"Submitting feedback from {expert_id} on {prediction_id}")

        feedback_id = self._generate_id(f"{prediction_id}_{expert_id}_{datetime.now()}")

        feedback = ExpertFeedback(
            id=feedback_id,
            prediction_id=prediction_id,
            expert_id=expert_id,
            expert_name=self.experts.get(expert_id, ExpertProfile(id=expert_id, name="Unknown", expertise_domains=[])).name,
            status=status,
            rating=rating,
            corrections=corrections or {},
            comments=comments,
            confidence_in_feedback=confidence,
            review_duration_seconds=review_duration
        )

        self.feedbacks[prediction_id].append(feedback)

        # Update expert profile
        if expert_id in self.experts:
            self.experts[expert_id].review_count += 1

        # Update metrics
        self.metrics["predictions_reviewed"] += 1
        self._update_metrics()

        logger.success(f"Feedback submitted: {feedback_id}")

        # Check if enough feedback received
        if len(self.feedbacks[prediction_id]) >= self.min_reviewers:
            self._aggregate_feedback(prediction_id)

        return feedback

    def get_feedback_summary(self, prediction_id: str) -> Optional[FeedbackSummary]:
        """
        Get aggregated feedback summary.

        Args:
            prediction_id: Prediction ID

        Returns:
            Feedback summary if available
        """
        return self.summaries.get(prediction_id)

    def _aggregate_feedback(self, prediction_id: str) -> FeedbackSummary:
        """
        Aggregate feedback from multiple experts.

        Args:
            prediction_id: Prediction ID

        Returns:
            Aggregated summary
        """
        logger.info(f"Aggregating feedback for {prediction_id}")

        feedbacks = self.feedbacks.get(prediction_id, [])

        if not feedbacks:
            raise ValueError(f"No feedback for {prediction_id}")

        # Calculate average rating
        ratings = [f.rating for f in feedbacks if f.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

        # Determine consensus status
        statuses = [f.status for f in feedbacks]
        status_counts = defaultdict(int)
        for status in statuses:
            status_counts[status] += 1

        consensus_status = max(status_counts.items(), key=lambda x: x[1])[0]

        # Calculate expert agreement
        agreement = status_counts[consensus_status] / len(statuses)

        # Collect common corrections
        all_corrections = []
        for f in feedbacks:
            if f.corrections:
                all_corrections.append(f.corrections)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            consensus_status,
            agreement,
            avg_rating,
            feedbacks
        )

        summary = FeedbackSummary(
            prediction_id=prediction_id,
            total_reviews=len(feedbacks),
            avg_rating=avg_rating,
            consensus_status=consensus_status,
            common_corrections=all_corrections,
            expert_agreement=agreement,
            recommendation=recommendation
        )

        self.summaries[prediction_id] = summary

        logger.success(
            f"Feedback aggregated: consensus={consensus_status.value}, "
            f"agreement={agreement:.2f}"
        )

        return summary

    def get_learning_data(self, min_agreement: float = 0.7) -> List[Dict[str, Any]]:
        """
        Get feedback data for agent learning.

        Args:
            min_agreement: Minimum expert agreement threshold

        Returns:
            List of feedback records for learning
        """
        logger.info("Extracting learning data from feedback")

        learning_data = []

        for pred_id, summary in self.summaries.items():
            # Only use high-agreement feedback
            if summary.expert_agreement < min_agreement:
                continue

            prediction = self.predictions.get(pred_id)
            if not prediction:
                continue

            feedbacks = self.feedbacks.get(pred_id, [])

            # Create learning record
            record = {
                "prediction_id": pred_id,
                "original_prediction": {
                    "content": prediction.content,
                    "confidence": prediction.confidence,
                    "structured_data": prediction.structured_data
                },
                "expert_feedback": {
                    "consensus_status": summary.consensus_status.value,
                    "avg_rating": summary.avg_rating,
                    "agreement": summary.expert_agreement,
                    "corrections": summary.common_corrections,
                    "recommendation": summary.recommendation
                },
                "individual_feedbacks": [
                    {
                        "expert_id": f.expert_id,
                        "status": f.status.value,
                        "rating": f.rating,
                        "comments": f.comments
                    }
                    for f in feedbacks
                ],
                "label": summary.consensus_status.value  # For supervised learning
            }

            learning_data.append(record)

        logger.info(f"Extracted {len(learning_data)} learning records")
        return learning_data

    def _select_experts(self, prediction: Prediction) -> List[str]:
        """
        Select appropriate experts for prediction review.

        Args:
            prediction: Prediction to review

        Returns:
            List of expert IDs
        """
        # Simple selection: match expertise domains
        pred_domain = prediction.metadata.get("domain", "general")

        candidates = []
        for expert in self.experts.values():
            if pred_domain in expert.expertise_domains or "general" in expert.expertise_domains:
                candidates.append(expert.id)

        # Select minimum reviewers
        selected = candidates[:self.min_reviewers]

        if not selected:
            # Fallback: select any experts
            selected = list(self.experts.keys())[:self.min_reviewers]

        return selected

    def _generate_review_questions(self, prediction: Prediction) -> List[str]:
        """Generate review questions for experts"""

        base_questions = [
            "Is this prediction scientifically sound?",
            "Are the conclusions supported by the evidence?",
            "What improvements would you suggest?"
        ]

        if prediction.confidence < 0.5:
            base_questions.append("What additional data or analysis is needed?")

        return base_questions

    def _generate_recommendation(
        self,
        consensus: ReviewStatus,
        agreement: float,
        avg_rating: float,
        feedbacks: List[ExpertFeedback]
    ) -> str:
        """Generate actionable recommendation"""

        if consensus == ReviewStatus.APPROVED and agreement > 0.8:
            return "Strong consensus: Approved. Proceed with prediction."

        elif consensus == ReviewStatus.APPROVED:
            return "Approved with moderate agreement. Consider expert comments."

        elif consensus == ReviewStatus.NEEDS_REVISION:
            return "Needs revision. Review expert corrections and resubmit."

        elif consensus == ReviewStatus.REJECTED:
            return "Rejected. Significant concerns raised. Reconsider approach."

        elif consensus == ReviewStatus.UNCERTAIN:
            return "Uncertain. Gather more evidence or seek additional expert input."

        else:
            return "Mixed feedback. Review individual comments for guidance."

    def _generate_id(self, text: str) -> str:
        """Generate unique ID"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _update_metrics(self):
        """Update engine metrics"""

        if not self.feedbacks:
            return

        # Calculate approval rate
        all_feedbacks = [f for feedbacks in self.feedbacks.values() for f in feedbacks]
        approved = sum(1 for f in all_feedbacks if f.status == ReviewStatus.APPROVED)
        self.metrics["approval_rate"] = approved / len(all_feedbacks) if all_feedbacks else 0.0

        # Calculate average review time
        review_times = [f.review_duration_seconds for f in all_feedbacks if f.review_duration_seconds > 0]
        self.metrics["avg_review_time"] = sum(review_times) / len(review_times) if review_times else 0.0

    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""

        return {
            "metrics": self.metrics,
            "experts_registered": len(self.experts),
            "predictions_submitted": len(self.predictions),
            "pending_reviews": len(self.get_pending_reviews()),
            "summaries_created": len(self.summaries),
            "expert_stats": [
                {
                    "expert_id": e.id,
                    "name": e.name,
                    "review_count": e.review_count,
                    "expertise": e.expertise_domains
                }
                for e in self.experts.values()
            ],
            "recent_feedback": [
                {
                    "prediction_id": s.prediction_id,
                    "consensus": s.consensus_status.value,
                    "agreement": s.expert_agreement,
                    "rating": s.avg_rating
                }
                for s in list(self.summaries.values())[-5:]
            ]
        }


class AsyncReviewWorkflow:
    """
    Asynchronous review workflow manager.

    Enables non-blocking review processes where predictions
    can be submitted and reviewed asynchronously.
    """

    def __init__(self, feedback_engine: ExpertFeedbackEngine):
        self.engine = feedback_engine
        self.interrupt_points: Dict[str, Dict[str, Any]] = {}

        logger.info("Async review workflow initialized")

    def create_interrupt(
        self,
        workflow_id: str,
        prediction: Prediction,
        context: Dict[str, Any]
    ) -> str:
        """
        Create workflow interrupt point for human review.

        Inspired by LangGraph's interrupt mechanism.

        Args:
            workflow_id: Workflow identifier
            prediction: Prediction requiring review
            context: Workflow context

        Returns:
            Interrupt ID
        """
        logger.info(f"Creating interrupt for workflow: {workflow_id}")

        interrupt_id = f"{workflow_id}_{prediction.id}"

        self.interrupt_points[interrupt_id] = {
            "workflow_id": workflow_id,
            "prediction": prediction,
            "context": context,
            "status": "waiting",
            "created_at": datetime.now()
        }

        # Submit for review
        self.engine.submit_prediction_for_review(prediction)

        logger.success(f"Interrupt created: {interrupt_id}")
        return interrupt_id

    def check_interrupt_status(self, interrupt_id: str) -> Dict[str, Any]:
        """Check if interrupt can be resumed"""

        interrupt = self.interrupt_points.get(interrupt_id)
        if not interrupt:
            return {"status": "not_found"}

        prediction_id = interrupt["prediction"].id
        summary = self.engine.get_feedback_summary(prediction_id)

        if summary:
            return {
                "status": "ready",
                "feedback": summary,
                "can_resume": True
            }
        else:
            return {
                "status": "waiting",
                "feedback": None,
                "can_resume": False
            }

    def resume_workflow(
        self,
        interrupt_id: str
    ) -> Tuple[bool, Optional[FeedbackSummary]]:
        """
        Resume workflow after human feedback received.

        Returns:
            (can_resume, feedback_summary)
        """
        status = self.check_interrupt_status(interrupt_id)

        if status["status"] == "ready":
            self.interrupt_points[interrupt_id]["status"] = "resumed"
            return True, status["feedback"]
        else:
            return False, None
