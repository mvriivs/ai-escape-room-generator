"""
CLI: ruleaza algoritmul genetic pana obtine un nivel cat mai apropiat de
dificultatea ceruta, afiseaza evolutia, salveaza graficul de fitness si
(optional) exporta nivelul castigator pentru Unity.

Exemple:
    python src/run_genetic.py --difficulty hard
    python src/run_genetic.py --target-score 130 --generations 50 --population 40
    python src/run_genetic.py --difficulty medium --export ../unity/Assets/StreamingAssets/level.json
"""

from __future__ import annotations

import argparse

from difficulty import CATEGORY_TARGET_SCORE
from export_json import save_level_json
from generator import Difficulty
from genetic import run_genetic_algorithm
from plot_fitness import plot_fitness_history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimizare de nivel cu algoritm genetic")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--difficulty", choices=[d.value for d in Difficulty], help="Foloseste scorul tinta calibrat pentru aceasta dificultate")
    group.add_argument("--target-score", type=float, help="Scor de dificultate tinta, exact (suprascrie --difficulty)")

    parser.add_argument("--population", type=int, default=24)
    parser.add_argument("--generations", type=int, default=30)
    parser.add_argument("--elitism", type=int, default=2)
    parser.add_argument("--mutation-rate", type=float, default=0.3)
    parser.add_argument("--mutation-strength", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=None)

    parser.add_argument("--plot", type=str, default="fitness_evolution.png", help="Cale PNG pentru graficul de fitness")
    parser.add_argument("--export", type=str, default=None, help="Cale JSON unde se exporta nivelul castigator (ex: pentru Unity)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.target_score is not None:
        target = args.target_score
        difficulty_label = f"scor={target:.1f}"
        difficulty_for_export = Difficulty.MEDIUM  # doar eticheta din JSON; scorul e cel real
    else:
        difficulty_value = args.difficulty or Difficulty.MEDIUM.value
        target = CATEGORY_TARGET_SCORE[difficulty_value]
        difficulty_label = difficulty_value
        difficulty_for_export = Difficulty(difficulty_value)

    print(f"Rulez algoritmul genetic: tinta='{difficulty_label}' (scor={target:.1f}), "
          f"populatie={args.population}, generatii={args.generations}")

    result = run_genetic_algorithm(
        target_score=target,
        population_size=args.population,
        generations=args.generations,
        elitism=args.elitism,
        mutation_rate=args.mutation_rate,
        mutation_strength=args.mutation_strength,
        seed=args.seed,
    )

    best = result.best
    print()
    print(f"Cel mai bun individ gasit (fitness={best.fitness:.2f}):")
    print(f"  gene: {best.genes}")
    if best.score:
        print(
            f"  scor obtinut={best.score.raw_score:.1f} (tinta={target:.1f}, "
            f"diferenta={abs(best.score.raw_score - target):.1f})"
        )
        print(f"  categorie masurata: '{best.score.category}'")
        print(
            f"  traseu={best.score.path_length} pasi, inamici={best.score.enemy_count}, "
            f"capcane={best.score.trap_count}, comori={best.score.treasure_count}, "
            f"densitate pereti={best.score.wall_density:.0%}"
        )
    print()
    print(best.grid.render())

    plot_fitness_history(result, args.plot, title=f"Evolutie fitness -- tinta '{difficulty_label}' (scor={target:.1f})")
    print(f"\nGrafic salvat in: {args.plot}")

    if args.export:
        save_level_json(args.export, best.grid, best.result, difficulty_for_export)
        print(f"Nivel exportat in: {args.export}")


if __name__ == "__main__":
    main()
