"""
Grafic cu evolutia fitness-ului algoritmului genetic.

Afiseaza:
    - cel mai bun fitness;
    - fitness-ul mediu al populatiei.

Graficul este salvat ca PNG.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from genetic import GAResult


def plot_fitness_history(
    ga_result: GAResult,
    out_path: str,
    title: str | None = None,
) -> None:

    generations = range(
        len(
            ga_result.best_fitness_history
        )
    )

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    ax.plot(
        generations,
        ga_result.best_fitness_history,
        label="Cel mai bun fitness",
        linewidth=2,
    )

    ax.plot(
        generations,
        ga_result.mean_fitness_history,
        label="Fitness mediu",
        linewidth=1.5,
        linestyle="--",
    )

    ax.set_xlabel(
        "Generatie"
    )

    ax.set_ylabel(
        "Fitness"
    )

    ax.set_title(
        title
        or (
            "Evolutia fitness-ului "
            f"(tinta = "
            f"{ga_result.target_score:.1f})"
        )
    )

    ax.legend()

    ax.grid(
        True,
        alpha=0.3,
    )

    fig.tight_layout()

    fig.savefig(
        out_path,
        dpi=140,
    )

    plt.close(fig)