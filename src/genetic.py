"""
Algoritm genetic pentru optimizarea unui nivel Escape Room.

Cromozomul este format din:

    cells_x
    cells_y
    enemy_count
    trap_count
    treasure_count

Fiecare individ este transformat intr-un nivel valid folosind
generator.generate_level_from_params().

Fitness-ul folosit este fitness-ul complex definit in complex_fitness.py.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from difficulty import (
    CATEGORY_TARGET_SCORE,
    DifficultyScore,
    compute_difficulty_score,
)

from generator import (
    Difficulty,
    generate_level_from_params,
)

from grid import Grid
from solver import ValidationResult

from complex_fitness import (
    FitnessBreakdown,
    complex_fitness,
)


# ---------------------------------------------------------------------
# LIMITE GENE
# ---------------------------------------------------------------------

GENE_BOUNDS: dict[str, tuple[int, int]] = {
    "cells_x": (4, 14),
    "cells_y": (4, 14),
    "enemy_count": (0, 10),
    "trap_count": (0, 10),
    "treasure_count": (0, 6),
}

GENE_NAMES = list(
    GENE_BOUNDS.keys()
)


# ---------------------------------------------------------------------
# INDIVIDUAL
# ---------------------------------------------------------------------

@dataclass
class Individual:
    genes: dict[str, int]

    grid: Grid | None = None

    result: ValidationResult | None = None

    score: DifficultyScore | None = None

    fitness: float = float("-inf")

    fitness_breakdown: FitnessBreakdown | None = None


# ---------------------------------------------------------------------
# INITIALIZARE
# ---------------------------------------------------------------------

def _random_genes(
    rng: random.Random,
) -> dict[str, int]:

    return {
        name: rng.randint(lo, hi)
        for name, (lo, hi)
        in GENE_BOUNDS.items()
    }


# ---------------------------------------------------------------------
# CLAMP
# ---------------------------------------------------------------------

def _clamp_genes(
    genes: dict[str, float],
) -> dict[str, int]:

    clamped: dict[str, int] = {}

    for name, value in genes.items():

        lo, hi = GENE_BOUNDS[name]

        clamped[name] = int(
            max(
                lo,
                min(
                    hi,
                    round(value),
                ),
            )
        )

    return clamped


# ---------------------------------------------------------------------
# EVALUARE INDIVID
# ---------------------------------------------------------------------

def evaluate(
    genes: dict[str, int],
    target_score: float,
    difficulty: str,
    rng: random.Random,
) -> Individual:
    """
    Construieste un nivel si calculeaza fitness-ul complex.
    """

    grid, result = generate_level_from_params(
        genes["cells_x"],
        genes["cells_y"],
        genes["enemy_count"],
        genes["trap_count"],
        genes["treasure_count"],
        seed=rng.randrange(1_000_000),
    )

    if (
        grid is None
        or result is None
        or not result.is_valid
    ):
        return Individual(
            genes=genes,
            grid=grid,
            result=result,
            fitness=float("-inf"),
        )

    # Calculam scorul nivelului.
    score = compute_difficulty_score(
        grid,
        result,
    )

    # Calculam fitness-ul complex.
    breakdown = complex_fitness(
        score=score,
        target_score=target_score,
        difficulty=difficulty,
    )

    return Individual(
        genes=genes,
        grid=grid,
        result=result,
        score=score,
        fitness=breakdown.final_fitness,
        fitness_breakdown=breakdown,
    )


# ---------------------------------------------------------------------
# SELECTIE
# ---------------------------------------------------------------------

def _tournament_select(
    population: list[Individual],
    rng: random.Random,
    k: int = 3,
) -> Individual:

    k = min(
        k,
        len(population),
    )

    contenders = rng.sample(
        population,
        k,
    )

    return max(
        contenders,
        key=lambda ind: ind.fitness,
    )


# ---------------------------------------------------------------------
# CROSSOVER
# ---------------------------------------------------------------------

def _crossover(
    parent_a: Individual,
    parent_b: Individual,
    rng: random.Random,
) -> dict[str, int]:

    child = {}

    for name in GENE_NAMES:

        if rng.random() < 0.5:
            child[name] = parent_a.genes[name]
        else:
            child[name] = parent_b.genes[name]

    return child


# ---------------------------------------------------------------------
# MUTATIE
# ---------------------------------------------------------------------

def _mutate(
    genes: dict[str, int],
    rng: random.Random,
    rate: float,
    strength: float,
) -> dict[str, int]:

    mutated = dict(genes)

    for name in GENE_NAMES:

        if rng.random() < rate:

            lo, hi = GENE_BOUNDS[name]

            span = hi - lo

            mutated[name] += rng.gauss(
                0,
                span * strength,
            )

    return _clamp_genes(
        mutated
    )


# ---------------------------------------------------------------------
# REZULTAT
# ---------------------------------------------------------------------

@dataclass
class GAResult:

    best: Individual

    best_fitness_history: list[float] = field(
        default_factory=list
    )

    mean_fitness_history: list[float] = field(
        default_factory=list
    )

    target_score: float = 0.0

    difficulty: str = "medium"


# ---------------------------------------------------------------------
# ALGORITM PRINCIPAL
# ---------------------------------------------------------------------

def run_genetic_algorithm(
    target_score: float,
    population_size: int = 24,
    generations: int = 30,
    elitism: int = 2,
    mutation_rate: float = 0.3,
    mutation_strength: float = 0.15,
    seed: int | None = None,
    difficulty: str = "medium",
) -> GAResult:
    """
    Ruleaza algoritmul genetic.

    difficulty:
        easy / medium / hard

    target_score:
        scorul global dorit.
    """

    if difficulty not in (
        "easy",
        "medium",
        "hard",
    ):
        raise ValueError(
            "difficulty trebuie sa fie "
            "'easy', 'medium' sau 'hard'."
        )

    if population_size < 2:
        raise ValueError(
            "population_size trebuie sa fie >= 2."
        )

    if generations < 1:
        raise ValueError(
            "generations trebuie sa fie >= 1."
        )

    if elitism < 0:
        raise ValueError(
            "elitism trebuie sa fie >= 0."
        )

    if elitism >= population_size:
        elitism = population_size - 1

    rng = random.Random(seed)

    # -------------------------------------------------------------
    # POPULATIA INITIALA
    # -------------------------------------------------------------

    population = [
        evaluate(
            genes=_random_genes(rng),
            target_score=target_score,
            difficulty=difficulty,
            rng=rng,
        )
        for _ in range(population_size)
    ]

    best_history: list[float] = []
    mean_history: list[float] = []

    # -------------------------------------------------------------
    # ISTORIC FITNESS
    # -------------------------------------------------------------

    def record(
        pop: list[Individual],
    ) -> None:

        pop.sort(
            key=lambda ind: ind.fitness,
            reverse=True,
        )

        best_history.append(
            float(pop[0].fitness)
        )

        finite = [
            ind.fitness
            for ind in pop
            if np.isfinite(ind.fitness)
        ]

        if finite:
            mean_history.append(
                float(np.mean(finite))
            )
        else:
            mean_history.append(
                float("-inf")
            )

    # -------------------------------------------------------------
    # GENERATII
    # -------------------------------------------------------------

    for _ in range(generations):

        record(population)

        next_population = population[
            :elitism
        ]

        while len(next_population) < population_size:

            parent_a = _tournament_select(
                population,
                rng,
            )

            parent_b = _tournament_select(
                population,
                rng,
            )

            child_genes = _crossover(
                parent_a,
                parent_b,
                rng,
            )

            child_genes = _mutate(
                child_genes,
                rng,
                mutation_rate,
                mutation_strength,
            )

            child = evaluate(
                genes=child_genes,
                target_score=target_score,
                difficulty=difficulty,
                rng=rng,
            )

            next_population.append(
                child
            )

        population = next_population

    # Inregistram si ultima generatie.
    record(population)

    return GAResult(
        best=population[0],
        best_fitness_history=best_history,
        mean_fitness_history=mean_history,
        target_score=target_score,
        difficulty=difficulty,
    )


# ---------------------------------------------------------------------
# RUN PENTRU DIFFICULTY
# ---------------------------------------------------------------------

def run_for_difficulty(
    difficulty: Difficulty,
    **kwargs,
) -> GAResult:

    target = CATEGORY_TARGET_SCORE[
        difficulty.value
    ]

    return run_genetic_algorithm(
        target_score=target,
        difficulty=difficulty.value,
        **kwargs,
    )