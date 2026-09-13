from fastapi import APIRouter, status

from utils.dependencies import CellServiceDep
from utils.schemas.cell import CellCreate, CellOut, CellUpdate

router = APIRouter(prefix="/cells", tags=["cells"])


@router.post("", response_model=CellOut, status_code=status.HTTP_201_CREATED)
def create_cell(payload: CellCreate, service: CellServiceDep) -> CellOut:
    return service.create(payload)


@router.get("", response_model=list[CellOut])
def list_cells(service: CellServiceDep) -> list[CellOut]:
    return service.list_all()


@router.get("/active", response_model=list[CellOut])
def list_active_cells(service: CellServiceDep) -> list[CellOut]:
    return service.list_active()


@router.get("/{cell_id}", response_model=CellOut)
def get_cell(cell_id: int, service: CellServiceDep) -> CellOut:
    return service.get(cell_id)


@router.put("/{cell_id}", response_model=CellOut)
def update_cell(cell_id: int, payload: CellUpdate, service: CellServiceDep) -> CellOut:
    return service.update(cell_id, payload)


@router.delete("/{cell_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cell(cell_id: int, service: CellServiceDep) -> None:
    service.delete(cell_id)
