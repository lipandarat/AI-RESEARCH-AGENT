"""
Evolution & Optimization Module

Enables the research agent to:
- Learn from performance feedback
- Evolve strategies over time
- Optimize prediction algorithms
- Adapt to new domains
- Self-improve through experience

Implements genetic algorithms and adaptive learning.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import json
import copy

import numpy as np
from loguru import logger


class OptimizationStrategy(str, Enum):
    """Optimization strategies"""
    GENETIC_ALGORITHM = "genetic_algorithm"
    GRADIENT_DESCENT = "gradient_descent"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    EVOLUTIONARY_STRATEGY = "evolutionary_strategy"


@dataclass
class PerformanceMetrics:
    """Performance metrics for evaluation"""
    accuracy: float  # 0-1
    precision: float  # 0-1
    recall: float  # 0-1
    novelty_score: float  # How novel are predictions
    success_rate: float  # Experiment success rate
    efficiency: float  # Resource efficiency
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Strategy:
    """Research strategy configuration"""
    id: str
    name: str
    parameters: Dict[str, Any]
    performance_history: List[PerformanceMetrics] = field(default_factory=list)
    generation: int = 0
    fitness_score: float = 0.0
    parent_ids: List[str] = field(default_factory=list)


@dataclass
class EvolutionConfig:
    """Configuration for evolutionary optimization"""
    population_size: int = 20
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    selection_pressure: float = 0.3  # Top % to keep
    max_generations: int = 100
    fitness_threshold: float = 0.9
    diversity_weight: float = 0.2


class EvolutionaryOptimizer:
    """
    Evolutionary optimizer for research strategies.

    Evolves agent behavior through:
    - Strategy population management
    - Fitness evaluation
    - Selection, crossover, mutation
    - Performance tracking
    - Adaptive parameter tuning
    """

    def __init__(
        self,
        config: Optional[EvolutionConfig] = None
    ):
        self.config = config or EvolutionConfig()

        # Strategy population
        self.population: List[Strategy] = []
        self.generation_counter = 0

        # Performance tracking
        self.best_strategies: List[Strategy] = []
        self.evolution_history: List[Dict] = []

        # Parameter search space
        self.parameter_space = self._define_parameter_space()

        logger.info("Evolutionary optimizer initialized")

    def _define_parameter_space(self) -> Dict[str, Dict]:
        """
        Define searchable parameter space for strategies.

        These parameters control hypothesis generation,
        experiment design, and analysis behavior.
        """
        return {
            # Hypothesis generation parameters
            "hypothesis_creativity": {
                "type": "continuous",
                "min": 0.0,
                "max": 1.0,
                "description": "Balance between novel and safe hypotheses"
            },
            "hypothesis_complexity": {
                "type": "discrete",
                "values": ["simple", "moderate", "complex"],
                "description": "Complexity level of generated hypotheses"
            },
            "domain_focus": {
                "type": "continuous",
                "min": 0.0,
                "max": 1.0,
                "description": "Specialization vs generalization"
            },

            # Experiment planning parameters
            "experiment_duration_preference": {
                "type": "discrete",
                "values": ["short", "medium", "long"],
                "description": "Preferred experiment duration"
            },
            "risk_tolerance": {
                "type": "continuous",
                "min": 0.0,
                "max": 1.0,
                "description": "Willingness to try risky experiments"
            },
            "resource_budget": {
                "type": "continuous",
                "min": 0.1,
                "max": 1.0,
                "description": "Resource allocation strategy"
            },

            # Analysis parameters
            "statistical_threshold": {
                "type": "continuous",
                "min": 0.01,
                "max": 0.1,
                "description": "P-value threshold for significance"
            },
            "exploration_exploitation_balance": {
                "type": "continuous",
                "min": 0.0,
                "max": 1.0,
                "description": "Explore new vs exploit known"
            },

            # Learning parameters
            "memory_retention": {
                "type": "continuous",
                "min": 0.5,
                "max": 1.0,
                "description": "How long to retain memories"
            },
            "adaptation_rate": {
                "type": "continuous",
                "min": 0.01,
                "max": 0.5,
                "description": "Speed of strategy adaptation"
            }
        }

    def initialize_population(self, seed_strategy: Optional[Dict] = None):
        """
        Initialize population with random or seeded strategies.

        Args:
            seed_strategy: Optional initial strategy to base population on
        """
        logger.info(f"Initializing population of {self.config.population_size}")

        self.population = []

        for i in range(self.config.population_size):
            if seed_strategy and i == 0:
                # Use seed as first member
                params = seed_strategy
            else:
                # Generate random parameters
                params = self._generate_random_parameters()

            strategy = Strategy(
                id=f"strategy_gen0_{i}",
                name=f"Strategy {i}",
                parameters=params,
                generation=0
            )

            self.population.append(strategy)

        logger.success(f"Population initialized with {len(self.population)} strategies")

    def _generate_random_parameters(self) -> Dict[str, Any]:
        """Generate random parameters within search space"""
        params = {}

        for param_name, param_config in self.parameter_space.items():
            if param_config["type"] == "continuous":
                params[param_name] = random.uniform(
                    param_config["min"],
                    param_config["max"]
                )
            elif param_config["type"] == "discrete":
                params[param_name] = random.choice(param_config["values"])

        return params

    def evaluate_strategy(
        self,
        strategy: Strategy,
        performance: PerformanceMetrics
    ):
        """
        Evaluate strategy based on performance metrics.

        Args:
            strategy: Strategy to evaluate
            performance: Performance metrics
        """
        # Add to history
        strategy.performance_history.append(performance)

        # Calculate fitness score (weighted combination)
        fitness = (
            0.3 * performance.accuracy +
            0.2 * performance.success_rate +
            0.2 * performance.novelty_score +
            0.15 * performance.efficiency +
            0.15 * (performance.precision + performance.recall) / 2
        )

        strategy.fitness_score = fitness

        logger.debug(f"Strategy {strategy.id} fitness: {fitness:.3f}")

    def evolve_generation(self) -> List[Strategy]:
        """
        Evolve population to next generation.

        Steps:
        1. Selection - Keep best strategies
        2. Crossover - Combine successful strategies
        3. Mutation - Introduce variations
        4. Replacement - Form new population

        Returns:
            New generation of strategies
        """
        logger.info(f"Evolving generation {self.generation_counter}")

        # 1. Selection
        elite = self._select_elite()

        # 2. Generate offspring through crossover
        offspring = []
        target_offspring = self.config.population_size - len(elite)

        while len(offspring) < target_offspring:
            if random.random() < self.config.crossover_rate:
                parent1 = self._tournament_selection()
                parent2 = self._tournament_selection()
                child = self._crossover(parent1, parent2)
            else:
                # Clone elite member
                child = copy.deepcopy(random.choice(elite))

            # 3. Mutation
            if random.random() < self.config.mutation_rate:
                child = self._mutate(child)

            child.generation = self.generation_counter + 1
            child.id = f"strategy_gen{child.generation}_{len(offspring)}"
            offspring.append(child)

        # 4. Replacement
        new_population = elite + offspring
        self.population = new_population
        self.generation_counter += 1

        # Track best
        best_strategy = max(self.population, key=lambda s: s.fitness_score)
        self.best_strategies.append(copy.deepcopy(best_strategy))

        # Log evolution history
        self.evolution_history.append({
            "generation": self.generation_counter,
            "best_fitness": best_strategy.fitness_score,
            "avg_fitness": np.mean([s.fitness_score for s in self.population]),
            "diversity": self._calculate_diversity(),
            "timestamp": datetime.now().isoformat()
        })

        logger.success(
            f"Generation {self.generation_counter}: "
            f"Best fitness={best_strategy.fitness_score:.3f}"
        )

        return new_population

    def _select_elite(self) -> List[Strategy]:
        """Select top performing strategies"""
        sorted_pop = sorted(
            self.population,
            key=lambda s: s.fitness_score,
            reverse=True
        )

        elite_count = int(self.config.population_size * self.config.selection_pressure)
        return sorted_pop[:elite_count]

    def _tournament_selection(self, tournament_size: int = 3) -> Strategy:
        """Select strategy via tournament"""
        tournament = random.sample(self.population, tournament_size)
        return max(tournament, key=lambda s: s.fitness_score)

    def _crossover(self, parent1: Strategy, parent2: Strategy) -> Strategy:
        """
        Create offspring by combining parent parameters.

        Uses uniform crossover: randomly select each parameter
        from either parent.
        """
        child_params = {}

        for param_name in self.parameter_space.keys():
            # Randomly choose from parent1 or parent2
            if random.random() < 0.5:
                child_params[param_name] = parent1.parameters.get(param_name)
            else:
                child_params[param_name] = parent2.parameters.get(param_name)

        child = Strategy(
            id="temp",  # Will be updated
            name="Offspring",
            parameters=child_params,
            parent_ids=[parent1.id, parent2.id]
        )

        return child

    def _mutate(self, strategy: Strategy) -> Strategy:
        """
        Mutate strategy parameters.

        Randomly modify parameters within search space.
        """
        mutated_params = copy.deepcopy(strategy.parameters)

        # Mutate 1-3 random parameters
        params_to_mutate = random.sample(
            list(self.parameter_space.keys()),
            k=random.randint(1, 3)
        )

        for param_name in params_to_mutate:
            param_config = self.parameter_space[param_name]

            if param_config["type"] == "continuous":
                # Add Gaussian noise
                current = mutated_params[param_name]
                noise = random.gauss(0, 0.1)
                new_value = np.clip(
                    current + noise,
                    param_config["min"],
                    param_config["max"]
                )
                mutated_params[param_name] = new_value

            elif param_config["type"] == "discrete":
                # Random selection
                mutated_params[param_name] = random.choice(param_config["values"])

        strategy.parameters = mutated_params
        return strategy

    def _calculate_diversity(self) -> float:
        """
        Calculate population diversity.

        Higher diversity = more exploration
        Lower diversity = convergence
        """
        if len(self.population) < 2:
            return 0.0

        # Calculate parameter variance
        all_params = []
        for strategy in self.population:
            # Convert parameters to numeric vector
            param_vector = []
            for param_name, param_value in strategy.parameters.items():
                if isinstance(param_value, (int, float)):
                    param_vector.append(param_value)
                else:
                    # Hash discrete values
                    param_vector.append(hash(str(param_value)) % 100 / 100)
            all_params.append(param_vector)

        # Calculate variance
        param_array = np.array(all_params)
        diversity = np.mean(np.var(param_array, axis=0))

        return float(diversity)

    def get_best_strategy(self) -> Strategy:
        """Get current best performing strategy"""
        if not self.population:
            raise ValueError("No strategies in population")

        return max(self.population, key=lambda s: s.fitness_score)

    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of evolution progress"""
        if not self.population:
            return {}

        best = self.get_best_strategy()

        return {
            "current_generation": self.generation_counter,
            "population_size": len(self.population),
            "best_fitness": best.fitness_score,
            "best_strategy_id": best.id,
            "best_parameters": best.parameters,
            "avg_fitness": np.mean([s.fitness_score for s in self.population]),
            "diversity": self._calculate_diversity(),
            "evolution_history": self.evolution_history[-10:],  # Last 10 generations
            "total_evaluations": sum(
                len(s.performance_history) for s in self.population
            )
        }

    def save_checkpoint(self, filepath: str):
        """Save optimizer state to file"""
        checkpoint = {
            "config": {
                "population_size": self.config.population_size,
                "mutation_rate": self.config.mutation_rate,
                "crossover_rate": self.config.crossover_rate,
                "selection_pressure": self.config.selection_pressure
            },
            "generation": self.generation_counter,
            "population": [
                {
                    "id": s.id,
                    "name": s.name,
                    "parameters": s.parameters,
                    "fitness": s.fitness_score,
                    "generation": s.generation
                }
                for s in self.population
            ],
            "best_strategies": [
                {
                    "id": s.id,
                    "parameters": s.parameters,
                    "fitness": s.fitness_score
                }
                for s in self.best_strategies[-5:]  # Last 5 best
            ],
            "evolution_history": self.evolution_history
        }

        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Checkpoint saved to {filepath}")

    def load_checkpoint(self, filepath: str):
        """Load optimizer state from file"""
        with open(filepath, 'r') as f:
            checkpoint = json.load(f)

        self.generation_counter = checkpoint["generation"]
        self.evolution_history = checkpoint["evolution_history"]

        # Reconstruct population
        self.population = [
            Strategy(
                id=s["id"],
                name=s["name"],
                parameters=s["parameters"],
                fitness_score=s["fitness"],
                generation=s["generation"]
            )
            for s in checkpoint["population"]
        ]

        logger.info(f"Checkpoint loaded from {filepath}")


