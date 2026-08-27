"""
CLI pentru rularea algoritmului genetic.

Exemple:

    python src/run_genetic.py --difficulty easy

    python src/run_genetic.py --difficulty medium

    python src/run_genetic.py --difficulty hard

    python src/run_genetic.py --difficulty medium --generations 50

    python src/run_genetic.py --difficulty hard --plot fitness.png

    python src/run_genetic.py --difficulty medium --export level.json
"""

from __future__ import annotations

import argparse

from difficulty import CATEGORY_TARGET_SCORE
from export_json import save_level_json
from generator import Difficulty
from genetic import run_genetic_algorithm


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Optimizare Escape Room "
            "cu algoritm genetic"
        )
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--difficulty",
        choices=[
            d.value
            for d in Difficulty
        ],
        help=(
            "Dificultatea pentru care "
            "se optimizeaza nivelul"
        ),
    )

    group.add_argument(
        "--target-score",
        type=float,
        help=(
            "Scor tinta exact"
        ),
    )

    parser.add_argument(
        "--population",
        type=int,
        default=24,
        help="Dimensiunea populatiei",
    )

    parser.add_argument(
        "--generations",
        type=int,
        default=30,
        help="Numarul de generatii",
    )

    parser.add_argument(
        "--elitism",
        type=int,
        default=2,
        help="Numarul indivizilor pastrati",
    )

    parser.add_argument(
        "--mutation-rate",
        type=float,
        default=0.3,
        help="Probabilitatea de mutatie",
    )

    parser.add_argument(
        "--mutation-strength",
        type=float,
        default=0.15,
        help="Intensitatea mutatiei",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed pentru reproducibilitate",
    )

    parser.add_argument(
        "--plot",
        type=str,
        default=None,
        help=(
            "Fisier PNG pentru istoricul "
            "fitness-ului"
        ),
    )

    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help=(
            "Fisier JSON pentru nivelul final"
        ),
    )

    return parser.parse_args()


def main() -> None:

    args = parse_args()

    # -------------------------------------------------------------
    # STABILIRE TARGET
    # -------------------------------------------------------------

    if args.target_score is not None:

        target = args.target_score

        difficulty_label = (
            f"scor={target:.1f}"
        )

        # Pentru export avem nevoie de o eticheta.
        difficulty_for_export = Difficulty.MEDIUM

        difficulty_value = "medium"

    else:

        difficulty_value = (
            args.difficulty
            or Difficulty.MEDIUM.value
        )

        target = CATEGORY_TARGET_SCORE[
            difficulty_value
        ]

        difficulty_label = (
            difficulty_value
        )

        difficulty_for_export = Difficulty(
            difficulty_value
        )

    # -------------------------------------------------------------
    # AFISARE CONFIGURATIE
    # -------------------------------------------------------------

    print()
    print(
        "=========================================="
    )
    print(
        " AI ESCAPE ROOM - ALGORITM GENETIC"
    )
    print(
        "=========================================="
    )

    print(
        f"Dificultate: {difficulty_label}"
    )

    print(
        f"Scor tinta: {target:.1f}"
    )

    print(
        f"Populatie: {args.population}"
    )

    print(
        f"Generatii: {args.generations}"
    )

    print()

    # -------------------------------------------------------------
    # RUN GA
    # -------------------------------------------------------------

    result = run_genetic_algorithm(
        target_score=target,
        population_size=args.population,
        generations=args.generations,
        elitism=args.elitism,
        mutation_rate=args.mutation_rate,
        mutation_strength=args.mutation_strength,
        seed=args.seed,
        difficulty=difficulty_value,
    )

    best = result.best

    # -------------------------------------------------------------
    # REZULTAT
    # -------------------------------------------------------------

    print(
        "Cel mai bun individ gasit:"
    )

    print(
        f"  Fitness final: "
        f"{best.fitness:.4f}"
    )

    print(
        f"  Scor dificultate: "
        f"{best.score.raw_score:.2f}"
    )

    print(
        f"  Scor tinta: "
        f"{target:.2f}"
    )

    print(
        f"  Categorie masurata: "
        f"{best.score.category}"
    )

    print()

    print(
        "Gene:"
    )

    for name, value in best.genes.items():
        print(
            f"  {name}: {value}"
        )

    # -------------------------------------------------------------
    # CARACTERISTICI
    # -------------------------------------------------------------

    print()

    print(
        "Caracteristici:"
    )

    print(
        f"  traseu: "
        f"{best.score.path_length} pasi"
    )

    print(
        f"  inamici: "
        f"{best.score.enemy_count}"
    )

    print(
        f"  capcane: "
        f"{best.score.trap_count}"
    )

    print(
        f"  comori: "
        f"{best.score.treasure_count}"
    )

    print(
        f"  densitate pereti: "
        f"{best.score.wall_density:.2%}"
    )

    print(
        f"  dead-end ratio: "
        f"{best.score.dead_end_ratio:.2%}"
    )

    # -------------------------------------------------------------
    # FITNESS BREAKDOWN
    # -------------------------------------------------------------

    if best.fitness_breakdown is not None:

        breakdown = (
            best.fitness_breakdown
        )

        print()

        print(
            "Descompunere fitness:"
        )

        print(
            f"  similaritate scor: "
            f"{breakdown.total_similarity:.4f}"
        )

        print(
            f"  similaritate caracteristici: "
            f"{breakdown.feature_similarity:.4f}"
        )

        print(
            f"  complexitate structurala: "
            f"{breakdown.structural_complexity:.4f}"
        )

        print(
            f"  bonus interactiuni: "
            f"{breakdown.interaction_bonus:.4f}"
        )

        print(
            f"  penalizare dezechilibru: "
            f"{breakdown.balance_penalty:.4f}"
        )

    # -------------------------------------------------------------
    # GRID
    # -------------------------------------------------------------

    print()

    print(
        "Nivel generat:"
    )

    print(
        best.grid.render()
    )

    # -------------------------------------------------------------
    # PLOT
    # -------------------------------------------------------------

    if args.plot:

        from plot_fitness import (
            plot_fitness_history,
        )

        plot_fitness_history(
            result,
            args.plot,
            title=(
                "Evolutie fitness - "
                f"{difficulty_label}"
            ),
        )

        print()

        print(
            f"Grafic salvat in: "
            f"{args.plot}"
        )

    # -------------------------------------------------------------
    # EXPORT JSON
    # -------------------------------------------------------------

    if args.export:

        save_level_json(
            args.export,
            best.grid,
            best.result,
            difficulty_for_export,
        )

        print()

        print(
            f"Nivel exportat in: "
            f"{args.export}"
        )


if __name__ == "__main__":
    main()