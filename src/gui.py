"""
Vizualizare grafica (Pygame) pentru un nivel generat.

Deseneaza grila cu tile-uri rotunjite, umbre si iconite vectoriale pentru
fiecare tip de celula, plus un panou lateral cu legenda si statusul
validarii.

Apasa R pentru a genera un nivel nou (aceeasi dificultate), Esc pentru iesire.

Exemplu de rulare:
    python src/gui.py --difficulty medium
    python src/gui.py --difficulty hard --seed 42
"""

from __future__ import annotations

import argparse
import math

import pygame

from generator import Difficulty, generate_level
from grid import Cell, Grid, Position

TILE = 46
GAP = 4
PADDING = 16
SIDEBAR_W = 250

# --- paleta de culori (tema intunecata, tip "dungeon") -------------------
BG_TOP = (22, 24, 38)
BG_BOTTOM = (12, 13, 22)
PANEL_BG = (28, 30, 46)
PANEL_BORDER = (52, 55, 78)

WALL_COLOR = (46, 48, 66)
WALL_LINE = (34, 36, 52)
FLOOR_COLOR = (223, 217, 200)
FLOOR_SHADOW = (198, 192, 176)

START_COLOR = (66, 145, 235)
KEY_COLOR = (240, 195, 60)
DOOR_COLOR = (150, 92, 52)
DOOR_DARK = (108, 64, 34)
EXIT_COLOR = (66, 191, 119)
ENEMY_COLOR = (220, 68, 68)
TRAP_COLOR = (167, 68, 191)
TREASURE_COLOR = (240, 165, 40)

TEXT_MAIN = (235, 235, 240)
TEXT_DIM = (150, 152, 170)
OK_COLOR = (90, 210, 140)
BAD_COLOR = (230, 90, 90)

TILE_COLORS = {
    Cell.WALL: WALL_COLOR,
    Cell.FLOOR: FLOOR_COLOR,
    Cell.START: FLOOR_COLOR,
    Cell.KEY: FLOOR_COLOR,
    Cell.DOOR: FLOOR_COLOR,
    Cell.EXIT: FLOOR_COLOR,
    Cell.ENEMY: FLOOR_COLOR,
    Cell.TRAP: FLOOR_COLOR,
    Cell.TREASURE: FLOOR_COLOR,
}

LEGEND_ITEMS = [
    (Cell.START, "Start", START_COLOR),
    (Cell.KEY, "Cheie", KEY_COLOR),
    (Cell.DOOR, "Usa", DOOR_COLOR),
    (Cell.EXIT, "Iesire", EXIT_COLOR),
    (Cell.WALL, "Perete", WALL_COLOR),
    (Cell.FLOOR, "Podea", FLOOR_COLOR),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Escape Room Generator - vizualizare Pygame")
    parser.add_argument(
        "--difficulty",
        choices=[d.value for d in Difficulty],
        default=Difficulty.EASY.value,
    )
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def vertical_gradient(surface: pygame.Surface, top: tuple, bottom: tuple) -> None:
    height = surface.get_height()
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surface, color, (0, y), (surface.get_width(), y))


def draw_tile_base(screen: pygame.Surface, rect: pygame.Rect, cell: Cell) -> None:
    """Deseneaza fundalul tile-ului (cu umbra) inainte de iconita."""
    shadow_rect = rect.move(0, 3)
    pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=10)

    base_color = TILE_COLORS[cell]
    pygame.draw.rect(screen, base_color, rect, border_radius=10)

    if cell == Cell.WALL:
        # textura simpla de "caramida": doua linii orizontale mai inchise
        for frac in (0.35, 0.7):
            y = rect.y + int(rect.height * frac)
            pygame.draw.line(screen, WALL_LINE, (rect.x + 4, y), (rect.right - 4, y), 2)
    else:
        # podea: un contur usor mai inchis pentru profunzime
        pygame.draw.rect(screen, FLOOR_SHADOW, rect, width=1, border_radius=10)


