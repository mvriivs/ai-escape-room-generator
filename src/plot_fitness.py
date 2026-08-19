"""
Grafic cu evolutia fitness-ului algoritmului genetic pe generatii
(cel mai bun individ + media populatiei), salvat ca PNG.

Backend "Agg" (headless) -- functioneaza si fara ecran/GUI, potrivit pentru
rulare din linia de comanda.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from genetic import GAResult


def plot_fitness_history(ga_result: GAResult, out_path: str, title: str | None = None) -> None:
    generations = range(len(ga_result.best_fitness_history))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(generations, ga_result.best_fitness_history, label="Cel mai bun fitness", color="#2a9d8f", linewidth=2)
    ax.plot(generations, ga_result.mean_fitness_history, label="Fitness mediu (populatie)", color="#e76f51", linewidth=1.5, linestyle="--")

    ax.set_xlabel("Generatie")
    ax.set_ylabel("Fitness (-|scor - scor tinta|, 0 = perfect)")
    ax.set_title(title or f"Evolutia fitness-ului (scor tinta = {ga_result.target_score:.1f})")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
