from datetime import UTC, datetime

from models import LecturaPanel


def test_lectura_panel_model_has_expected_table() -> None:
    lectura = LecturaPanel(
        timestamp=datetime.now(UTC),
        voltaje=36.0,
        corriente=8.0,
        potencia=288.0,
        energia_acumulada=1.5,
        punto_id=1,
    )

    assert LecturaPanel.__tablename__ == "lecturas_panel"
    assert lectura.punto_id == 1
