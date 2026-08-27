"""Teste pentru functia complexa de fitness."""

import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
    ),
)

from difficulty import DifficultyScore
from complex_fitness import complex_fitness


def make_score(
    path_length=20,
    enemy_count=2,
    trap_count=2,
    treasure_count=2,
    wall_density=0.3,
    dead_end_ratio=0.2,
    raw_score=100.0,
):
    """Construieste un DifficultyScore pentru teste."""

    return DifficultyScore(
        path_length=path_length,
        enemy_count=enemy_count,
        trap_count=trap_count,
        treasure_count=treasure_count,
        wall_density=wall_density,
        dead_end_ratio=dead_end_ratio,
        raw_score=raw_score,
    )


def test_fitness_returns_valid_components():
    """Verifica daca toate componentele fitness-ului au valori valide."""

    score = make_score(
        path_length=25,
        enemy_count=3,
        trap_count=3,
        treasure_count=3,
        wall_density=0.50,
        dead_end_ratio=0.20,
        raw_score=109.0,
    )

    result = complex_fitness(
        score,
        target_score=109.0,
        difficulty="medium",
    )

    assert 0.0 <= result.total_similarity <= 1.0
    assert 0.0 <= result.feature_similarity <= 1.0
    assert 0.0 <= result.structural_complexity <= 1.0
    assert 0.0 <= result.interaction_bonus <= 1.0
    assert result.balance_penalty >= 0.0

    assert isinstance(result.final_fitness, float)


def test_fitness_is_higher_for_better_matching_level():
    """Un nivel apropiat de tinta trebuie sa aiba fitness mai mare."""

    good_score = make_score(
        path_length=25,
        enemy_count=3,
        trap_count=3,
        treasure_count=3,
        wall_density=0.50,
        dead_end_ratio=0.20,
        raw_score=109.0,
    )

    bad_score = make_score(
        path_length=10,
        enemy_count=0,
        trap_count=0,
        treasure_count=6,
        wall_density=0.20,
        dead_end_ratio=0.05,
        raw_score=50.0,
    )

    good = complex_fitness(
        good_score,
        target_score=109.0,
        difficulty="medium",
    )

    bad = complex_fitness(
        bad_score,
        target_score=109.0,
        difficulty="medium",
    )

    assert good.final_fitness > bad.final_fitness


def test_fitness_prefers_target_score():
    """Fitness-ul trebuie sa prefere un scor global apropiat de tinta."""

    score_close = make_score(
        path_length=25,
        enemy_count=3,
        trap_count=3,
        treasure_count=3,
        wall_density=0.50,
        dead_end_ratio=0.20,
        raw_score=109.0,
    )

    score_far = make_score(
        path_length=25,
        enemy_count=3,
        trap_count=3,
        treasure_count=3,
        wall_density=0.50,
        dead_end_ratio=0.20,
        raw_score=180.0,
    )

    close = complex_fitness(
        score_close,
        target_score=109.0,
        difficulty="medium",
    )

    far = complex_fitness(
        score_far,
        target_score=109.0,
        difficulty="medium",
    )

    assert close.total_similarity > far.total_similarity


def test_fitness_handles_all_difficulties():
    """Verifica functionarea pentru Easy, Medium si Hard."""

    test_cases = [
        ("easy", 60.0),
        ("medium", 109.0),
        ("hard", 191.0),
    ]

    for difficulty, target in test_cases:

        score = make_score(
            path_length=25,
            enemy_count=3,
            trap_count=3,
            treasure_count=3,
            wall_density=0.50,
            dead_end_ratio=0.20,
            raw_score=target,
        )

        result = complex_fitness(
            score,
            target_score=target,
            difficulty=difficulty,
        )

        assert isinstance(result.final_fitness, float)

        assert 0.0 <= result.total_similarity <= 1.0
        assert 0.0 <= result.feature_similarity <= 1.0
        assert 0.0 <= result.structural_complexity <= 1.0
        assert 0.0 <= result.interaction_bonus <= 1.0
        assert result.balance_penalty >= 0.0


def test_similarity_is_best_at_target():
    """Similaritatea scorului global trebuie sa fie maxima la tinta."""

    score = make_score(
        path_length=25,
        enemy_count=3,
        trap_count=3,
        treasure_count=3,
        wall_density=0.50,
        dead_end_ratio=0.20,
        raw_score=109.0,
    )

    result = complex_fitness(
        score,
        target_score=109.0,
        difficulty="medium",
    )

    assert result.total_similarity == 1.0


def test_invalid_difficulty_raises_error():
    """O dificultate necunoscuta trebuie sa produca ValueError."""

    score = make_score()

    try:
        complex_fitness(
            score,
            target_score=100.0,
            difficulty="impossible",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Era asteptat ValueError pentru o dificultate necunoscuta."
        )


def test_as_dict_contains_all_components():
    """Verifica daca FitnessBreakdown poate fi exportat ca dictionar."""

    score = make_score(
        path_length=25,
        enemy_count=3,
        trap_count=3,
        treasure_count=3,
        wall_density=0.50,
        dead_end_ratio=0.20,
        raw_score=109.0,
    )

    result = complex_fitness(
        score,
        target_score=109.0,
        difficulty="medium",
    )

    data = result.as_dict()

    expected_keys = {
        "total_similarity",
        "feature_similarity",
        "structural_complexity",
        "interaction_bonus",
        "balance_penalty",
        "final_fitness",
    }

    assert set(data.keys()) == expected_keys


if __name__ == "__main__":
    tests = [
        obj
        for name, obj in list(globals().items())
        if name.startswith("test_")
    ]

    passed = 0

    for test in tests:
        test()
        passed += 1
        print(f"OK  {test.__name__}")

    print(f"\n{passed}/{len(tests)} teste trecute")