from datetime import datetime

from _pytest.monkeypatch import MonkeyPatch

from main import LecturaPayload, health_check, recibir_lectura


def test_health_uses_issue_update_date(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("UPDATE_DATE", "2026-09-12")

    assert health_check() == {
        "service_status": "operational",
        "update_date": "2026-09-12",
        "message": "El sistema se encuentra en funcionamiento correcto",
    }


def test_health_reports_invalid_update_date(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("UPDATE_DATE", "12/09/2026")

    result = health_check()

    assert result == {
        "service_status": "degraded",
        "update_date": "Configuración inválida",
        "message": "El sistema requiere atención: la configuración de actualización no es válida",
    }


def test_health_reports_missing_update_date(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("UPDATE_DATE", raising=False)

    assert health_check()["update_date"] == "No definida"


def test_recibir_lectura_returns_payload() -> None:
    lectura = LecturaPayload(
        timestamp=datetime(2026, 9, 12, 12, 0),
        voltaje=36.0,
        corriente=8.0,
        potencia=288.0,
        energia_acumulada=1.5,
        punto_id=1,
    )

    result = recibir_lectura(lectura)

    assert result["message"] == "Lectura recibida exitosamente"
    assert result["data"] == lectura
