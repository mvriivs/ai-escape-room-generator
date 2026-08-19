"""Teste de baza pentru BFS si validarea nivelurilor."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from grid import Cell, Grid, Position
from solver import bfs_shortest_path, validate_level


def make_simple_valid_grid() -> Grid:
    # 5x1: S . K . nimic -> facem un grid 4x1 simplu S K D E pe un rand liber
    grid = Grid(4, 1, fill=Cell.FLOOR)
    grid.set(Position(0, 0), Cell.START)
    grid.set(Position(1, 0), Cell.KEY)
    grid.set(Position(2, 0), Cell.DOOR)
    grid.set(Position(3, 0), Cell.EXIT)
    return grid


def test_bfs_finds_path_on_open_grid():
    grid = Grid(3, 3, fill=Cell.FLOOR)
    path = bfs_shortest_path(grid, Position(0, 0), Position(2, 2))
    assert path is not None
    assert path[0] == Position(0, 0)
    assert path[-1] == Position(2, 2)
    assert len(path) == 5  # drum Manhattan minim intr-o grila goala 3x3


def test_bfs_blocked_by_wall():
    grid = Grid(3, 1, fill=Cell.FLOOR)
    grid.set(Position(1, 0), Cell.WALL)
    path = bfs_shortest_path(grid, Position(0, 0), Position(2, 0))
    assert path is None


def test_validate_level_valid_case():
    grid = make_simple_valid_grid()
    result = validate_level(grid)
    assert result.is_valid
    assert result.total_length == 3  # 3 pasi: S->K->D->E pe un rand de 4 celule


def test_validate_level_missing_cells():
    grid = Grid(3, 3, fill=Cell.FLOOR)
    result = validate_level(grid)
    assert not result.is_valid
    assert "Lipsesc" in result.reason


def test_validate_level_unreachable():
    grid = make_simple_valid_grid()
    # blocam complet accesul intre Key si Door adaugand pereti pe un grid mai mare
    grid = Grid(5, 1, fill=Cell.WALL)
    grid.set(Position(0, 0), Cell.START)
    grid.set(Position(1, 0), Cell.KEY)
    # celula 2 ramane WALL -> blocheaza drumul spre Door
    grid.set(Position(3, 0), Cell.DOOR)
    grid.set(Position(4, 0), Cell.EXIT)
    result = validate_level(grid)
    assert not result.is_valid


def test_validate_level_rejects_door_bypass():
    # grid 3x3 unde Door NU e obligatorie: se poate ajunge la Exit si pe
    # randul de jos, ocolind complet usa de pe randul de mijloc.
    #   S K .
    #   . D .
    #   . . E   <- E accesibil si prin coltul din stanga-jos, fara sa treci de D
    grid = Grid(3, 3, fill=Cell.FLOOR)
    grid.set(Position(0, 0), Cell.START)
    grid.set(Position(1, 0), Cell.KEY)
    grid.set(Position(1, 1), Cell.DOOR)
    grid.set(Position(2, 2), Cell.EXIT)

    result = validate_level(grid)
    assert not result.is_valid
    assert "ocoleste" in result.reason


if __name__ == "__main__":
    # rulare simpla fara pytest, ca fallback
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"OK  {t.__name__}")
    print(f"\n{passed}/{len(tests)} teste trecute")
