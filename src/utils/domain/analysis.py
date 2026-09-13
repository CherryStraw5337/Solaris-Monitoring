from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

SAFE_VOLTAGE_MARGIN = 1.2
EFFICIENCY_PRECISION = 2


def safe_voltage_limit(rated_voltage: float) -> float:
    if rated_voltage <= 0:
        raise ValueError("rated_voltage must be greater than zero")
    return round(rated_voltage * SAFE_VOLTAGE_MARGIN, EFFICIENCY_PRECISION)


@dataclass(frozen=True, slots=True)
class CellSpec:
    rated_voltage: float
    max_safe_voltage: float
    efficiency_threshold: float


@dataclass(frozen=True, slots=True)
class AnalyzedReading:
    voltage_measured: float
    efficiency_percentage: float
    is_anomaly: bool


class EfficiencyCalculator(Protocol):
    def calculate(self, voltage_measured: float, spec: CellSpec) -> float: ...


class AnomalyDetector(Protocol):
    def is_anomalous(
        self, voltage_measured: float, efficiency_percentage: float, spec: CellSpec
    ) -> bool: ...


class RatioEfficiencyCalculator:
    def calculate(self, voltage_measured: float, spec: CellSpec) -> float:
        if spec.rated_voltage <= 0:
            raise ValueError("rated_voltage must be greater than zero")
        return round((voltage_measured / spec.rated_voltage) * 100, EFFICIENCY_PRECISION)


class OverVoltageAnomalyDetector:
    def is_anomalous(
        self, voltage_measured: float, efficiency_percentage: float, spec: CellSpec
    ) -> bool:
        return voltage_measured > spec.max_safe_voltage


class LowEfficiencyAnomalyDetector:
    def is_anomalous(
        self, voltage_measured: float, efficiency_percentage: float, spec: CellSpec
    ) -> bool:
        return efficiency_percentage < spec.efficiency_threshold


class CompositeAnomalyDetector:
    def __init__(self, detectors: Sequence[AnomalyDetector]) -> None:
        self._detectors = tuple(detectors)

    def is_anomalous(
        self, voltage_measured: float, efficiency_percentage: float, spec: CellSpec
    ) -> bool:
        return any(
            detector.is_anomalous(voltage_measured, efficiency_percentage, spec)
            for detector in self._detectors
        )


class ReadingAnalyzer:
    def __init__(self, calculator: EfficiencyCalculator, detector: AnomalyDetector) -> None:
        self._calculator = calculator
        self._detector = detector

    def analyze(self, voltage_measured: float, spec: CellSpec) -> AnalyzedReading:
        efficiency = self._calculator.calculate(voltage_measured, spec)
        return AnalyzedReading(
            voltage_measured=voltage_measured,
            efficiency_percentage=efficiency,
            is_anomaly=self._detector.is_anomalous(voltage_measured, efficiency, spec),
        )
