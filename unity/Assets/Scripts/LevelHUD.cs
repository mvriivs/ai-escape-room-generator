using System.Collections.Generic;
using UnityEngine;

// Overlay simplu (OnGUI) cu statusul nivelului si legenda. Separat de
// LevelRenderer ca sa poata fi inlocuit usor mai tarziu cu o UI Canvas
// "adevarata", fara sa umble in codul de randare.
[RequireComponent(typeof(LevelRenderer))]
public class LevelHUD : MonoBehaviour
{
    private LevelRenderer renderer_;
    private GUIStyle boxStyle;
    private GUIStyle labelStyle;
    private readonly Dictionary<Color, Texture2D> swatchCache = new Dictionary<Color, Texture2D>();

    void Awake()
    {
        renderer_ = GetComponent<LevelRenderer>();
    }

    void OnGUI()
    {
        LevelData data = renderer_.Current;
        if (data == null) return;

        EnsureStyles();

        GUILayout.BeginArea(new Rect(12, 12, 320, 440), boxStyle);
        GUILayout.Label($"Dificultate ceruta: {data.difficulty}", labelStyle);
        GUILayout.Label(data.is_valid ? $"Status: OK ({data.path_length} pasi)" : $"Status: INVALID", labelStyle);
        if (!data.is_valid)
        {
            GUILayout.Label(data.reason, labelStyle);
        }
        else
        {
            bool matches = data.difficulty_category == data.difficulty;
            string mark = matches ? "OK" : "diferit";
            GUILayout.Label($"Scor: {data.difficulty_score:F0} -> masurat '{data.difficulty_category}' ({mark})", labelStyle);
            GUILayout.Label($"Pereti: {data.wall_density_pct:F0}% | Fundaturi: {data.dead_end_ratio_pct:F0}%", labelStyle);
        }
        GUILayout.Label(renderer_.useGeneticAlgorithm ? "Generare: algoritm genetic" : "Generare: directa", labelStyle);
        GUILayout.Space(6);
        GUILayout.Label("Nivel nou:", labelStyle);
        GUILayout.BeginHorizontal();
        DifficultyButton("Easy", "easy");
        DifficultyButton("Medium", "medium");
        DifficultyButton("Hard", "hard");
        GUILayout.EndHorizontal();
        if (renderer_.IsRegenerating)
        {
            GUILayout.Label("Se genereaza...", labelStyle);
        }

        GUILayout.Space(8);
        GUILayout.Label("Legenda:", labelStyle);
        LegendRow("Start", renderer_.startColor);
        LegendRow("Cheie", renderer_.keyColor);
        LegendRow("Usa", renderer_.doorColor);
        LegendRow("Iesire", renderer_.exitColor);
        LegendRow("Perete", renderer_.wallColor);
        GUILayout.Space(8);

        PlayerController player = renderer_.Player;
        if (player != null)
        {
            GUILayout.Label(player.HasKey ? "Cheie: DA" : "Cheie: nu inca", labelStyle);
            GUILayout.Label($"Vieti: {player.Lives}/{player.maxLives}", labelStyle);
            GUILayout.Label($"Comori: {player.TreasureCount}", labelStyle);
            if (player.HasWon)
            {
                GUILayout.Label(
                    renderer_.IsRegenerating
                        ? "Ai castigat! Se genereaza nivel nou..."
                        : "Ai castigat! Nivel nou in curand...",
                    labelStyle);
            }
        }

        GUILayout.Space(4);
        GUILayout.Label("WASD / sageti = miscare", labelStyle);
        GUILayout.Label("L = reincarca | N = nivel nou", labelStyle);
        GUILayout.Label("+ / - = zoom | click-dreapta + mouse = rotire camera", labelStyle);

        if (player != null)
        {
            GUILayout.Space(6);
            GUILayout.Label("Debug:", labelStyle);
            GUILayout.Label(player.DebugStatus, labelStyle);
        }

        GUILayout.EndArea();
    }

    private void DifficultyButton(string label, string difficultyArg)
    {
        GUI.enabled = !renderer_.IsRegenerating;
        if (GUILayout.Button(label, GUILayout.Width(70)))
        {
            renderer_.RegenerateFromPython(difficultyArg);
        }
        GUI.enabled = true;
    }

    private void LegendRow(string label, Color color)
    {
        GUILayout.BeginHorizontal();
        // GUILayout.Box("", ...) + GUI.color nu se coloreaza fiabil (skin-ul
        // implicit are propriul shading peste tint) -- desenam direct o
        // textura solida in culoarea respectiva, fara ambiguitate.
        GUILayout.Box(GetSwatch(color), GUIStyle.none, GUILayout.Width(16), GUILayout.Height(16));
        GUILayout.Label(label, labelStyle);
        GUILayout.EndHorizontal();
    }

    private Texture2D GetSwatch(Color color)
    {
        if (swatchCache.TryGetValue(color, out Texture2D tex)) return tex;

        tex = new Texture2D(1, 1);
        tex.SetPixel(0, 0, color);
        tex.Apply();
        swatchCache[color] = tex;
        return tex;
    }

    private void EnsureStyles()
    {
        if (boxStyle != null) return;

        boxStyle = new GUIStyle(GUI.skin.box);
        Texture2D bg = new Texture2D(1, 1);
        bg.SetPixel(0, 0, new Color(0f, 0f, 0f, 0.55f));
        bg.Apply();
        boxStyle.normal.background = bg;

        labelStyle = new GUIStyle(GUI.skin.label);
        labelStyle.normal.textColor = Color.white;
        labelStyle.fontSize = 13;
    }
}
