import pytest

from edsia_beyond.domain.errors import CellNotFoundError, DuplicateCellNameError
from edsia_beyond.repositories.protocols import CellRepository
from edsia_beyond.schemas.cell import CellCreate, CellUpdate
from edsia_beyond.services.cell_service import CellService
from tests.fakes import InMemoryCellRepository, make_cell


def build_service(repo: InMemoryCellRepository | None = None) -> CellService:
    # La anotación fuerza a mypy a verificar que el fake satisface el protocolo.
    cells: CellRepository = repo if repo is not None else InMemoryCellRepository()
    return CellService(cells=cells)


def test_create_derives_max_safe_voltage_from_rated_voltage() -> None:
    service = build_service()

    cell = service.create(
        CellCreate(name="Celda_01", location="Techo", rated_voltage=5.0)
    )

    assert cell.max_safe_voltage == 6.0
    assert cell.is_active is True


def test_create_rejects_duplicate_names() -> None:
    service = build_service(InMemoryCellRepository([make_cell(name="Celda_01")]))

    with pytest.raises(DuplicateCellNameError):
        service.create(CellCreate(name="Celda_01", location="Otro", rated_voltage=5.0))


def test_get_raises_when_cell_is_missing() -> None:
    with pytest.raises(CellNotFoundError):
        build_service().get(404)


def test_list_active_excludes_inactive_cells() -> None:
    repo = InMemoryCellRepository(
        [make_cell(1, "activa"), make_cell(2, "inactiva", is_active=False)]
    )
    service = build_service(repo)

    assert len(service.list_all()) == 2
    assert [cell.name for cell in service.list_active()] == ["activa"]


def test_update_recomputes_max_safe_voltage_when_rating_changes() -> None:
    service = build_service(InMemoryCellRepository([make_cell(rated_voltage=5.0)]))

    updated = service.update(1, CellUpdate(rated_voltage=10.0))

    assert updated.rated_voltage == 10.0
    assert updated.max_safe_voltage == 12.0


def test_update_leaves_untouched_fields_alone() -> None:
    service = build_service(InMemoryCellRepository([make_cell()]))

    updated = service.update(1, CellUpdate(efficiency_threshold=70.0))

    assert updated.efficiency_threshold == 70.0
    assert updated.max_safe_voltage == 6.0
    assert updated.name == "Celda_01"


def test_update_rejects_a_name_owned_by_another_cell() -> None:
    repo = InMemoryCellRepository([make_cell(1, "uno"), make_cell(2, "dos")])
    service = build_service(repo)

    with pytest.raises(DuplicateCellNameError):
        service.update(1, CellUpdate(name="dos"))


def test_update_allows_reassigning_a_cell_its_own_name() -> None:
    service = build_service(InMemoryCellRepository([make_cell(1, "uno")]))

    assert service.update(1, CellUpdate(name="uno")).name == "uno"


def test_update_raises_when_cell_is_missing() -> None:
    with pytest.raises(CellNotFoundError):
        build_service().update(404, CellUpdate(location="Techo"))


def test_delete_removes_the_cell() -> None:
    repo = InMemoryCellRepository([make_cell()])
    service = build_service(repo)

    service.delete(1)

    assert service.list_all() == []


def test_delete_raises_when_cell_is_missing() -> None:
    with pytest.raises(CellNotFoundError):
        build_service().delete(404)