def draw_start_icon(screen: pygame.Surface, rect: pygame.Rect) -> None:
    cx, cy = rect.center
    r = rect.width // 3
    pygame.draw.circle(screen, START_COLOR, (cx, cy), r)
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), r, width=2)
    # sageata mica in interior, sugereaza "start / player"
    tip = (cx + r // 2, cy)
    pygame.draw.polygon(
        screen,
        (255, 255, 255),
        [(cx - r // 3, cy - r // 2), (cx - r // 3, cy + r // 2), tip],
    )


def draw_key_icon(screen: pygame.Surface, rect: pygame.Rect) -> None:
    cx, cy = rect.center
    ring_r = rect.width // 6
    ring_center = (cx - rect.width // 6, cy)
    pygame.draw.circle(screen, KEY_COLOR, ring_center, ring_r, width=4)
    shaft_start = (ring_center[0] + ring_r, cy)
    shaft_end = (rect.right - rect.width // 5, cy)
    pygame.draw.line(screen, KEY_COLOR, shaft_start, shaft_end, 4)
    pygame.draw.line(screen, KEY_COLOR, shaft_end, (shaft_end[0], shaft_end[1] + 6), 4)
    pygame.draw.line(
        screen, KEY_COLOR, (shaft_end[0] - 6, shaft_end[1]), (shaft_end[0] - 6, shaft_end[1] + 5), 4
    )


def draw_door_icon(screen: pygame.Surface, rect: pygame.Rect) -> None:
    door_rect = rect.inflate(-14, -10)
    pygame.draw.rect(screen, DOOR_COLOR, door_rect, border_radius=4)
    pygame.draw.rect(screen, DOOR_DARK, door_rect, width=2, border_radius=4)
    pygame.draw.line(
        screen, DOOR_DARK, (door_rect.centerx, door_rect.top + 3), (door_rect.centerx, door_rect.bottom - 3), 2
    )
    knob = (door_rect.centerx + 5, door_rect.centery)
    pygame.draw.circle(screen, (250, 220, 120), knob, 3)


def draw_exit_icon(screen: pygame.Surface, rect: pygame.Rect) -> None:
    frame = rect.inflate(-12, -12)
    pygame.draw.rect(screen, EXIT_COLOR, frame, border_radius=6)
    cx, cy = frame.center
    # sageata alba spre exterior
    pygame.draw.line(screen, (255, 255, 255), (cx - 7, cy), (cx + 7, cy), 3)
    pygame.draw.polygon(
        screen,
        (255, 255, 255),
        [(cx + 3, cy - 6), (cx + 3, cy + 6), (cx + 11, cy)],
    )


def draw_enemy_icon(screen: pygame.Surface, rect: pygame.Rect) -> None:
    cx, cy = rect.center
    r = rect.width // 3
    pygame.draw.circle(screen, ENEMY_COLOR, (cx, cy), r)
    for dx in (-r // 2, r // 2):
        pygame.draw.circle(screen, (255, 255, 255), (cx + dx, cy - r // 4), 3)


def draw_trap_icon(screen: pygame.Surface, rect: pygame.Rect) -> None:
    cx, cy = rect.center
    r = rect.width // 4
    pygame.draw.line(screen, TRAP_COLOR, (cx - r, cy - r), (cx + r, cy + r), 4)
    pygame.draw.line(screen, TRAP_COLOR, (cx - r, cy + r), (cx + r, cy - r), 4)


def draw_treasure_icon(screen: pygame.Surface, rect: pygame.Rect) -> None:
    chest = rect.inflate(-14, -14)
    pygame.draw.rect(screen, TREASURE_COLOR, chest, border_radius=4)
    band = pygame.Rect(chest.x, chest.centery - 2, chest.width, 4)
    pygame.draw.rect(screen, (180, 120, 20), band)
    pygame.draw.circle(screen, (180, 120, 20), chest.center, 3)


ICON_DRAWERS = {
    Cell.START: draw_start_icon,
    Cell.KEY: draw_key_icon,
    Cell.DOOR: draw_door_icon,
    Cell.EXIT: draw_exit_icon,
    Cell.ENEMY: draw_enemy_icon,
    Cell.TRAP: draw_trap_icon,
    Cell.TREASURE: draw_treasure_icon,
}


def draw_grid(screen: pygame.Surface, grid: Grid, origin: tuple[int, int]) -> None:
    ox, oy = origin
    for y in range(grid.height):
        for x in range(grid.width):
            cell = grid.get(Position(x, y))
            rect = pygame.Rect(
                ox + x * (TILE + GAP), oy + y * (TILE + GAP), TILE, TILE
            )
            draw_tile_base(screen, rect, cell)
            drawer = ICON_DRAWERS.get(cell)
            if drawer:
                drawer(screen, rect)


def draw_text(screen, font, text, pos, color=TEXT_MAIN):
    surf = font.render(text, True, color)
    screen.blit(surf, pos)
    return surf.get_height()


def draw_sidebar(
    screen: pygame.Surface,
    panel_rect: pygame.Rect,
    fonts: dict,
    difficulty: Difficulty,
    result,
) -> None:
    pygame.draw.rect(screen, PANEL_BG, panel_rect)
    pygame.draw.line(
        screen, PANEL_BORDER, (panel_rect.x, 0), (panel_rect.x, panel_rect.height), 2
    )

    x = panel_rect.x + 20
    y = 24

    y += draw_text(screen, fonts["title"], "Escape Room", (x, y)) + 2
    y += draw_text(screen, fonts["small"], "generat procedural", (x, y), TEXT_DIM) + 18

    y += draw_text(screen, fonts["label"], "Dificultate", (x, y), TEXT_DIM) + 2
    y += draw_text(screen, fonts["value"], difficulty.value.capitalize(), (x, y)) + 18

    y += draw_text(screen, fonts["label"], "Status", (x, y), TEXT_DIM) + 4
    dot_color = OK_COLOR if result.is_valid else BAD_COLOR
    pygame.draw.circle(screen, dot_color, (x + 6, y + 8), 6)
    status_text = "Valid" if result.is_valid else "Invalid"
    draw_text(screen, fonts["value"], status_text, (x + 20, y))
    y += 26

    if result.is_valid:
        y += draw_text(screen, fonts["label"], "Traseu optim", (x, y), TEXT_DIM) + 2
        y += draw_text(screen, fonts["value"], f"{result.total_length} pasi", (x, y)) + 18
    else:
        y += 4
        reason_surf = fonts["small"].render(result.reason, True, BAD_COLOR)
        screen.blit(reason_surf, (x, y))
        y += reason_surf.get_height() + 18

    y += 6
    pygame.draw.line(screen, PANEL_BORDER, (x, y), (panel_rect.right - 20, y), 1)
    y += 18

    y += draw_text(screen, fonts["label"], "Legenda", (x, y), TEXT_DIM) + 10
    swatch = 22
    for cell, label, color in LEGEND_ITEMS:
        rect = pygame.Rect(x, y, swatch, swatch)
        draw_tile_base(screen, rect, cell)
        drawer = ICON_DRAWERS.get(cell)
        if drawer:
            drawer(screen, rect)
        draw_text(screen, fonts["value"], label, (x + swatch + 10, y + 3))
        y += swatch + 8

    y = panel_rect.bottom - 70
    pygame.draw.line(screen, PANEL_BORDER, (x, y), (panel_rect.right - 20, y), 1)
    y += 14
    draw_text(screen, fonts["small"], "R  regenereaza nivel", (x, y), TEXT_DIM)
    y += 20
    draw_text(screen, fonts["small"], "Esc  iesire", (x, y), TEXT_DIM)


def build_fonts() -> dict:
    return {
        "title": pygame.font.SysFont("segoeuisemibold", 26),
        "label": pygame.font.SysFont("segoeui", 14),
        "value": pygame.font.SysFont("segoeuisemibold", 18),
        "small": pygame.font.SysFont("segoeui", 14),
    }


def compute_window_size(grid: Grid) -> tuple[int, int, tuple[int, int]]:
    grid_w = grid.width * (TILE + GAP) - GAP
    grid_h = grid.height * (TILE + GAP) - GAP
    width = PADDING * 2 + grid_w + SIDEBAR_W
    height = max(PADDING * 2 + grid_h, 380)
    origin = (PADDING, PADDING)
    return width, height, origin


def run(difficulty: Difficulty, seed: int | None) -> None:
    grid, result = generate_level(difficulty, seed=seed)

    pygame.init()
    pygame.display.set_caption("AI Escape Room Generator")
    width, height, origin = compute_window_size(grid)
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    fonts = build_fonts()

    bg = pygame.Surface((width, height))
    vertical_gradient(bg, BG_TOP, BG_BOTTOM)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    grid, result = generate_level(difficulty, seed=None)
                    width, height, origin = compute_window_size(grid)
                    screen = pygame.display.set_mode((width, height))
                    bg = pygame.Surface((width, height))
                    vertical_gradient(bg, BG_TOP, BG_BOTTOM)

        screen.blit(bg, (0, 0))
        draw_grid(screen, grid, origin)

        panel_rect = pygame.Rect(width - SIDEBAR_W, 0, SIDEBAR_W, height)
        draw_sidebar(screen, panel_rect, fonts, difficulty, result)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


def main() -> None:
    args = parse_args()
    run(Difficulty(args.difficulty), args.seed)


if __name__ == "__main__":
    main()
