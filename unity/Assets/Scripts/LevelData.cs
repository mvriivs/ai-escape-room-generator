using System;

// Structura plata, in oglinda cu ce exporta export_json.py din partea Python.
// JsonUtility din Unity nu suporta liste imbricate/null bine, de-asta grid-ul
// e trimis ca un singur array (randuri concatenate) in loc de array 2D.
[Serializable]
public class LevelData
{
    public string difficulty;
    public int width;
    public int height;
    public string[] cells; // flat, row-major: cells[y * width + x]
    public bool is_valid;
    public int path_length;
    public string reason;

    public int start_x, start_y;
    public int key_x, key_y;
    public int door_x, door_y;
    public int exit_x, exit_y;

    public float difficulty_score;
    public string difficulty_category;
    public int enemy_count, trap_count, treasure_count;
    public float wall_density_pct;
    public float dead_end_ratio_pct;

    public char CellAt(int x, int y)
    {
        string s = cells[y * width + x];
        return string.IsNullOrEmpty(s) ? '.' : s[0];
    }
}
