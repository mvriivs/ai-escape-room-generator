"""
Validare de nivel folosind Breadth-First Search (BFS).

Verifica daca exista un traseu valid:
    Start -> Key -> Door -> Exit

BFS gaseste, pentru fiecare segment, cel mai scurt drum intre doua puncte
pe grid (folosind doar celule "walkable" - fara pereti).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from grid import Grid, Position


def bfs_shortest_path(
    grid: Grid,
    start: Position,
    goal: Position,
    avoid: frozenset[Position] = frozenset(),
) -> list[Position] | None:
    """Returneaza cel mai scurt drum (lista de pozitii) de la start la goal,
    sau None daca nu exista traseu. `avoid` sunt celule tratate ca pereti in
    plus fata de peretii reali -- folosit ca sa verificam daca un traseu
    OCOLESTE un punct obligatoriu (Cheie/Usa)."""
    if not grid.is_walkable(start) or not grid.is_walkable(goal):
        return None
    if start in avoid or goal in avoid:
        return None
    if start == goal:
        return [start]

    visited = {start}
    parent: dict[Position, Position] = {}
    queue = deque([start])

    while queue:
        current = queue.popleft()
        if current == goal:
            return _reconstruct_path(parent, start, goal)

        for nxt in grid.neighbors(current):
            if nxt in visited or nxt in avoid:
                continue
            if grid.is_walkable(nxt):
                visited.add(nxt)
                parent[nxt] = current
                queue.append(nxt)

    return None


def _reconstruct_path(
    parent: dict[Position, Position], start: Position, goal: Position
) -> list[Position]:
    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    return path


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str = ""
    start_to_key: list[Position] | None = None
    key_to_door: list[Position] | None = None
    door_to_exit: list[Position] | None = None

    @property
    def total_length(self) -> int:
        """Lungimea totala a traseului optim (numar de pasi)."""
        segments = [self.start_to_key, self.key_to_door, self.door_to_exit]
        return sum(len(seg) - 1 for seg in segments if seg)


def validate_level(grid: Grid) -> ValidationResult:
    """Verifica daca nivelul e rezolvabil: exista traseu S -> K -> D -> E,
    parcurs in aceasta ordine."""
    from grid import Cell

    start = grid.find(Cell.START)
    key = grid.find(Cell.KEY)
    door = grid.find(Cell.DOOR)
    exit_ = grid.find(Cell.EXIT)

    missing = [
        name
        for name, pos in [("Start", start), ("Key", key), ("Door", door), ("Exit", exit_)]
        if pos is None
    ]
    if missing:
        return ValidationResult(False, reason=f"Lipsesc celule obligatorii: {', '.join(missing)}")

    path1 = bfs_shortest_path(grid, start, key)
    if path1 is None:
        return ValidationResult(False, reason="Nu exista drum de la Start la Key")

    path2 = bfs_shortest_path(grid, key, door)
    if path2 is None:
        return ValidationResult(False, reason="Nu exista drum de la Key la Door")

    path3 = bfs_shortest_path(grid, door, exit_)
    if path3 is None:
        return ValidationResult(False, reason="Nu exista drum de la Door la Exit")

    # Cheia si Usa trebuie sa fie OBLIGATORII, nu doar "pe un traseu posibil":
    # daca exista un drum alternativ care le ocoleste, jucatorul poate ajunge
    # la Usa fara Cheie (blocaj) sau la Exit fara Usa (mecanica fara sens).
    bypass_key = bfs_shortest_path(grid, start, door, avoid=frozenset({key}))
    if bypass_key is not None:
        return ValidationResult(
            False, reason="Exista un drum spre Usa care ocoleste Cheia (cheia nu e obligatorie)"
        )

    bypass_door = bfs_shortest_path(grid, start, exit_, avoid=frozenset({door}))
    if bypass_door is not None:
        return ValidationResult(
            False, reason="Exista un drum spre Exit care ocoleste Usa (usa nu e obligatorie)"
        )

    return ValidationResult(
        True,
        reason="Nivel valid",
        start_to_key=path1,
        key_to_door=path2,
        door_to_exit=path3,
    )
