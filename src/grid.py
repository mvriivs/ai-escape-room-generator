"""
Reprezentarea unei harti (grid) pentru un nivel de Escape Room.

Fiecare celula are un tip (perete, podea, start, cheie, usa, exit etc.).
Grila e stocata ca o lista de liste, indexata [y][x].
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple


class Cell(Enum):
    WALL = "#"
    FLOOR = "."
    START = "S"
    KEY = "K"
    DOOR = "D"
    EXIT = "E"
    ENEMY = "X"
    TRAP = "T"
    TREASURE = "$"

    def __str__(self) -> str:
        return self.value


# Celule prin care se poate trece la parcurgerea grafului (pentru BFS).
# Peretii sunt singurele celule blocate; restul sunt "walkable".
WALKABLE = {
    Cell.FLOOR,
    Cell.START,
    Cell.KEY,
    Cell.DOOR,
    Cell.EXIT,
    Cell.ENEMY,
    Cell.TRAP,
    Cell.TREASURE,
}


class Position(NamedTuple):
    x: int
    y: int


class Grid:
    def __init__(self, width: int, height: int, fill: Cell = Cell.FLOOR):
        self.width = width
        self.height = height
        self._cells: list[list[Cell]] = [
            [fill for _ in range(width)] for _ in range(height)
        ]

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def get(self, pos: Position) -> Cell:
        return self._cells[pos.y][pos.x]

    def set(self, pos: Position, cell: Cell) -> None:
        self._cells[pos.y][pos.x] = cell

    def is_walkable(self, pos: Position) -> bool:
        return self.in_bounds(pos) and self.get(pos) in WALKABLE

    def neighbors(self, pos: Position) -> list[Position]:
        candidates = [
            Position(pos.x + 1, pos.y),
            Position(pos.x - 1, pos.y),
            Position(pos.x, pos.y + 1),
            Position(pos.x, pos.y - 1),
        ]
        return [p for p in candidates if self.in_bounds(p)]

    def find(self, cell_type: Cell) -> Position | None:
        """Returneaza prima pozitie care contine un anumit tip de celula."""
        for y in range(self.height):
            for x in range(self.width):
                if self._cells[y][x] == cell_type:
                    return Position(x, y)
        return None

    def count(self, cell_type: Cell) -> int:
        return sum(row.count(cell_type) for row in self._cells)

    def render(self) -> str:
        return "\n".join("".join(str(c) for c in row) for row in self._cells)

    def __str__(self) -> str:
        return self.render()
