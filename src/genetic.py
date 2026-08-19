"""
Algoritm genetic pentru ajustarea unui nivel catre un scor de dificultate
TINTA (mai precis decat generarea directa dintr-o presetare Easy/Medium/Hard).

Cromozom = un vector de parametri de generare:
    cells_x, cells_y       -- dimensiunea labirintului
    enemy_count             -- numar de inamici
    trap_count              -- numar de capcane
    treasure_count           -- numar de comori

Din acesti parametri se construieste efectiv un nivel, folosind
`generator.generate_level_from_params` -- adica FIECARE individ e mereu un
nivel valid (Cheia/Usa obligatorii), indiferent de valorile genelor.
Algoritmul genetic nu "repara" niveluri stricate, ci cauta combinatia de
parametri al carei scor de dificultate (difficulty.py) e cat mai aproape de
scorul tinta.

Operatii clasice de algoritm genetic:
    - selectie:  turneu (se aleg k indivizi random, castiga cel mai bun)
    - crossover: uniform (fiecare gena vine random de la unul din parinti)
    - mutatie:   perturbare gaussiana pe fiecare gena, cu o probabilitate data
    - elitism:   cei mai buni N indivizi trec neschimbati in generatia urmatoare

Fitness = -abs(scor_obtinut - scor_tinta)  (0 = perfect; cu cat mai negativ,
cu atat mai departe de tinta). Se maximizeaza.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from difficulty import CATEGORY_TARGET_SCORE, DifficultyScore, compute_difficulty_score
from generator import Difficulty, generate_level_from_params
from grid import Grid
from solver import ValidationResult

# Limite [min, max] pentru fiecare gena.
GENE_BOUNDS: dict[str, tuple[int, int]] = {
    "cells_x": (4, 14),
    "cells_y": (4, 14),
    "enemy_count": (0, 10),
    "trap_count": (0, 10),
    "treasure_count": (0, 6),
}
GENE_NAMES = list(GENE_BOUNDS.keys())


@dataclass
class Individual:
    genes: dict[str, int]
    grid: Grid | None = None
    result: ValidationResult | None = None
    score: DifficultyScore | None = None
    fitness: float = float("-inf")


def _random_genes(rng: random.Random) -> dict[str, int]:
    return {name: rng.randint(lo, hi) for name, (lo, hi) in GENE_BOUNDS.items()}


def _clamp_genes(genes: dict[str, float]) -> dict[str, int]:
    clamped = {}
    for name, value in genes.items():
        lo, hi = GENE_BOUNDS[name]
        clamped[name] = int(max(lo, min(hi, round(value))))
    return clamped


def evaluate(genes: dict[str, int], target_score: float, rng: random.Random) -> Individual:
    """Construieste efectiv nivelul descris de `genes` si calculeaza fitness-ul
    lui fata de `target_score`."""
    grid, result = generate_level_from_params(
        genes["cells_x"],
        genes["cells_y"],
        genes["enemy_count"],
        genes["trap_count"],
        genes["treasure_count"],
        seed=rng.randrange(1_000_000),
    )
    if grid is None or result is None or not result.is_valid:
        return Individual(genes=genes, grid=grid, result=result, fitness=float("-inf"))

    score = compute_difficulty_score(grid, result)
    fitness = -abs(score.raw_score - target_score)
    return Individual(genes=genes, grid=grid, result=result, score=score, fitness=fitness)


def _tournament_select(population: list[Individual], rng: random.Random, k: int = 3) -> Individual:
    contenders = rng.sample(population, k)
    return max(contenders, key=lambda ind: ind.fitness)


def _crossover(parent_a: Individual, parent_b: Individual, rng: random.Random) -> dict[str, int]:
    return {name: (parent_a.genes[name] if rng.random() < 0.5 else parent_b.genes[name]) for name in GENE_NAMES}


def _mutate(genes: dict[str, int], rng: random.Random, rate: float, strength: float) -> dict[str, int]:
    mutated = dict(genes)
    for name in GENE_NAMES:
        if rng.random() < rate:
            lo, hi = GENE_BOUNDS[name]
            span = hi - lo
            mutated[name] = mutated[name] + rng.gauss(0, span * strength)
    return _clamp_genes(mutated)


@dataclass
class GAResult:
    best: Individual
    best_fitness_history: list[float] = field(default_factory=list)
    mean_fitness_history: list[float] = field(default_factory=list)
    target_score: float = 0.0


def run_genetic_algorithm(
    target_score: float,
    population_size: int = 24,
    generations: int = 30,
    elitism: int = 2,
    mutation_rate: float = 0.3,
    mutation_strength: float = 0.15,
    seed: int | None = None,
) -> GAResult:
    """Evolueaza o populatie de niveluri pe `generations` generatii, ca sa
    gaseasca parametrii al caror scor de dificultate e cat mai aproape de
    `target_score`. Returneaza cel mai bun individ gasit + istoricul
    fitness-ului (pentru graficul de evolutie)."""
    rng = random.Random(seed)

    population = [evaluate(_random_genes(rng), target_score, rng) for _ in range(population_size)]

    best_history: list[float] = []
    mean_history: list[float] = []

    def record(pop: list[Individual]) -> None:
        pop.sort(key=lambda ind: ind.fitness, reverse=True)
        best_history.append(pop[0].fitness)
        finite = [ind.fitness for ind in pop if np.isfinite(ind.fitness)]
        mean_history.append(float(np.mean(finite)) if finite else float("-inf"))

    for _ in range(generations):
        record(population)

        next_population = population[:elitism]  # elitism: trec neschimbati
        while len(next_population) < population_size:
            parent_a = _tournament_select(population, rng)
            parent_b = _tournament_select(population, rng)
            child_genes = _crossover(parent_a, parent_b, rng)
            child_genes = _mutate(child_genes, rng, mutation_rate, mutation_strength)
            next_population.append(evaluate(child_genes, target_score, rng))

        population = next_population

    record(population)  # generatia finala

    return GAResult(
        best=population[0],
        best_fitness_history=best_history,
        mean_fitness_history=mean_history,
        target_score=target_score,
    )


def run_for_difficulty(difficulty: Difficulty, **kwargs) -> GAResult:
    """Comoditate: ruleaza algoritmul genetic cu scorul tinta calibrat pentru
    o dificultate Easy/Medium/Hard, in loc sa dai un scor brut manual."""
    target = CATEGORY_TARGET_SCORE[difficulty.value]
    return run_genetic_algorithm(target, **kwargs)
