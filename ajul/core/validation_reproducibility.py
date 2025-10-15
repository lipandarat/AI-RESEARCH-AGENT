"""
Validation & Reproducibility Module

Ensures experiments are reproducible and results are reliable.

Key features:
- Experiment specification versioning
- Environment capture
- Seed management
- Replication protocols
- Result verification
- Reproducibility scoring
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json
import os
import platform

from loguru import logger


class ReproducibilityStatus(str, Enum):
    """Reproducibility validation status"""
    FULLY_REPRODUCIBLE = "fully_reproducible"
    PARTIALLY_REPRODUCIBLE = "partially_reproducible"
    NOT_REPRODUCIBLE = "not_reproducible"
    UNTESTED = "untested"


@dataclass
class ExperimentEnvironment:
    """Complete environment specification"""
    python_version: str
    platform: str
    dependencies: Dict[str, str]
    hardware: Dict[str, Any]
    random_seed: Optional[int]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExperimentCheckpoint:
    """Versioned experiment specification"""
    checkpoint_id: str
    experiment_id: str
    version: int
    specification: Dict[str, Any]
    code_hash: str
    data_hash: Optional[str]
    environment: ExperimentEnvironment
    parameters: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReplicationResult:
    """Results from replication attempt"""
    original_experiment_id: str
    replication_id: str
    original_results: Dict[str, Any]
    replicated_results: Dict[str, Any]
    reproducibility_score: float  # 0-1
    status: ReproducibilityStatus
    differences: List[str]
    environment_match: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationReport:
    """Complete validation report"""
    experiment_id: str
    checkpoint_id: str
    replication_attempts: int
    successful_replications: int
    reproducibility_score: float
    status: ReproducibilityStatus
    validation_checks: Dict[str, bool]
    issues_found: List[str]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class ValidationReproducibilityEngine:
    """
    Engine for ensuring experiment reproducibility.

    Workflow:
    1. Capture complete experiment specification
    2. Version code and data
    3. Record environment
    4. Generate reproducibility protocol
    5. Facilitate replication
    6. Verify results consistency
    7. Score reproducibility
    """

    def __init__(
        self,
        checkpoint_dir: str = "./checkpoints",
        tolerance: float = 0.01  # Acceptable result variation
    ):
        self.checkpoint_dir = checkpoint_dir
        self.tolerance = tolerance

        # Storage
        self.checkpoints: Dict[str, ExperimentCheckpoint] = {}
        self.replications: List[ReplicationResult] = []
        self.validation_reports: List[ValidationReport] = []

        os.makedirs(checkpoint_dir, exist_ok=True)

        logger.info("Validation & reproducibility engine initialized")

    def create_experiment_checkpoint(
        self,
        experiment_id: str,
        specification: Dict[str, Any],
        code: str,
        parameters: Dict[str, Any],
        data_info: Optional[Dict] = None,
        random_seed: Optional[int] = None
    ) -> ExperimentCheckpoint:
        """
        Create versioned checkpoint of experiment.

        Args:
            experiment_id: Experiment identifier
            specification: Complete experiment spec
            code: Experiment code
            parameters: All parameters used
            data_info: Information about data
            random_seed: Random seed if used

        Returns:
            Experiment checkpoint
        """
        logger.info(f"Creating checkpoint for experiment {experiment_id}")

        # Capture environment
        environment = self._capture_environment(random_seed)

        # Hash code for versioning
        code_hash = self._hash_string(code)

        # Hash data if available
        data_hash = None
        if data_info:
            data_hash = self._hash_dict(data_info)

        # Generate checkpoint ID
        checkpoint_id = self._generate_checkpoint_id(experiment_id)

        # Determine version
        existing_versions = [
            cp.version for cp in self.checkpoints.values()
            if cp.experiment_id == experiment_id
        ]
        version = max(existing_versions, default=0) + 1

        checkpoint = ExperimentCheckpoint(
            checkpoint_id=checkpoint_id,
            experiment_id=experiment_id,
            version=version,
            specification=specification,
            code_hash=code_hash,
            data_hash=data_hash,
            environment=environment,
            parameters=parameters
        )

        # Store
        self.checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint_to_disk(checkpoint)

        logger.success(f"Checkpoint created: {checkpoint_id} (v{version})")

        return checkpoint

    def generate_replication_protocol(
        self,
        checkpoint: ExperimentCheckpoint
    ) -> Dict[str, Any]:
        """
        Generate step-by-step replication protocol.

        Args:
            checkpoint: Experiment checkpoint

        Returns:
            Replication protocol
        """
        logger.info(f"Generating replication protocol for {checkpoint.checkpoint_id}")

        protocol = {
            "experiment_id": checkpoint.experiment_id,
            "checkpoint_id": checkpoint.checkpoint_id,
            "version": checkpoint.version,
            "title": checkpoint.specification.get("title", "Experiment"),

            "environment_setup": {
                "python_version": checkpoint.environment.python_version,
                "platform": checkpoint.environment.platform,
                "dependencies": checkpoint.environment.dependencies,
                "installation_command": self._generate_install_command(
                    checkpoint.environment.dependencies
                )
            },

            "random_seed": {
                "required": checkpoint.environment.random_seed is not None,
                "seed_value": checkpoint.environment.random_seed,
                "instructions": "Set random seed before running experiment"
            },

            "parameters": checkpoint.parameters,

            "data_requirements": {
                "data_hash": checkpoint.data_hash,
                "note": "Use exact same data as original experiment"
            },

            "execution_steps": [
                "1. Set up environment with specified dependencies",
                "2. Set random seed if applicable",
                "3. Load data matching data_hash",
                "4. Set parameters exactly as specified",
                "5. Run experiment code",
                "6. Record all outputs",
                "7. Compare results with original"
            ],

            "validation": {
                "code_hash": checkpoint.code_hash,
                "tolerance": self.tolerance,
                "note": "Results should match within tolerance"
            },

            "contact": {
                "checkpoint_file": f"{self.checkpoint_dir}/{checkpoint.checkpoint_id}.json"
            }
        }

        logger.success("Replication protocol generated")

        return protocol

    async def replicate_experiment(
        self,
        checkpoint: ExperimentCheckpoint,
        new_results: Dict[str, Any],
        original_results: Dict[str, Any]
    ) -> ReplicationResult:
        """
        Attempt to replicate experiment and validate results.

        Args:
            checkpoint: Original experiment checkpoint
            new_results: Results from replication attempt
            original_results: Original experiment results

        Returns:
            Replication result with reproducibility score
        """
        logger.info(f"Replicating experiment {checkpoint.experiment_id}")

        replication_id = self._generate_replication_id()

        # Check environment match
        current_env = self._capture_environment()
        env_match = self._compare_environments(
            checkpoint.environment,
            current_env
        )

        # Compare results
        differences = self._compare_results(
            original_results,
            new_results
        )

        # Calculate reproducibility score
        score = self._calculate_reproducibility_score(
            original_results,
            new_results,
            differences
        )

        # Determine status
        status = self._determine_reproducibility_status(score)

        result = ReplicationResult(
            original_experiment_id=checkpoint.experiment_id,
            replication_id=replication_id,
            original_results=original_results,
            replicated_results=new_results,
            reproducibility_score=score,
            status=status,
            differences=differences,
            environment_match=env_match
        )

        self.replications.append(result)

        logger.success(
            f"Replication complete: score={score:.2f}, status={status.value}"
        )

        return result

    def validate_experiment_reproducibility(
        self,
        experiment_id: str,
        checkpoint_id: str
    ) -> ValidationReport:
        """
        Comprehensive validation of experiment reproducibility.

        Args:
            experiment_id: Experiment to validate
            checkpoint_id: Checkpoint to validate against

        Returns:
            Validation report
        """
        logger.info(f"Validating reproducibility for {experiment_id}")

        checkpoint = self.checkpoints.get(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        # Count replication attempts
        replications = [
            r for r in self.replications
            if r.original_experiment_id == experiment_id
        ]

        successful = [
            r for r in replications
            if r.status == ReproducibilityStatus.FULLY_REPRODUCIBLE
        ]

        # Run validation checks
        validation_checks = {
            "checkpoint_exists": checkpoint is not None,
            "code_versioned": checkpoint.code_hash is not None,
            "environment_captured": checkpoint.environment is not None,
            "parameters_recorded": len(checkpoint.parameters) > 0,
            "replications_attempted": len(replications) > 0,
            "replications_successful": len(successful) > 0
        }

        # Calculate overall reproducibility score
        if replications:
            avg_score = sum(r.reproducibility_score for r in replications) / len(replications)
        else:
            avg_score = 0.0

        # Determine status
        if len(successful) == len(replications) and len(replications) > 0:
            status = ReproducibilityStatus.FULLY_REPRODUCIBLE
        elif len(successful) > 0:
            status = ReproducibilityStatus.PARTIALLY_REPRODUCIBLE
        elif len(replications) > 0:
            status = ReproducibilityStatus.NOT_REPRODUCIBLE
        else:
            status = ReproducibilityStatus.UNTESTED

        # Identify issues
        issues = []
        if not validation_checks["replications_attempted"]:
            issues.append("No replication attempts yet")
        if not validation_checks["code_versioned"]:
            issues.append("Code not properly versioned")
        if avg_score < 0.5:
            issues.append("Low reproducibility score")

        # Generate recommendations
        recommendations = []
        if status != ReproducibilityStatus.FULLY_REPRODUCIBLE:
            recommendations.append("Perform additional replication attempts")
        if not validation_checks["parameters_recorded"]:
            recommendations.append("Record all experiment parameters")
        if avg_score < 0.8:
            recommendations.append("Improve experimental controls")

        report = ValidationReport(
            experiment_id=experiment_id,
            checkpoint_id=checkpoint_id,
            replication_attempts=len(replications),
            successful_replications=len(successful),
            reproducibility_score=avg_score,
            status=status,
            validation_checks=validation_checks,
            issues_found=issues,
            recommendations=recommendations
        )

        self.validation_reports.append(report)

        logger.success(
            f"Validation complete: {len(successful)}/{len(replications)} successful"
        )

        return report

    def _capture_environment(
        self,
        random_seed: Optional[int] = None
    ) -> ExperimentEnvironment:
        """Capture current environment"""
        import sys

        # Get installed packages
        dependencies = {}
        try:
            import pkg_resources
            for package in pkg_resources.working_set:
                dependencies[package.project_name] = package.version
        except:
            pass

        # Hardware info (basic)
        hardware = {
            "processor": platform.processor(),
            "machine": platform.machine()
        }

        return ExperimentEnvironment(
            python_version=sys.version,
            platform=platform.platform(),
            dependencies=dependencies,
            hardware=hardware,
            random_seed=random_seed
        )

    def _compare_environments(
        self,
        env1: ExperimentEnvironment,
        env2: ExperimentEnvironment
    ) -> bool:
        """Check if environments match"""
        # Check Python version
        if env1.python_version != env2.python_version:
            logger.warning("Python version mismatch")
            return False

        # Check platform
        if env1.platform != env2.platform:
            logger.warning("Platform mismatch")
            return False

        # Check key dependencies
        key_packages = ["numpy", "scipy", "pandas"]
        for pkg in key_packages:
            if pkg in env1.dependencies and pkg in env2.dependencies:
                if env1.dependencies[pkg] != env2.dependencies[pkg]:
                    logger.warning(f"Dependency version mismatch: {pkg}")
                    return False

        return True

    def _compare_results(
        self,
        original: Dict[str, Any],
        replicated: Dict[str, Any]
    ) -> List[str]:
        """Compare results and identify differences"""
        differences = []

        # Check keys match
        original_keys = set(original.keys())
        replicated_keys = set(replicated.keys())

        if original_keys != replicated_keys:
            differences.append(f"Key mismatch: {original_keys ^ replicated_keys}")

        # Compare values
        for key in original_keys & replicated_keys:
            orig_val = original[key]
            repl_val = replicated[key]

            if isinstance(orig_val, (int, float)) and isinstance(repl_val, (int, float)):
                # Numeric comparison with tolerance
                if abs(orig_val - repl_val) > self.tolerance:
                    differences.append(
                        f"{key}: {orig_val} vs {repl_val} "
                        f"(diff={abs(orig_val - repl_val):.6f})"
                    )
            elif orig_val != repl_val:
                differences.append(f"{key}: {orig_val} vs {repl_val}")

        return differences

    def _calculate_reproducibility_score(
        self,
        original: Dict[str, Any],
        replicated: Dict[str, Any],
        differences: List[str]
    ) -> float:
        """Calculate reproducibility score"""
        if not original:
            return 0.0

        total_keys = len(original)
        matching_keys = total_keys - len(differences)

        # Base score from key matches
        base_score = matching_keys / total_keys if total_keys > 0 else 0.0

        # Penalty for large differences
        penalty = min(0.3, len(differences) * 0.1)

        return max(0.0, base_score - penalty)

    def _determine_reproducibility_status(
        self,
        score: float
    ) -> ReproducibilityStatus:
        """Determine status from score"""
        if score >= 0.95:
            return ReproducibilityStatus.FULLY_REPRODUCIBLE
        elif score >= 0.7:
            return ReproducibilityStatus.PARTIALLY_REPRODUCIBLE
        else:
            return ReproducibilityStatus.NOT_REPRODUCIBLE

    def _hash_string(self, text: str) -> str:
        """Hash string for versioning"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _hash_dict(self, data: Dict) -> str:
        """Hash dictionary"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    def _generate_checkpoint_id(self, experiment_id: str) -> str:
        """Generate checkpoint ID"""
        timestamp = datetime.now().isoformat()
        combined = f"{experiment_id}_{timestamp}"
        return self._hash_string(combined)

    def _generate_replication_id(self) -> str:
        """Generate replication ID"""
        timestamp = datetime.now().isoformat()
        return self._hash_string(timestamp)

    def _generate_install_command(self, dependencies: Dict[str, str]) -> str:
        """Generate pip install command"""
        packages = [f"{name}=={version}" for name, version in dependencies.items()]
        return f"pip install {' '.join(packages[:5])}..."  # Truncate for display

    def _save_checkpoint_to_disk(self, checkpoint: ExperimentCheckpoint):
        """Save checkpoint to file"""
        filepath = os.path.join(
            self.checkpoint_dir,
            f"{checkpoint.checkpoint_id}.json"
        )

        data = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "experiment_id": checkpoint.experiment_id,
            "version": checkpoint.version,
            "specification": checkpoint.specification,
            "code_hash": checkpoint.code_hash,
            "data_hash": checkpoint.data_hash,
            "parameters": checkpoint.parameters,
            "environment": {
                "python_version": checkpoint.environment.python_version,
                "platform": checkpoint.environment.platform,
                "random_seed": checkpoint.environment.random_seed
            },
            "created_at": checkpoint.created_at.isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Checkpoint saved to {filepath}")

    def get_reproducibility_summary(self) -> Dict[str, Any]:
        """Get summary of all reproducibility efforts"""
        return {
            "total_checkpoints": len(self.checkpoints),
            "total_replications": len(self.replications),
            "successful_replications": len([
                r for r in self.replications
                if r.status == ReproducibilityStatus.FULLY_REPRODUCIBLE
            ]),
            "avg_reproducibility_score": (
                sum(r.reproducibility_score for r in self.replications) / len(self.replications)
                if self.replications else 0.0
            ),
            "validation_reports": len(self.validation_reports),
            "recent_replications": [
                {
                    "experiment_id": r.original_experiment_id,
                    "score": r.reproducibility_score,
                    "status": r.status.value
                }
                for r in self.replications[-5:]
            ]
        }
