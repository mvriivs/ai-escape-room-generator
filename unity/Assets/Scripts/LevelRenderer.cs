using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

// Citeste level.json (exportat din Python: generator + BFS) si randeaza
// nivelul ca o scena 3D vazuta de sus, cu lumina si umbre reale -- acelasi
// stil cu DungeonGenerator.cs din workshop (primitive + material cache),
// dar pornind de la un grid deja generat si validat in Python, nu generat
// aici. Spawneaza si un personaj (PlayerController) care se plimba pe grid.
//
// Setup in Unity:
//   1. Creeaza un GameObject gol in scena (ex: "LevelRenderer").
//   2. Ataseaza acest script.
//   3. Apasa Play. Daca nu exista Camera/Light in scena, se creeaza automat.
//
// Workflow zilnic:
//   python src/main.py --difficulty medium --export "<proiect_unity>/Assets/StreamingAssets/level.json"
//   apoi, in Play Mode, apasa L ca sa reincarce nivelul nou fara restart.
//
// Alegerea dificultatii se poate face si direct din Unity, fara linia de
// comanda: campul "Start Difficulty" de mai jos (din Inspector, inainte de
// Play) sau butoanele Easy/Medium/Hard din HUD (in timpul jocului).
public class LevelRenderer : MonoBehaviour
{
    public enum StartDifficulty { Easy, Medium, Hard }

    [Header("Sursa datelor")]
    public string jsonFileName = "level.json";
    public float tileSize = 1.0f;

    [Header("Dificultate la Play (sau butoanele din HUD)")]
    public StartDifficulty startDifficulty = StartDifficulty.Medium;

    [Header("Culori -- tema 'dungeon magic'")]
    public Color floorColor = new Color(0.85f, 0.76f, 0.60f);
    public Color wallColor = new Color(0.17f, 0.15f, 0.26f);
    public Color startColor = new Color(0.20f, 0.80f, 0.74f);
    public Color keyColor = new Color(0.98f, 0.80f, 0.28f);
    public Color doorColor = new Color(0.64f, 0.35f, 0.20f);
    public Color exitColor = new Color(0.82f, 0.34f, 0.80f);
    public Color enemyColor = new Color(0.84f, 0.22f, 0.30f);
    public Color trapColor = new Color(0.56f, 0.22f, 0.70f);
    public Color treasureColor = new Color(0.96f, 0.63f, 0.18f);
    public Color playerColor = new Color(0.97f, 0.94f, 0.88f);

    [Header("Pereti")]
    public float wallHeight = 1.0f;
    public float wallScaleXZ = 0.92f; // < 1 => se vede un mic gap intre pereti, arata mai putin "bloc masiv"

    // Cele 3 functii de fitness ale echipei (vezi genetic.py) -- alegi din
    // Inspector care ruleaza in joc, ca sa le poti demonstra pe rand.
    public enum FitnessMode { Default, Baseline, Complex }

    [Header("Generare (Python)")]
    [Tooltip("true = foloseste algoritmul genetic (genetic.py, prin run_genetic.py) ca sa gaseasca un nivel cu scorul de dificultate cat mai aproape de tinta. false = generare directa (main.py), mai rapida dar mai putin precisa pe scor.")]
    public bool useGeneticAlgorithm = true;
    public FitnessMode fitnessMode = FitnessMode.Default;
    public int geneticPopulation = 16;
    public int geneticGenerations = 15;

    [Header("Regenerare automata (Python) la victorie")]
    public bool autoRegenerateOnWin = true;
    public float winRegenerateDelay = 2.5f;
    [Tooltip("'python' cauta in PATH. Pune o cale completa doar daca 'python' nu e recunoscut.")]
    public string pythonExecutable = "python";
    [Tooltip("Gol = dedus automat, presupunand structura <repo>/unity/ (proiectul Unity) + <repo>/src/ (Python), ca frati.")]
    public string pythonScriptDir = "";

    public LevelData Current { get; private set; }
    public PlayerController Player { get; private set; }
    public bool IsRegenerating { get; private set; }

