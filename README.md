# AI Escape Room Generator

Generator procedural de niveluri pentru un joc de tip Escape Room. Python
genereaza si valideaza nivelurile (labirint + BFS + scor de dificultate +
algoritm genetic), Unity le randeaza si le face jucabile.

## Structura

- `src/` - generator, BFS, scor de dificultate, algoritm genetic (Python)
- `unity/` - proiectul Unity (front-end)
- `tests/` - teste Python

## Setup

```bash
git clone https://github.com/mvriivs/ai-escape-room-generator.git
cd ai-escape-room-generator
pip install -r requirements.txt
```

Deschide folderul `unity/` in Unity Hub (versiunea 6000.5.3f1).

## Rulare

```bash
python src/main.py --difficulty medium
python src/run_genetic.py --difficulty hard
```

In Unity: apasa Play. WASD/sageti = miscare, +/- = zoom, L = reincarca
nivelul, N = nivel nou. Dificultatea se alege din Inspector (LevelRenderer)
sau din butoanele din HUD.

## Cum functioneaza

Python genereaza un labirint fara bucle, pune Start/Cheie/Usa/Iesire +
inamici/capcane/comori, valideaza cu BFS ca traseul chiar trece prin Cheie
si Usa (nu doar ca exista o cale), si calculeaza un scor de dificultate.
Algoritmul genetic cauta parametrii al caror scor e cel mai aproape de o
tinta ceruta. Rezultatul e exportat ca JSON, pe care Unity il citeste si il
randeaza -- Unity nu genereaza si nu valideaza nimic singur.

## Teste

```bash
python tests/test_solver.py
python tests/test_difficulty.py
python tests/test_genetic.py
```
