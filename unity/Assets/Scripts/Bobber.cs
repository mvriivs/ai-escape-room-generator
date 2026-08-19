using UnityEngine;

// Mica animatie de "idle" (plutire pe verticala + rotatie) pentru obiectele
// importante (cheie, iesire), ca sa iasa in evidenta pe harta in loc sa
// stea complet static.
public class Bobber : MonoBehaviour
{
    public float bobHeight = 0.12f;
    public float bobSpeed = 2.5f;
    public float spinSpeed = 90f;

    private Vector3 basePos;

    void Start()
    {
        basePos = transform.position;
    }

    void Update()
    {
        float y = basePos.y + Mathf.Sin(Time.time * bobSpeed) * bobHeight;
        transform.position = new Vector3(basePos.x, y, basePos.z);
        transform.Rotate(Vector3.up, spinSpeed * Time.deltaTime, Space.World);
    }
}
