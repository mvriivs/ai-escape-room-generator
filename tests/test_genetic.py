"""Teste pentru algoritmul genetic de optimizare a dificultatii."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from genetic import run_genetic_algorithm


def test_best_individual_is_valid_and_close_to_target():
    target = 111.0  # ~mijlocul benzii "medium"
    result = run_genetic_algorithm(
        target_score=target, population_size=16, generations=15, seed=42
    )

    assert result.best.result is not None
    assert result.best.result.is_valid
    assert result.best.score is not None
    # ar trebui sa gaseasca ceva rezonabil de aproape de tinta
    assert abs(result.best.score.raw_score - target) < 15


def test_fitness_history_length_matches_generations():
    generations = 10
    result = run_genetic_algorithm(target_score=100.0, population_size=12, generations=generations, seed=1)

    assert len(result.best_fitness_history) == generations + 1  # +1 pt. generatia finala
    assert len(result.mean_fitness_history) == generations + 1


def test_best_fitness_never_gets_worse_across_generations():
    """Datorita elitismului, cel mai bun fitness observat nu ar trebui sa
    scada niciodata de la o generatie la alta."""
    result = run_genetic_algorithm(target_score=150.0, population_size=16, generations=15, seed=5)

    history = result.best_fitness_history
    for i in range(1, len(history)):
        assert history[i] >= history[i - 1] - 1e-9


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"OK  {t.__name__}")
    print(f"\n{passed}/{len(tests)} teste trecute")
