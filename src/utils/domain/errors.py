class DomainError(Exception):
    """Base para errores de negocio traducibles a respuestas HTTP."""


class CellNotFoundError(DomainError):
    def __init__(self, cell_id: int) -> None:
        self.cell_id = cell_id
        super().__init__(f"Photovoltaic cell {cell_id} not found")


class DuplicateCellNameError(DomainError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"A photovoltaic cell named '{name}' already exists")


class InactiveCellError(DomainError):
    def __init__(self, cell_id: int) -> None:
        self.cell_id = cell_id
        super().__init__(f"Photovoltaic cell {cell_id} is inactive and cannot accept readings")


class ReadingNotFoundError(DomainError):
    def __init__(self, reading_id: int) -> None:
        self.reading_id = reading_id
        super().__init__(f"Reading {reading_id} not found")


class NoReadingsInPeriodError(DomainError):
    def __init__(self, cell_id: int, days: int) -> None:
        self.cell_id = cell_id
        self.days = days
        super().__init__(f"No readings for cell {cell_id} in the last {days} day(s)")