class AdaptiveLearner:
    """
    Adaptive learning system that adjusts behavior based on feedback.

    Implements online learning to continuously improve performance.
    """

    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.performance_buffer: List[PerformanceMetrics] = []
        self.adaptation_history: List[Dict] = []

    def observe_performance(self, metrics: PerformanceMetrics):
        """Record performance observation"""
        self.performance_buffer.append(metrics)

        # Keep last 100 observations
        if len(self.performance_buffer) > 100:
            self.performance_buffer.pop(0)

    def suggest_adaptations(self, current_strategy: Dict) -> Dict[str, Any]:
        """
        Suggest parameter adaptations based on recent performance.

        Args:
            current_strategy: Current strategy parameters

        Returns:
            Suggested parameter adjustments
        """
        if len(self.performance_buffer) < 5:
            return {}  # Not enough data

        recent_perf = self.performance_buffer[-10:]

        # Analyze trends
        avg_accuracy = np.mean([p.accuracy for p in recent_perf])
        avg_novelty = np.mean([p.novelty_score for p in recent_perf])

        suggestions = {}

        # If accuracy is low, suggest more conservative approach
        if avg_accuracy < 0.6:
            suggestions["hypothesis_creativity"] = max(
                0.0,
                current_strategy.get("hypothesis_creativity", 0.5) - self.learning_rate
            )
            suggestions["risk_tolerance"] = max(
                0.0,
                current_strategy.get("risk_tolerance", 0.5) - self.learning_rate
            )

        # If novelty is low, suggest more exploration
        if avg_novelty < 0.5:
            suggestions["hypothesis_creativity"] = min(
                1.0,
                current_strategy.get("hypothesis_creativity", 0.5) + self.learning_rate
            )
            suggestions["exploration_exploitation_balance"] = min(
                1.0,
                current_strategy.get("exploration_exploitation_balance", 0.5) + self.learning_rate
            )

        if suggestions:
            self.adaptation_history.append({
                "timestamp": datetime.now().isoformat(),
                "trigger": "performance_feedback",
                "suggestions": suggestions
            })

        return suggestions

    def get_learning_progress(self) -> Dict[str, Any]:
        """Get learning progress summary"""
        if not self.performance_buffer:
            return {}

        recent = self.performance_buffer[-20:]

        return {
            "observations": len(self.performance_buffer),
            "recent_avg_accuracy": np.mean([p.accuracy for p in recent]),
            "recent_avg_novelty": np.mean([p.novelty_score for p in recent]),
            "adaptations_made": len(self.adaptation_history),
            "last_adaptation": self.adaptation_history[-1] if self.adaptation_history else None
        }
