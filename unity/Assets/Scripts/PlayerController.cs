using System.Collections;
using UnityEngine;

// Miscare pe grid (o celula per apasare de tasta - WASD sau sagetile),
// verificata direct pe datele nivelului (nu fizica/coliziuni Unity):
//   - peretii ('#') blocheaza mereu.
//   - usa ('D') blocheaza pana cand ai cheia.
//   - cheia ('K') e culeasa automat cand intri pe celula ei.
//   - iesirea ('E') declanseaza starea de "castigat".
public class PlayerController : MonoBehaviour
{
    public float moveDuration = 0.12f;
    public int maxLives = 3;

    public bool HasKey { get; private set; }
    public bool HasWon { get; private set; }
    public int MoveCount { get; private set; }
    public int Lives { get; private set; }
    public int TreasureCount { get; private set; }
    public string DebugStatus { get; private set; } = "(inca nicio tasta apasata)";

    private LevelRenderer levelRenderer;
    private LevelData data;
    private GameObject keyObject;
    private GameObject doorObject;

    private int gridX;
    private int gridY;
    private bool isMoving;

    public void Spawn(LevelRenderer renderer, LevelData levelData, GameObject key, GameObject door)
    {
        levelRenderer = renderer;
        data = levelData;
        keyObject = key;
        doorObject = door;
        HasKey = false;
        HasWon = false;
        isMoving = false;
        MoveCount = 0;
        Lives = maxLives;
        TreasureCount = 0;
        DebugStatus = "(inca nicio tasta apasata)";

        gridX = data.start_x;
        gridY = data.start_y;
        transform.position = GridToWorld(gridX, gridY);
    }

    void Update()
    {
        // debug: cat timp a trecut de la ultimul input citit -- daca ramane
        // mereu pe "(inca nicio tasta apasata)" in HUD, tastele nu ajung deloc
        // la joc (cel mai probabil fereastra Game nu are focus).
        if (isMoving || HasWon || data == null) return;

        int dx = 0, dy = 0;
        string keyName = null;
        if (Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow)) { dy = 1; keyName = "sus"; }
        else if (Input.GetKeyDown(KeyCode.S) || Input.GetKeyDown(KeyCode.DownArrow)) { dy = -1; keyName = "jos"; }
        else if (Input.GetKeyDown(KeyCode.A) || Input.GetKeyDown(KeyCode.LeftArrow)) { dx = -1; keyName = "stanga"; }
        else if (Input.GetKeyDown(KeyCode.D) || Input.GetKeyDown(KeyCode.RightArrow)) { dx = 1; keyName = "dreapta"; }

        if (keyName == null) return;

        bool moved = TryMove(dx, dy);
        DebugStatus = $"tasta='{keyName}' | mutat={moved} | pozitie=({gridX},{gridY}) | total mutari={MoveCount}";
    }

    private bool TryMove(int dx, int dy)
    {
        int nx = gridX + dx;
        int ny = gridY + dy;
        if (nx < 0 || nx >= data.width || ny < 0 || ny >= data.height) return false;

        char target = data.CellAt(nx, ny);
        if (target == '#') return false;
        if (target == 'D' && !HasKey) return false; // usa blocata fara cheie

        if (target == 'K' && keyObject != null)
        {
            HasKey = true;
            Destroy(keyObject);
            keyObject = null;
        }
        if (target == 'D' && doorObject != null)
        {
            Destroy(doorObject);
            doorObject = null;
        }
        if (target == 'E')
        {
            HasWon = true;
        }

        // inamic/capcana -- te loveste (o viata mai putin) si te trimite
        // inapoi la Start; comoara -- se aduna la scor. Ambele dispar dupa
        // prima intalnire (levelRenderer tine evidenta lor).
        bool bounceBack = false;
        if (target == 'X' || target == 'T')
        {
            GameObject hazard = levelRenderer.TakeContentAt(nx, ny);
            if (hazard != null) Destroy(hazard);
            Lives = Mathf.Max(0, Lives - 1);
            if (Lives == 0) Lives = maxLives; // fara game-over deocamdata -- doar un reset "soft"
            bounceBack = true;
        }
        else if (target == '$')
        {
            GameObject treasure = levelRenderer.TakeContentAt(nx, ny);
            if (treasure != null)
            {
                Destroy(treasure);
                TreasureCount++;
            }
        }

        gridX = nx;
        gridY = ny;
        MoveCount++;
        StartCoroutine(MoveTo(GridToWorld(gridX, gridY), dx, dy, bounceBack));
        return true;
    }

    private IEnumerator MoveTo(Vector3 destination, int dx, int dy, bool bounceBack)
    {
        isMoving = true;
        if (dx != 0 || dy != 0)
        {
            transform.rotation = Quaternion.LookRotation(new Vector3(dx, 0f, dy));
        }

        yield return Slide(destination);

        if (bounceBack)
        {
            yield return new WaitForSeconds(0.25f);
            gridX = data.start_x;
            gridY = data.start_y;
            yield return Slide(GridToWorld(gridX, gridY));
        }

        isMoving = false;
    }

    private IEnumerator Slide(Vector3 destination)
    {
        Vector3 start = transform.position;
        float t = 0f;
        while (t < moveDuration)
        {
            t += Time.deltaTime;
            transform.position = Vector3.Lerp(start, destination, t / moveDuration);
            yield return null;
        }
        transform.position = destination;
    }

    private Vector3 GridToWorld(int x, int y)
    {
        float tile = levelRenderer != null ? levelRenderer.tileSize : 1f;
        return new Vector3(x * tile, 0.3f, y * tile);
    }
}
