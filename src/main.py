"""
CLI simplu pentru generarea si vizualizarea (text) a unui nivel.

Exemplu de rulare:
    python src/main.py --difficulty medium
    python src/main.py --difficulty hard --seed 42
"""

from __future__ import annotations

import argparse

from difficulty import compute_difficulty_score
from export_json import save_level_json
from generator import Difficulty, generate_level


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Escape Room Generator - CLI de test")
    parser.add_argument(
        "--difficulty",
        choices=[d.value for d in Difficulty],
        default=Difficulty.EASY.value,
        help="Dificultatea nivelului generat",
    )
    parser.add_argument("--seed", type=int, default=None, help="Seed pentru reproducibilitate")
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=200,
        help="Cate incercari de generare inainte de a renunta",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Cale fisier JSON unde se exporta nivelul (ex: pentru front-end-ul Unity)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    difficulty = Difficulty(args.difficulty)

    grid, result = generate_level(difficulty, seed=args.seed, max_attempts=args.max_attempts)

    print(f"Dificultate: {difficulty.value}")
    print(f"Dimensiune: {grid.width}x{grid.height}")
    print()
    print(grid.render())
    print()

    if result.is_valid:
        print(f"[OK] Nivel valid. Lungime traseu optim S->K->D->E: {result.total_length} pasi")

        score = compute_difficulty_score(grid, result)
        match = "OK" if score.category == difficulty.value else "NEPOTRIVIT"
        print(
            f"Scor dificultate: {score.raw_score:.1f} -> masurat ca '{score.category}' "
            f"(cerut: '{difficulty.value}') [{match}]"
        )
        print(
            f"  detalii: traseu={score.path_length} pasi, inamici={score.enemy_count}, "
            f"capcane={score.trap_count}, comori={score.treasure_count}, "
            f"densitate pereti={score.wall_density:.0%}"
        )
    else:
        print(f"[EROARE] Nivel invalid: {result.reason}")

    if args.export:
        save_level_json(args.export, grid, result, difficulty)
        print(f"\nExportat in: {args.export}")


if __name__ == "__main__":
    main()
