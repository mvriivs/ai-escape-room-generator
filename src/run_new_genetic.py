import argparse
import os
import sys
from generator import Difficulty
from genetic import run_for_difficulty
import export_json

def main():
    # Citesc argumentele trimise automat de Unity cand apas Easy/Medium/Hard sau Nivel Nou
    parser = argparse.ArgumentParser(description="AI Escape Room Generator")
    parser.add_argument("--difficulty", type=str, default="medium", help="Dificultatea dorita")
    parser.add_argument("--population", type=int, default=24, help="Dimensiunea populatiei")
    parser.add_argument("--generations", type=int, default=30, help="Numarul de generatii")
    parser.add_argument("--export", type=str, required=True, help="Calea unde se salveaza level.json")
    args = parser.parse_args()

    # Mapez textul primit de la Unity la enum-ul din proiect
    diff_map = {
        "easy": Difficulty.EASY,
        "medium": Difficulty.MEDIUM,
        "hard": Difficulty.HARD
    }
    difficulty_enum = diff_map.get(args.difficulty.lower(), Difficulty.MEDIUM)

    print(f"Generare nivelul {args.difficulty.upper()} folosind algoritmul genetic")

    # Rulez algoritmul genetic cu parametrii primiti din Unity
    ga_result = run_for_difficulty(
        difficulty=difficulty_enum,
        population_size=args.population,
        generations=args.generations,
        seed=None  # Fara seed fix ca sa genereze harti diferite de fiecare data
    )

    best_map = ga_result.best
    print(f"Harta generata cu succes! Fitness: {best_map.fitness:.4f}")

    # Exportez direct la calea ceruta de Unity
    export_json.save_level_json(
        path=args.export,
        grid=best_map.grid,
        result=best_map.result,
        difficulty=difficulty_enum
    )
    print(f"Fisier salvat la: {args.export}")

if __name__ == "__main__":
    main()