from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict[str, str]:
    return {"message": "EDSIA Beyond API - Photovoltaic Monitor"}


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "message": "API funcionando correctamente"}
