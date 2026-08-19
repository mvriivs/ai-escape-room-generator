# AI Escape Room Generator

Generarea si optimizarea automata a nivelurilor pentru un joc de tip Escape
Room folosind algoritmi genetici si cautare BFS.

## Status implementare

- [x] Reprezentare grid (`src/grid.py`)
- [x] Generator procedural: labirint perfect (spanning tree) pe dificultati Easy/Medium/Hard (`src/generator.py`)
- [x] Validare nivel cu BFS: Start -> Key -> Door -> Exit, cu Cheia/Usa OBLIGATORII (nu doar posibile) (`src/solver.py`)
- [x] Plasare inamici / capcane / comori (in afara traseului critic)
- [x] **Scor de dificultate** (lungime traseu, nr. inamici, nr. capcane, nr. comori, densitate pereti), calibrat empiric (`src/difficulty.py`)
- [x] CLI text pentru generare + vizualizare (`src/main.py`)
- [x] Export JSON pentru front-end (`src/export_json.py`)
- [x] Front-end Unity 3D (randare + camera + lumina + tema de culori + textura proceduala) -- `unity/`
- [x] Personaj jucabil (miscare pe grid, WASD/sageti) cu interactiuni: cheie, usa, inamici/capcane (vieti), comori (scor)
- [x] Alegerea dificultatii direct din Unity (dropdown la Play sau butoane Easy/Medium/Hard in HUD)
- [x] Regenerare automata a unui nivel nou la victorie (Unity cheama Python ca subproces)
- [ ] **Algoritm genetic** (selectie, crossover, mutatie, elitism) care optimizeaza nivelul spre dificultatea ceruta
- [ ] **Grafic evolutie fitness** pe generatii (Matplotlib)
- [ ] NumPy -- folosit doar pentru scor deocamdata; va fi central in algoritmul genetic

## Arhitectura: Python = creierul, Unity = front-end-ul

Python genereaza nivelul, il valideaza cu BFS, calculeaza scorul de
dificultate si (in curand) il optimizeaza cu algoritmul genetic. Rezultatul
e exportat ca JSON. Unity doar citeste JSON-ul si il randeaza -- nu
genereaza si nu valideaza nimic singur.

```
ai-escape-room-generator/     <- radacina repo-ului (monorepo)
  src/                         <- Python: generator, BFS, scor de dificultate
  tests/                       <- teste Python
  unity/                       <- proiect Unity (front-end)
    Assets/Scripts/
      LevelData.cs             <- oglinda JSON-ului exportat din Python
      LevelRenderer.cs         <- randare 3D + cheama Python (subproces)
      LevelHUD.cs               <- overlay: status, legenda, butoane dificultate
      PlayerController.cs       <- miscare pe grid + interactiuni
      Bobber.cs                 <- animatie idle (plutire/rotatie)
    Assets/StreamingAssets/level.json   <- nivelul curent (generat, nu e sursa -- gitignored)
```

Unity gaseste automat folderul `src/` (presupune ca `unity/` si `src/` sunt
frati sub aceeasi radacina) si `python` din PATH -- nu sunt cai hardcodate.
Daca nu merge pe o masina noua, se pot suprascrie manual `pythonExecutable`
/ `pythonScriptDir` in Inspector, pe componenta `LevelRenderer`.

### Workflow

```bash
# 1. (optional -- Unity o face oricum automat la Play) genereaza si exporta manual un nivel
python src/main.py --difficulty medium --export unity/Assets/StreamingAssets/level.json

# 2. Deschide 'unity/' ca proiect in Unity Hub, apasa Play
#    (scena se creeaza automat -- nu trebuie configurat nimic manual)
#    Dificultatea se alege din Inspector (campul "Start Difficulty" pe
#    LevelRenderer) inainte de Play, sau din butoanele Easy/Medium/Hard din HUD.

# 3. In Play Mode: WASD/sageti = miscare, L = reincarca JSON-ul curent,
#    N = nivel nou (aceeasi dificultate), +/- = zoom
```

## Rulare (doar partea Python, fara Unity)

```bash
python src/main.py --difficulty easy
python src/main.py --difficulty medium --seed 42
python src/main.py --difficulty hard
```

## Teste

```bash
python tests/test_solver.py
python tests/test_difficulty.py
```

(sau, daca ai `pytest` instalat: `pytest tests/`)

## Legenda simboluri

| Simbol | Semnificatie |
|--------|--------------|
| `#`    | Perete       |
| `.`    | Podea liber  |
| `S`    | Start        |
| `K`    | Key (cheie)  |
| `D`    | Door (usa) -- blocata pana culegi cheia |
| `E`    | Exit         |
| `X`    | Inamic (te loveste: -1 viata, te trimite la Start) |
| `T`    | Capcana (la fel ca inamicul) |
| `$`    | Comoara (se aduna la scor) |

## Pasii urmatori

1. **Algoritm genetic**: populatie de niveluri (fiecare = un labirint +
   pozitii de inamici/capcane/comori), fitness = cat de aproape e scorul de
   dificultate (`src/difficulty.py`) de dificultatea tinta, apoi selectie +
   crossover + mutatie + elitism pe generatii, pana convergem la un nivel cu
   dificultatea dorita cu mai multa precizie decat generarea directa.
2. **Grafic Matplotlib** cu evolutia fitness-ului (best/media pe generatie) --
   fie salvat ca PNG, fie afisat live.
