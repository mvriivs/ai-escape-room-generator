# in loc sa reevaluez fiecare inamic sau capcana, ma bazez pe raw_score
# apoi compar matematic cu tintele din CATEGORY_TARGET_SCORE si scad liniar din fitnessul maxim

from difficulty import DifficultyScore, CATEGORY_TARGET_SCORE

# functia de fitness liniara (baseline)
def baseline_linear_fitness(score: DifficultyScore, difficulty_name: str) -> float:
    # validez si extrag tinta 
    difficulty_key = difficulty_name.lower()
    if difficulty_key not in CATEGORY_TARGET_SCORE:
        raise ValueError(f"Dificultate necunoscuta: {difficulty_key}")
        
    target_score = CATEGORY_TARGET_SCORE[difficulty_key]
    
    # eroarea absoluta liniara
    error = abs(score.raw_score - target_score)
    
    # normalizare eroare in raport cu tinta
    error_ratio = error / target_score
    
    # fitness-ul final este diferenaa pana la 1.0 (limitat la minim 0.0)
    fitness = max(0.0, 1.0 - error_ratio)
    
    return float(fitness)