    private readonly Dictionary<Color, Material> materialCache = new Dictionary<Color, Material>();
    private Texture2D noiseTexture;
    private Light sun;
    private GameObject keyObject;
    private GameObject doorObject;
    private readonly Dictionary<Vector2Int, GameObject> contentAt = new Dictionary<Vector2Int, GameObject>();
    private bool regenerateScheduled;
    private float zoomMultiplier = 1f; // reglat cu rotita mouse-ului, vezi Update()

    // VARIABILE NOI PENTRU ROTIREA CAMEREI - andreea
    private float rotationX = 45f; // Unghiul pe verticala (pitch)
    private float rotationY = -35f; // Unghiul pe orizontala (yaw)
    private float rotationSpeed = 3f;

    // Proiectul porneste fara nicio scena salvata -- ca sa nu fie nevoie de
    // setup manual in Editor, cream automat obiectul cu LevelRenderer +
    // LevelHUD la intrarea in Play Mode, daca nu exista deja unul in scena.
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void Bootstrap()
    {
        if (FindFirstObjectByType<LevelRenderer>() != null) return;

        GameObject go = new GameObject("LevelRenderer");
        go.AddComponent<LevelRenderer>();
        go.AddComponent<LevelHUD>();
    }

    void Start()
    {
        EnsureCameraAndLight();

        bool started = RegenerateFromPython(DifficultyArg(startDifficulty));
        if (!started)
        {
            // Python n-a pornit (cale gresita etc.) -- macar incarcam ce e
            // deja pe disc, daca exista un level.json dintr-o rulare anterioara.
            LoadAndBuild();
        }
    }

    private static string DifficultyArg(StartDifficulty d) => d.ToString().ToLowerInvariant();

