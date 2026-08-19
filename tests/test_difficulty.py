"""Teste pentru scorul de dificultate."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from difficulty import compute_difficulty_score
from generator import Difficulty, generate_level


def test_score_increases_with_difficulty():
    """Scorul mediu masurat trebuie sa creasca strict Easy < Medium < Hard,
    pe acelasi set de seed-uri."""
    seeds = range(10)

    def avg_score(diff):
        total = 0.0
        for seed in seeds:
            grid, result = generate_level(diff, seed=seed)
            assert result.is_valid
            total += compute_difficulty_score(grid, result).raw_score
        return total / len(list(seeds))

    easy_avg = avg_score(Difficulty.EASY)
    medium_avg = avg_score(Difficulty.MEDIUM)
    hard_avg = avg_score(Difficulty.HARD)

    assert easy_avg < medium_avg < hard_avg


def test_category_matches_requested_difficulty():
    """Pentru majoritatea seed-urilor, categoria masurata (din scor) trebuie
    sa coincida cu dificultatea ceruta la generare."""
    for diff in [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]:
        matches = 0
        trials = 20
        for seed in range(trials):
            grid, result = generate_level(diff, seed=seed)
            score = compute_difficulty_score(grid, result)
            if score.category == diff.value:
                matches += 1
        assert matches / trials >= 0.9, f"{diff.value}: doar {matches}/{trials} categorii corecte"


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"OK  {t.__name__}")
    print(f"\n{passed}/{len(tests)} teste trecute")
