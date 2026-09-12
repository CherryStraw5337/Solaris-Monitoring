from main import health_check


def test_health_uses_issue_update_date(monkeypatch) -> None:
    monkeypatch.setenv("UPDATE_DATE", "2026-09-12")

    assert health_check() == {
        "service_status": "operational",
        "update_date": "2026-09-12",
        "message": "El sistema se encuentra en funcionamiento correcto",
    }


def test_health_reports_invalid_update_date(monkeypatch) -> None:
    monkeypatch.setenv("UPDATE_DATE", "12/09/2026")

    result = health_check()

    assert result == {
        "service_status": "degraded",
        "update_date": "Configuración inválida",
        "message": "El sistema requiere atención: la configuración de actualización no es válida",
    }