    // Daca pythonScriptDir nu e setat manual, presupunem structura de
    // monorepo: <repo>/unity/<proiect Unity>/Assets si <repo>/src/ ca frati
    // -- adica Assets/../../src.
    private string ResolvePythonScriptDir()
    {
        if (!string.IsNullOrEmpty(pythonScriptDir)) return pythonScriptDir;
        return Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "src"));
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.L))
        {
            LoadAndBuild();
        }
        if (Input.GetKeyDown(KeyCode.N))
        {
            RegenerateFromPython(null);
        }

        HandleZoomInput();

        // Roteste camera daca dai Click Dreapta (sau Click Mijloc / Scroll) si misti mouse-ul
        if (Input.GetMouseButton(1) || Input.GetMouseButton(2))
        {
            rotationY += Input.GetAxis("Mouse X") * rotationSpeed * 10f;
            rotationX -= Input.GetAxis("Mouse Y") * rotationSpeed * 10f;
            rotationX = Mathf.Clamp(rotationX, 10f, 85f); 
            
            if (Current != null)
            {
                ApplyCameraTransform(Current);
            }
        }

        if (autoRegenerateOnWin && !regenerateScheduled && Player != null && Player.HasWon)
        {
            regenerateScheduled = true;
            StartCoroutine(RegenerateAfterDelay());
        }
    }

    private IEnumerator RegenerateAfterDelay()
    {
        yield return new WaitForSeconds(winRegenerateDelay);
        RegenerateFromPython(null);
        regenerateScheduled = false;
    }

    // Cheama Python (generator + BFS) ca sa produca un nivel nou si il
    // exporta direct peste level.json, apoi il incarca. Python ramane
    // "creierul" -- Unity doar declanseaza rularea si randeaza rezultatul.
    // `difficulty` = null => pastreaza dificultatea nivelului curent (sau
    // "medium" daca inca nu exista niciunul).
    public bool RegenerateFromPython(string difficulty)
    {
        if (IsRegenerating) return false;
        IsRegenerating = true;

        difficulty ??= Current != null ? Current.difficulty : "medium";
        string exportPath = Path.Combine(Application.streamingAssetsPath, jsonFileName);
        string scriptDir = ResolvePythonScriptDir();

        // Cu algoritmul genetic: cauta parametrii (dimensiune labirint,
        // nr. inamici/capcane/comori) al caror scor de dificultate e cel
        // mai aproape de tinta -- ~1s cu setarile de mai jos, testat.
        // Fara el: generare directa, instant, dar scorul iese doar
        // "aproximativ" in banda dificultatii (fara optimizare).
        string fitnessArg = fitnessMode.ToString().ToLowerInvariant(); // Default|Baseline|Complex -> default|baseline|complex
        string arguments = useGeneticAlgorithm
            ? $"run_genetic.py --difficulty {difficulty} --fitness {fitnessArg} --population {geneticPopulation} --generations {geneticGenerations} --export \"{exportPath}\""
            : $"main.py --difficulty {difficulty} --export \"{exportPath}\"";

        var psi = new System.Diagnostics.ProcessStartInfo
        {
            FileName = pythonExecutable,
            Arguments = arguments,
            WorkingDirectory = scriptDir,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardError = true,
        };

        try
        {
            using (var process = System.Diagnostics.Process.Start(psi))
            {
                process.WaitForExit(8000);
                if (process.ExitCode != 0)
                {
                    Debug.LogError("[LevelRenderer] Python a esuat: " + process.StandardError.ReadToEnd());
                    IsRegenerating = false;
                    return false;
                }
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError(
                $"[LevelRenderer] Nu am putut rula '{pythonExecutable}' in '{scriptDir}': {e.Message}\n"
                + "Verifica ca 'python' e in PATH, sau seteaza manual pythonExecutable/pythonScriptDir in Inspector.");
            IsRegenerating = false;
            return false;
        }

        LoadAndBuild();
        IsRegenerating = false;
        return true;
    }

    public void LoadAndBuild()
    {
        string path = Path.Combine(Application.streamingAssetsPath, jsonFileName);
        if (!File.Exists(path))
        {
            Debug.LogWarning($"[LevelRenderer] Nu gasesc {path}. Exporta un nivel din Python cu --export.");
            return;
        }

        string json = File.ReadAllText(path);
        LevelData data = JsonUtility.FromJson<LevelData>(json);
        if (data == null || data.cells == null || data.cells.Length == 0)
        {
            Debug.LogError("[LevelRenderer] JSON invalid sau gol.");
            return;
        }

        Current = data;
        Build(data);
        FrameCamera(data);
        SpawnPlayer(data);
    }

    private void Build(LevelData data)
    {
        ClearChildren();
        keyObject = null;
        doorObject = null;
        contentAt.Clear();

        for (int y = 0; y < data.height; y++)
        {
            for (int x = 0; x < data.width; x++)
            {
                char c = data.CellAt(x, y);
                BuildCell(x, y, c);
            }
        }
    }

    private void BuildCell(int x, int y, char c)
    {
        if (c == '#')
        {
            PlaceBox($"wall_{x}_{y}", x, y, wallColor, height: wallHeight, yOffset: 0f, scaleXZ: wallScaleXZ);
            return;
        }

        // podeaua se pune sub orice alt tip de celula (S/K/D/E/X/T/$/.)
        PlaceBox($"floor_{x}_{y}", x, y, floorColor, height: 0.2f, yOffset: 0f);

        switch (c)
        {
            case 'S':
            {
                // pad plat pe podea -- personajul insusi marcheaza pozitia de start
                GameObject pad = PlaceCylinder($"start_{x}_{y}", x, y, startColor, radius: 0.4f, height: 0.04f, yOffset: 0.02f);
                EnableGlow(pad, startColor, 0.5f);
                break;
            }
            case 'K':
                keyObject = BuildKeyIcon(x, y);
                break;
            case 'D':
                doorObject = BuildDoorIcon(x, y);
                break;
            case 'E':
                BuildExitIcon(x, y);
                break;
            case 'X':
            {
                GameObject go = PlaceCapsule($"enemy_{x}_{y}", x, y, enemyColor, radius: 0.25f, yOffset: 0.35f);
                contentAt[new Vector2Int(x, y)] = go;
                break;
            }
            case 'T':
            {
                GameObject go = PlaceBox($"trap_{x}_{y}", x, y, trapColor, height: 0.08f, yOffset: 0.14f, scaleXZ: 0.55f, rotateY: 45f);
                contentAt[new Vector2Int(x, y)] = go;
                break;
            }
            case '$':
            {
                GameObject go = BuildTreasureIcon(x, y);
                contentAt[new Vector2Int(x, y)] = go;
                break;
            }
        }
    }

    // Scoate (si elimina din evidenta) obiectul de continut de la (x,y) --
    // folosit de PlayerController cand jucatorul culege o comoara sau da
    // peste o capcana/inamic, ca sa nu se mai declanseze a doua oara.
    public GameObject TakeContentAt(int x, int y)
    {
        Vector2Int key = new Vector2Int(x, y);
        if (contentAt.TryGetValue(key, out GameObject go))
        {
            contentAt.Remove(key);
            return go;
        }
        return null;
    }

    // ---------- iconite compuse ----------

    private GameObject BuildKeyIcon(int x, int y)
    {
        GameObject parent = new GameObject($"key_{x}_{y}");
        parent.transform.parent = transform;
        parent.transform.position = new Vector3(x * tileSize, 0.5f, y * tileSize);

        GameObject bow = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        bow.name = "bow";
        bow.transform.parent = parent.transform;
        bow.transform.localScale = new Vector3(0.34f, 0.34f, 0.12f);
        bow.transform.localPosition = new Vector3(-0.16f, 0f, 0f);

        GameObject shaft = GameObject.CreatePrimitive(PrimitiveType.Cube);
        shaft.name = "shaft";
        shaft.transform.parent = parent.transform;
        shaft.transform.localScale = new Vector3(0.34f, 0.08f, 0.08f);
        shaft.transform.localPosition = new Vector3(0.14f, 0f, 0f);

        GameObject tooth = GameObject.CreatePrimitive(PrimitiveType.Cube);
        tooth.name = "tooth";
        tooth.transform.parent = parent.transform;
        tooth.transform.localScale = new Vector3(0.1f, 0.16f, 0.08f);
        tooth.transform.localPosition = new Vector3(0.26f, -0.08f, 0f);

        foreach (Transform child in parent.transform)
        {
            ApplyColor(child.gameObject, keyColor);
            EnableGlow(child.gameObject, keyColor, 1.3f);
        }

        Bobber bob = parent.AddComponent<Bobber>();
        bob.spinSpeed = 100f;
        return parent;
    }

    private GameObject BuildDoorIcon(int x, int y)
    {
        GameObject parent = new GameObject($"door_{x}_{y}");
        parent.transform.parent = transform;
        parent.transform.position = new Vector3(x * tileSize, 0f, y * tileSize);

        GameObject frame = GameObject.CreatePrimitive(PrimitiveType.Cube);
        frame.name = "frame";
        frame.transform.parent = parent.transform;
        frame.transform.localScale = new Vector3(tileSize * 0.8f, 0.78f, tileSize * 0.16f);
        frame.transform.localPosition = new Vector3(0f, 0.39f, 0f);
        ApplyColor(frame, doorColor);

        GameObject knob = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        knob.name = "knob";
        knob.transform.parent = parent.transform;
        knob.transform.localScale = Vector3.one * 0.1f;
        knob.transform.localPosition = new Vector3(tileSize * 0.22f, 0.4f, tileSize * 0.1f);
        ApplyColor(knob, keyColor);
        EnableGlow(knob, keyColor, 1f);

        return parent;
    }

    private void BuildExitIcon(int x, int y)
    {
        GameObject basePad = PlaceCylinder($"exit_{x}_{y}", x, y, exitColor, radius: 0.35f, height: 0.12f, yOffset: 0.22f);
        EnableGlow(basePad, exitColor, 1.1f);
        Bobber padBob = basePad.AddComponent<Bobber>();
        padBob.spinSpeed = 35f;
        padBob.bobHeight = 0.04f;

        GameObject beam = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        beam.name = $"exit_beam_{x}_{y}";
        beam.transform.parent = transform;
        beam.transform.localScale = new Vector3(0.1f, 0.6f, 0.1f);
        beam.transform.position = new Vector3(x * tileSize, 0.9f, y * tileSize);
        Destroy(beam.GetComponent<Collider>());
        ApplyColor(beam, exitColor);
        EnableGlow(beam, exitColor, 1.6f);
        Bobber beamBob = beam.AddComponent<Bobber>();
        beamBob.spinSpeed = 60f;
        beamBob.bobHeight = 0f;
    }

    private GameObject BuildTreasureIcon(int x, int y)
    {
        GameObject parent = new GameObject($"treasure_{x}_{y}");
        parent.transform.parent = transform;
        parent.transform.position = new Vector3(x * tileSize, 0f, y * tileSize);

        GameObject baseChest = GameObject.CreatePrimitive(PrimitiveType.Cube);
        baseChest.name = "chest";
        baseChest.transform.parent = parent.transform;
        baseChest.transform.localScale = new Vector3(tileSize * 0.5f, 0.3f, tileSize * 0.5f);
        baseChest.transform.localPosition = new Vector3(0f, 0.35f, 0f);
        ApplyColor(baseChest, treasureColor);
        EnableGlow(baseChest, treasureColor, 0.9f);

        GameObject lid = GameObject.CreatePrimitive(PrimitiveType.Cube);
        lid.name = "lid";
        lid.transform.parent = parent.transform;
        lid.transform.localScale = new Vector3(tileSize * 0.55f, 0.08f, tileSize * 0.55f);
        lid.transform.localPosition = new Vector3(0f, 0.54f, 0f);
        ApplyColor(lid, new Color(0.45f, 0.3f, 0.08f));

        return parent;
    }

    // ---------- personaj ----------

    private void SpawnPlayer(LevelData data)
    {
        if (Player == null)
        {
            GameObject go = BuildPlayerModel();
            Player = go.AddComponent<PlayerController>();
        }

        Player.Spawn(this, data, keyObject, doorObject);
    }

    private GameObject BuildPlayerModel()
    {
        GameObject parent = new GameObject("Player");
        parent.transform.parent = transform;

        GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        body.name = "body";
        body.transform.parent = parent.transform;
        body.transform.localScale = new Vector3(0.32f, 0.28f, 0.32f);
        body.transform.localPosition = new Vector3(0f, 0.3f, 0f);
        Destroy(body.GetComponent<Collider>());
        ApplyColor(body, playerColor);
        EnableGlow(body, playerColor, 0.25f);

        GameObject nose = GameObject.CreatePrimitive(PrimitiveType.Cube);
        nose.name = "facing";
        nose.transform.parent = parent.transform;
        nose.transform.localScale = new Vector3(0.1f, 0.1f, 0.22f);
        nose.transform.localPosition = new Vector3(0f, 0.3f, 0.22f);
        Destroy(nose.GetComponent<Collider>());
        ApplyColor(nose, startColor);

        return parent;
    }

    // ---------- primitive helpers ----------

    private GameObject PlaceBox(string name, int x, int y, Color color, float height, float yOffset, float scaleXZ = 1f, float rotateY = 0f)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.parent = transform;
        go.transform.localScale = new Vector3(tileSize * scaleXZ, height, tileSize * scaleXZ);
        go.transform.position = new Vector3(x * tileSize, yOffset + height / 2f, y * tileSize);
        if (rotateY != 0f) go.transform.rotation = Quaternion.Euler(0f, rotateY, 0f);
        ApplyColor(go, color);
        return go;
    }

    private GameObject PlaceSphere(string name, int x, int y, Color color, float radius, float yOffset)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        go.name = name;
        go.transform.parent = transform;
        go.transform.localScale = Vector3.one * radius * 2f;
        go.transform.position = new Vector3(x * tileSize, yOffset, y * tileSize);
        ApplyColor(go, color);
        return go;
    }

    private GameObject PlaceCapsule(string name, int x, int y, Color color, float radius, float yOffset)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        go.name = name;
        go.transform.parent = transform;
        go.transform.localScale = new Vector3(radius * 2f, yOffset, radius * 2f);
        go.transform.position = new Vector3(x * tileSize, yOffset, y * tileSize);
        ApplyColor(go, color);
        return go;
    }

    private GameObject PlaceCylinder(string name, int x, int y, Color color, float radius, float height, float yOffset)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        go.name = name;
        go.transform.parent = transform;
        go.transform.localScale = new Vector3(radius * 2f, height, radius * 2f);
        go.transform.position = new Vector3(x * tileSize, yOffset, y * tileSize);
        ApplyColor(go, color);
        return go;
    }

    private void ApplyColor(GameObject go, Color color)
    {
        Renderer renderer = go.GetComponent<Renderer>();
        if (renderer != null) renderer.sharedMaterial = GetMaterialForColor(color);
    }

    // Adauga emisie (glow) pe materialul obiectului, ca elementele importante
    // (Start/Key/Exit/Treasure) sa iasa in evidenta fata de peretii si podeaua
    // "plate". Sigur de folosit: culorile astea sunt exclusive fiecarui tip
    // de celula, deci nu afecteaza alte obiecte care share-uiesc materialul.
    private void EnableGlow(GameObject go, Color color, float intensity)
    {
        Renderer renderer = go.GetComponent<Renderer>();
        if (renderer == null) return;

        Material material = renderer.sharedMaterial;
        if (material == null || !material.HasProperty("_EmissionColor")) return;

        material.EnableKeyword("_EMISSION");
        material.SetColor("_EmissionColor", color * intensity);
        material.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
    }

    private Material GetMaterialForColor(Color color)
    {
        if (materialCache.TryGetValue(color, out Material cached)) return cached;

        Shader shader = Shader.Find("Standard")
            ?? Shader.Find("Universal Render Pipeline/Lit")
            ?? Shader.Find("Legacy Shaders/Diffuse")
            ?? Shader.Find("Unlit/Color");

        Material material = new Material(shader);
        if (material.HasProperty("_Color")) material.SetColor("_Color", color);
        else if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", color);

        // textura generata procedural (nu descarcam nimic) -- rupe aspectul
        // "plastic plat" al culorilor solide si da senzatie de piatra/nisip
        Texture2D noise = GetNoiseTexture();
        if (material.HasProperty("_MainTex"))
        {
            material.SetTexture("_MainTex", noise);
            material.mainTextureScale = new Vector2(2f, 2f);
        }
        else if (material.HasProperty("_BaseMap"))
        {
            material.SetTexture("_BaseMap", noise);
            material.mainTextureScale = new Vector2(2f, 2f);
        }

        materialCache[color] = material;
        return material;
    }

    // Textura de zgomot (Perlin), generata o singura data si refolosita ca
    // _MainTex pe toate materialele -- inmultita cu _Color, da o variatie
    // subtila de tip piatra/nisip in loc de o culoare plata, fara sa
    // descarcam vreun asset extern.
    private Texture2D GetNoiseTexture()
    {
        if (noiseTexture != null) return noiseTexture;

        const int size = 64;
        noiseTexture = new Texture2D(size, size, TextureFormat.RGB24, false);
        noiseTexture.wrapMode = TextureWrapMode.Repeat;
        noiseTexture.filterMode = FilterMode.Bilinear;

        float offsetX = Random.Range(0f, 1000f);
        float offsetY = Random.Range(0f, 1000f);

        for (int y = 0; y < size; y++)
        {
            for (int x = 0; x < size; x++)
            {
                float big = Mathf.PerlinNoise((x + offsetX) * 0.10f, (y + offsetY) * 0.10f);
                float fine = Mathf.PerlinNoise((x + offsetX) * 0.45f, (y + offsetY) * 0.45f);
                float shade = Mathf.Clamp01(0.78f + (big - 0.5f) * 0.3f + (fine - 0.5f) * 0.14f);
                noiseTexture.SetPixel(x, y, new Color(shade, shade, shade));
            }
        }
        noiseTexture.Apply();
        return noiseTexture;
    }

    private void ClearChildren()
    {
        for (int i = transform.childCount - 1; i >= 0; i--)
        {
            Transform child = transform.GetChild(i);
            if (Player != null && child.gameObject == Player.gameObject) continue;
            Object.Destroy(child.gameObject);
        }
    }

    // ---------- camera + lumina ----------

    private void EnsureCameraAndLight()
    {
        Camera cam = Camera.main;
        if (cam == null)
        {
            GameObject camGO = new GameObject("Main Camera");
            camGO.tag = "MainCamera";
            cam = camGO.AddComponent<Camera>();
        }
        // fundal solid, intunecat -- inlocuieste cerul albastru implicit
        // (nu are sens intr-o scena de dungeon vazuta de sus)
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.05f, 0.045f, 0.09f);

        sun = FindFirstObjectByType<Light>();
        if (sun == null)
        {
            GameObject lightGO = new GameObject("Directional Light");
            sun = lightGO.AddComponent<Light>();
            sun.type = LightType.Directional;
        }
        sun.transform.rotation = Quaternion.Euler(55f, -35f, 0f);
        sun.shadows = LightShadows.Soft;
        sun.intensity = 1.15f;
        sun.color = new Color(1f, 0.93f, 0.82f); // lumina calda, tip torta

        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.20f, 0.19f, 0.30f); // umbra rece, pt contrast cu lumina calda
    }

    // Reseteaza camera la unghiul implicit (apelata la fiecare nivel nou) --
    // rotatia curenta (drag cu click-dreapta/mijloc, vezi Update()) se
    // aplica peste acest unghi de baza, prin ApplyCameraTransform.
    private void FrameCamera(LevelData data)
    {
        rotationX = 55f;
        rotationY = -35f;
        ApplyCameraTransform(data);
    }

    private void ApplyCameraTransform(LevelData data)
    {
        Camera cam = Camera.main;
        if (cam == null) return;

        float cx = (data.width - 1) * tileSize / 2f;
        float cz = (data.height - 1) * tileSize / 2f;
        float span = Mathf.Max(data.width, data.height) * tileSize * zoomMultiplier;

        // Calcul pozitia camerei pe o sfera in jurul centrului labirintului folosind unghiurile de rotatie
        Quaternion rotation = Quaternion.Euler(rotationX, rotationY, 0f);
        Vector3 center = new Vector3(cx, 0f, cz);
        
        // Distanta fata de centru in functie de marimea hartii si zoom
        Vector3 offset = rotation * new Vector3(0f, 0f, -span * 1.2f);

        cam.transform.position = center + offset;
        cam.transform.LookAt(center);
        cam.fieldOfView = 46f;
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = span * 6f;
    }

    // Zoom: rotita mouse-ului SAU tastele -/= (util fara mouse -- ex. laptop
    // cu touchpad). Repozitioneaza camera fara sa reconstruiasca nivelul.
    private void HandleZoomInput()
    {
        if (Current == null) return;

        float scroll = Input.mouseScrollDelta.y;
        float keyZoom = 0f;
        if (Input.GetKey(KeyCode.Minus) || Input.GetKey(KeyCode.KeypadMinus)) keyZoom = -1f;
        else if (Input.GetKey(KeyCode.Equals) || Input.GetKey(KeyCode.KeypadPlus)) keyZoom = 1f;

        float delta = scroll * 0.08f + keyZoom * 0.03f;
        if (Mathf.Approximately(delta, 0f)) return;

        zoomMultiplier = Mathf.Clamp(zoomMultiplier - delta, 0.5f, 2.5f);
        FrameCamera(Current);
    }
}
