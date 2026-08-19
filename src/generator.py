"""
Generare procedurala de niveluri.

Nivelul e construit ca un LABIRINT PERFECT (spanning tree, generat prin
randomized DFS / "recursive backtracker") -- adica exista exact UN singur
drum posibil intre oricare doua celule, fara bucle.

De ce un labirint perfect si nu pereti random: cu pereti aruncati random,
aproape mereu exista si un drum "ocolitor" care sare peste Cheie sau peste
Usa -- testat empiric, sub 10% din nivelurile random treceau validarea
stricta (vezi solver.validate_level). Intr-un labirint perfect insa, orice
celula de pe traseul unic Start->Exit este AUTOMAT un punct obligatoriu
(scoaterea ei rupe arborele in doua) -- deci punand Cheia si Usa pe acel
traseu, obligativitatea e garantata prin constructie, nu prin sansa.

Start/Exit se aleg ca cele doua capete ale celui mai lung traseu din
labirint (tehnica "dublu BFS" pentru diametrul unui arbore), iar Cheia/Usa
se plaseaza la ~1/3 si ~2/3 pe acel traseu. Inamici/capcane/comori se
imprastie pe restul celulelor libere (in afara traseului critic), cu
densitate crescand cu dificultatea.

Aici se va conecta mai tarziu algoritmul genetic, care va ajusta pozitiile
lor (si eventual structura labirintului) ca sa corespunda unui scor de
dificultate cerut de utilizator.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from enum import Enum

from grid import Cell, Grid, Position
from solver import ValidationResult, validate_level


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class DifficultyParams:
    cells_x: int  # numar de celule "vizitabile" pe orizontala
    cells_y: int  # numar de celule "vizitabile" pe verticala
    enemy_count: int
    trap_count: int
    treasure_count: int


DIFFICULTY_PRESETS: dict[Difficulty, DifficultyParams] = {
    Difficulty.EASY: DifficultyParams(cells_x=5, cells_y=5, enemy_count=1, trap_count=1, treasure_count=2),
    Difficulty.MEDIUM: DifficultyParams(cells_x=7, cells_y=7, enemy_count=3, trap_count=3, treasure_count=3),
    Difficulty.HARD: DifficultyParams(cells_x=10, cells_y=10, enemy_count=6, trap_count=6, treasure_count=4),
}


def _generate_maze(cells_x: int, cells_y: int, rng: random.Random) -> Grid:
    """Labirint perfect prin randomized DFS iterativ (recursive backtracker).
    Fiecare "celula vizitabila" (cx, cy) ocupa pozitia grid (2*cx+1, 2*cy+1);
    intre celule adiacente vizitate consecutiv se sparge peretele dintre ele.
    Grid-ul final are dimensiunea (2*cells_x+1) x (2*cells_y+1)."""
    width = 2 * cells_x + 1
    height = 2 * cells_y + 1
    grid = Grid(width, height, fill=Cell.WALL)

    def cell_pos(cx: int, cy: int) -> Position:
        return Position(2 * cx + 1, 2 * cy + 1)

    visited = [[False] * cells_x for _ in range(cells_y)]
    start_cx, start_cy = rng.randrange(cells_x), rng.randrange(cells_y)
    visited[start_cy][start_cx] = True
    grid.set(cell_pos(start_cx, start_cy), Cell.FLOOR)
    stack = [(start_cx, start_cy)]

    while stack:
        cx, cy = stack[-1]
        candidates = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cells_x and 0 <= ny < cells_y and not visited[ny][nx]:
                candidates.append((nx, ny, dx, dy))

        if not candidates:
            stack.pop()
            continue

        nx, ny, dx, dy = rng.choice(candidates)
        wall_between = Position(2 * cx + 1 + dx, 2 * cy + 1 + dy)
        grid.set(wall_between, Cell.FLOOR)
        grid.set(cell_pos(nx, ny), Cell.FLOOR)
        visited[ny][nx] = True
        stack.append((nx, ny))

    return grid


def _farthest_position(grid: Grid, from_pos: Position) -> Position:
    """BFS de la from_pos; ultima celula scoasa din coada e la distanta
    maxima (BFS proceseaza celulele in ordinea crescatoare a distantei)."""
    visited = {from_pos}
    queue = deque([from_pos])
    farthest = from_pos
    while queue:
        current = queue.popleft()
        farthest = current
        for nxt in grid.neighbors(current):
            if nxt not in visited and grid.is_walkable(nxt):
                visited.add(nxt)
                queue.append(nxt)
    return farthest


def _longest_path(grid: Grid, rng: random.Random) -> list[Position]:
    """Diametrul labirintului (cel mai lung traseu), prin tehnica "dublu
    BFS": pornim dintr-o celula oarecare, gasim cea mai indepartata (A),
    apoi cea mai indepartata fata de A (B) -- A si B sunt capetele
    traseului maxim intr-un arbore."""
    from solver import bfs_shortest_path

    floor_cells = [
        Position(x, y)
        for y in range(grid.height)
        for x in range(grid.width)
        if grid.get(Position(x, y)) == Cell.FLOOR
    ]
    seed_pos = rng.choice(floor_cells)
    a = _farthest_position(grid, seed_pos)
    b = _farthest_position(grid, a)
    return bfs_shortest_path(grid, a, b) or [a]


def _scatter_content(
    grid: Grid, rng: random.Random, exclude: set[Position], counts: dict[Cell, int]
) -> None:
    """Imprastie inamici/capcane/comori pe celule FLOOR libere, in afara
    traseului critic (exclude), ca sa nu afecteze solvabilitatea."""
    free_cells = [
        Position(x, y)
        for y in range(grid.height)
        for x in range(grid.width)
        if grid.get(Position(x, y)) == Cell.FLOOR and Position(x, y) not in exclude
    ]
    rng.shuffle(free_cells)

    idx = 0
    for cell_type, count in counts.items():
        for _ in range(count):
            if idx >= len(free_cells):
                return
            grid.set(free_cells[idx], cell_type)
            idx += 1


def generate_level(
    difficulty: Difficulty, seed: int | None = None, max_attempts: int = 20
) -> tuple[Grid, ValidationResult]:
    """Genereaza un nivel pentru dificultatea data. Fiind construit ca
    labirint perfect, e valid aproape mereu din prima -- max_attempts e doar
    o plasa de siguranta (ex. labirinturi minuscule unde traseul e prea
    scurt ca sa incapa Cheie + Usa distincte)."""
    params = DIFFICULTY_PRESETS[difficulty]

    result: ValidationResult | None = None
    grid: Grid | None = None

    for attempt in range(max_attempts):
        attempt_seed = None if seed is None else seed * 1_000_003 + attempt
        rng = random.Random(attempt_seed)

        grid = _generate_maze(params.cells_x, params.cells_y, rng)
        path = _longest_path(grid, rng)

        if len(path) < 4:
            continue  # traseu prea scurt ca sa incapa S, K, D, E distincte

        start = path[0]
        exit_ = path[-1]
        key = path[max(1, len(path) // 3)]
        door = path[min(len(path) - 2, (2 * len(path)) // 3)]
        if len({start, key, door, exit_}) < 4:
            continue

        grid.set(start, Cell.START)
        grid.set(key, Cell.KEY)
        grid.set(door, Cell.DOOR)
        grid.set(exit_, Cell.EXIT)

        _scatter_content(
            grid,
            rng,
            exclude=set(path),
            counts={
                Cell.ENEMY: params.enemy_count,
                Cell.TRAP: params.trap_count,
                Cell.TREASURE: params.treasure_count,
            },
        )

        result = validate_level(grid)
        if result.is_valid:
            return grid, result

    return grid, result
