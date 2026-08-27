import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from baseline_fitness import baseline_linear_fitness
from difficulty import DifficultyScore

def test_baseline_fitness_perfect_match():
    # tinta pt easy e 60.0
    # creez un scor fictiv de fix 60.0
    mock_score = DifficultyScore(
        path_length=10, enemy_count=1, trap_count=1, 
        treasure_count=1, wall_density=0.3, dead_end_ratio=0.1, 
        raw_score=60.0 
    )
    
    fitness = baseline_linear_fitness(mock_score, "easy")
    
    # ar trebui sa fie o potrivire de 100%
    assert fitness == 1.0, f"Fitness-ul trebuia sa fie 1.0, dar este {fitness}"

def test_baseline_fitness_partial_match():
    # tinta pt easy este 60.0 si creez un scor de 30.0
    # eroarea este 30
    # 30 / 60 = 0.5 (50% eroare)
    mock_score = DifficultyScore(
        path_length=5, enemy_count=0, trap_count=0, 
        treasure_count=0, wall_density=0.1, dead_end_ratio=0.0, 
        raw_score=30.0
    )
    
    fitness = baseline_linear_fitness(mock_score, "easy")
    
    # fitness-ul ar trebui sa fie scazut cu 50%
    assert fitness == 0.5, f"Fitness-ul trebuia sa fie 0.5, dar este {fitness}"

def test_baseline_fitness_zero_match():
    # tinta pt easy este 60.0 si dau un scor de 200.0 (specific pt "hard").
    # eroarea este 140
    # 140 / 60 > 1.0 (eroare peste 100%)
    mock_score = DifficultyScore(
        path_length=40, enemy_count=6, trap_count=6, 
        treasure_count=4, wall_density=0.6, dead_end_ratio=0.4, 
        raw_score=200.0
    )
    
    fitness = baseline_linear_fitness(mock_score, "easy")
    
    # algoritmul ar trebui sa respinga complet aceasta harta pt easy
    assert fitness == 0.0, f"Fitness-ul trebuia să fie 0.0, dar este {fitness}"