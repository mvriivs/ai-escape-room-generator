"""
Export al unui nivel generat catre un fisier JSON, ca sa poata fi citit de
front-end-ul Unity (Python ramane "creierul": genereaza + valideaza +,
ulterior, optimizeaza cu algoritmul genetic; Unity doar randeaza rezultatul).

Format JSON (structura plata, fara liste imbricate/null - compatibila direct
cu JsonUtility din Unity, fara pachete suplimentare gen Newtonsoft):
{
  "difficulty": "medium",
  "width": 12,
  "height": 12,
  "cells": ["#", ".", "S", ...],   // flat, randuri concatenate: cells[y*width+x]
  "is_valid": true,
  "path_length": 17,
  "reason": "Nivel valid",
  "start_x": 5, "start_y": 6,
  "key_x": 3, "key_y": 3,
  "door_x": 2, "door_y": 8,
  "exit_x": 0, "exit_y": 11,
  "difficulty_score": 111.4,
  "difficulty_category": "medium",
  "enemy_count": 3, "trap_count": 3, "treasure_count": 3,
  "wall_density_pct": 42.0
}
"""

from __future__ import annotations

import json
from pathlib import Path

from difficulty import DifficultyScore, compute_difficulty_score
from generator import Difficulty
from grid import Cell, Grid, Position
from solver import ValidationResult


def level_to_dict(grid: Grid, result: ValidationResult, difficulty: Difficulty) -> dict:
    cells = [
        str(grid.get(Position(x, y)))
        for y in range(grid.height)
        for x in range(grid.width)
    ]

    data = {
        "difficulty": difficulty.value,
        "width": grid.width,
        "height": grid.height,
        "cells": cells,
        "is_valid": result.is_valid,
        "path_length": result.total_length,
        "reason": result.reason,
    }

    score: DifficultyScore | None = compute_difficulty_score(grid, result) if result.is_valid else None
    data["difficulty_score"] = score.raw_score if score else 0.0
    data["difficulty_category"] = score.category if score else "n/a"
    data["enemy_count"] = score.enemy_count if score else grid.count(Cell.ENEMY)
    data["trap_count"] = score.trap_count if score else grid.count(Cell.TRAP)
    data["treasure_count"] = score.treasure_count if score else grid.count(Cell.TREASURE)
    data["wall_density_pct"] = round((score.wall_density if score else 0.0) * 100, 1)

    for name, cell_type in (
        ("start", Cell.START),
        ("key", Cell.KEY),
        ("door", Cell.DOOR),
        ("exit", Cell.EXIT),
    ):
        pos = grid.find(cell_type)
        data[f"{name}_x"] = pos.x if pos else -1
        data[f"{name}_y"] = pos.y if pos else -1

    return data


def save_level_json(
    path: str | Path, grid: Grid, result: ValidationResult, difficulty: Difficulty
) -> None:
    data = level_to_dict(grid, result, difficulty)
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
