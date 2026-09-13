from sensor_simulado import generar_lectura


def test_generar_lectura_returns_consistent_values() -> None:
    payload, energia = generar_lectura(punto_id=1, energia_acumulada=0.0)

    assert payload["punto_id"] == 1
    assert payload["potencia"] == round(payload["voltaje"] * payload["corriente"], 2)
    assert payload["energia_acumulada"] == energia
    assert energia > 0
