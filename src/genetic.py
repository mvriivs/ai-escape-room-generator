"""
Algoritm genetic pentru ajustarea unui nivel catre o dificultate TINTA (mai
precis decat generarea directa dintr-o presetare Easy/Medium/Hard).

Cromozom = un vector de parametri de generare:
    cells_x, cells_y       -- dimensiunea labirintului
    enemy_count             -- numar de inamici
    trap_count              -- numar de capcane
    treasure_count           -- numar de comori

Din acesti parametri se construieste efectiv un nivel, folosind
`generator.generate_level_from_params` -- adica FIECARE individ e mereu un
nivel valid (Cheia/Usa obligatorii), indiferent de valorile genelor.
Algoritmul genetic nu "repara" niveluri stricate, ci cauta combinatia de
parametri cu cel mai bun fitness.

Operatii clasice de algoritm genetic:
    - selectie:  turneu (se aleg k indivizi random, castiga cel mai bun)
    - crossover: uniform (fiecare gena vine random de la unul din parinti)
    - mutatie:   perturbare gaussiana pe fiecare gena, cu o probabilitate data
    - elitism:   cei mai buni N indivizi trec neschimbati in generatia urmatoare

FUNCTII DE FITNESS -- proiectul are 3, interschimbabile prin `fitness_mode`,
cate una construita de fiecare membru al echipei, ca sa se poata compara pe
acelasi algoritm genetic (aceleasi selectie/crossover/mutatie/elitism), doar
cu "busola" diferita:

    "default"  -- (difficulty.py) eroare liniara fata de scorul brut
                  ponderat: fitness = -abs(scor - scor_tinta). Accepta orice
                  scor tinta numeric (--target-score).

    "baseline" -- (Andreea, baseline_fitness.py) eroare liniara normalizata
                  in [0, 1] fata de scorul din CATEGORY_TARGET_SCORE. Are
                  nevoie de o dificultate numita (easy/medium/hard).

    "complex"  -- (complex_fitness.py) fitness compus din similaritatea
                  scorului global + similaritatea caracteristicilor
                  individuale + complexitate structurala + bonus de
                  interactiuni intre caracteristici - penalizare de
                  dezechilibru. Are nevoie de o dificultate numita.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from baseline_fitness import baseline_linear_fitness
from complex_fitness import FitnessBreakdown, complex_fitness
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

FITNESS_MODES = ("default", "baseline", "complex")


@dataclass
class Individual:
    genes: dict[str, int]
    grid: Grid | None = None
    result: ValidationResult | None = None
    score: DifficultyScore | None = None
    fitness: float = float("-inf")
    # populat doar in modul "complex" -- util pt. debugging/grafice/prezentare
    fitness_breakdown: FitnessBreakdown | None = None


def _random_genes(rng: random.Random) -> dict[str, int]:
    return {name: rng.randint(lo, hi) for name, (lo, hi) in GENE_BOUNDS.items()}


def _clamp_genes(genes: dict[str, float]) -> dict[str, int]:
    clamped = {}
    for name, value in genes.items():
        lo, hi = GENE_BOUNDS[name]
        clamped[name] = int(max(lo, min(hi, round(value))))
    return clamped


def _resolve_fitness(
    score: DifficultyScore,
    target_score: float,
    difficulty_name: str | None,
    fitness_mode: str,
) -> tuple[float, FitnessBreakdown | None]:
    """Calculeaza fitness-ul unui scor deja obtinut, cu functia ceruta prin
    `fitness_mode`. Returneaza (fitness, breakdown-ul complex daca exista,
    altfel None)."""
    if fitness_mode == "baseline":
        if not difficulty_name:
            raise ValueError(
                "fitness_mode='baseline' are nevoie de o dificultate numita "
                "(easy/medium/hard), nu doar un scor tinta brut."
            )
        return baseline_linear_fitness(score, difficulty_name), None

    if fitness_mode == "complex":
        if not difficulty_name:
            raise ValueError(
                "fitness_mode='complex' are nevoie de o dificultate numita "
                "(easy/medium/hard), nu doar un scor tinta brut."
            )
        breakdown = complex_fitness(score, target_score, difficulty_name)
        return breakdown.final_fitness, breakdown

    if fitness_mode != "default":
        raise ValueError(f"fitness_mode necunoscut: '{fitness_mode}' (astepta {FITNESS_MODES})")

    return -abs(score.raw_score - target_score), None


def evaluate(
    genes: dict[str, int],
    target_score: float,
    rng: random.Random,
    difficulty_name: str | None = None,
    fitness_mode: str = "default",
) -> Individual:
    """Construieste efectiv nivelul descris de `genes` si calculeaza
    fitness-ul lui, folosind functia de fitness aleasa (`fitness_mode`)."""
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
    fitness, breakdown = _resolve_fitness(score, target_score, difficulty_name, fitness_mode)
    return Individual(genes=genes, grid=grid, result=result, score=score, fitness=fitness, fitness_breakdown=breakdown)


def _tournament_select(population: list[Individual], rng: random.Random, k: int = 3) -> Individual:
    k = min(k, len(population))
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
    difficulty: str = "medium"


def run_genetic_algorithm(
    target_score: float,
    difficulty_name: str | None = None,
    fitness_mode: str = "default",
    population_size: int = 24,
    generations: int = 30,
    elitism: int = 2,
    mutation_rate: float = 0.3,
    mutation_strength: float = 0.15,
    seed: int | None = None,
) -> GAResult:
    """Evolueaza o populatie de niveluri pe `generations` generatii, ca sa
    gaseasca parametrii cu cel mai bun fitness (vezi `fitness_mode`).
    Returneaza cel mai bun individ gasit + istoricul fitness-ului (pentru
    graficul de evolutie)."""
    if fitness_mode not in FITNESS_MODES:
        raise ValueError(f"fitness_mode necunoscut: '{fitness_mode}' (astepta {FITNESS_MODES})")
    if population_size < 2:
        raise ValueError("population_size trebuie sa fie >= 2.")
    if generations < 1:
        raise ValueError("generations trebuie sa fie >= 1.")
    if elitism < 0:
        raise ValueError("elitism trebuie sa fie >= 0.")
    if elitism >= population_size:
        elitism = population_size - 1

    rng = random.Random(seed)

    def make_individual(genes: dict[str, int]) -> Individual:
        return evaluate(genes, target_score, rng, difficulty_name=difficulty_name, fitness_mode=fitness_mode)

    population = [make_individual(_random_genes(rng)) for _ in range(population_size)]

    best_history: list[float] = []
    mean_history: list[float] = []

    def record(pop: list[Individual]) -> None:
        pop.sort(key=lambda ind: ind.fitness, reverse=True)
        best_history.append(float(pop[0].fitness))
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
            next_population.append(make_individual(child_genes))

        population = next_population

    record(population)  # generatia finala

    return GAResult(
        best=population[0],
        best_fitness_history=best_history,
        mean_fitness_history=mean_history,
        target_score=target_score,
        difficulty=difficulty_name or "medium",
    )


def run_for_difficulty(difficulty: Difficulty, fitness_mode: str = "default", **kwargs) -> GAResult:
    """Comoditate: ruleaza algoritmul genetic cu scorul tinta calibrat pentru
    o dificultate Easy/Medium/Hard, in loc sa dai un scor brut manual."""
    target = CATEGORY_TARGET_SCORE[difficulty.value]
    return run_genetic_algorithm(target, difficulty_name=difficulty.value, fitness_mode=fitness_mode, **kwargs)
