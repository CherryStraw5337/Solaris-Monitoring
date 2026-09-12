import pytest

from edsia_beyond.domain.analysis import (
    AnomalyDetector,
    CellSpec,
    CompositeAnomalyDetector,
    LowEfficiencyAnomalyDetector,
    OverVoltageAnomalyDetector,
    RatioEfficiencyCalculator,
    ReadingAnalyzer,
    safe_voltage_limit,
)

SPEC = CellSpec(rated_voltage=5.0, max_safe_voltage=6.0, efficiency_threshold=80.0)


class AlwaysDetector:
    def __init__(self, result: bool) -> None:
        self._result = result

    def is_anomalous(
        self, voltage_measured: float, efficiency_percentage: float, spec: CellSpec
    ) -> bool:
        return self._result


def test_safe_voltage_limit_applies_margin() -> None:
    assert safe_voltage_limit(5.0) == 6.0


@pytest.mark.parametrize("rated", [0.0, -1.0])
def test_safe_voltage_limit_rejects_non_positive(rated: float) -> None:
    with pytest.raises(ValueError, match="rated_voltage"):
        safe_voltage_limit(rated)


def test_efficiency_is_ratio_against_rated_voltage() -> None:
    assert RatioEfficiencyCalculator().calculate(4.85, SPEC) == 97.0


def test_efficiency_is_rounded_to_two_decimals() -> None:
    assert RatioEfficiencyCalculator().calculate(1.0, SPEC) == 20.0
    assert RatioEfficiencyCalculator().calculate(0.3333, SPEC) == 6.67


def test_efficiency_rejects_non_positive_rated_voltage() -> None:
    spec = CellSpec(rated_voltage=0.0, max_safe_voltage=1.0, efficiency_threshold=80.0)
    with pytest.raises(ValueError, match="rated_voltage"):
        RatioEfficiencyCalculator().calculate(4.0, spec)


@pytest.mark.parametrize(
    ("voltage", "expected"),
    [(6.01, True), (6.0, False), (4.0, False)],
)
def test_over_voltage_detector_triggers_strictly_above_limit(
    voltage: float, expected: bool
) -> None:
    assert OverVoltageAnomalyDetector().is_anomalous(voltage, 100.0, SPEC) is expected


@pytest.mark.parametrize(
    ("efficiency", "expected"),
    [(79.9, True), (80.0, False), (95.0, False)],
)
def test_low_efficiency_detector_triggers_below_threshold(
    efficiency: float, expected: bool
) -> None:
    assert LowEfficiencyAnomalyDetector().is_anomalous(4.0, efficiency, SPEC) is expected


def test_composite_detector_is_true_when_any_member_triggers() -> None:
    detector = CompositeAnomalyDetector([AlwaysDetector(False), AlwaysDetector(True)])
    assert detector.is_anomalous(4.0, 95.0, SPEC) is True


def test_composite_detector_is_false_when_no_member_triggers() -> None:
    detector = CompositeAnomalyDetector([AlwaysDetector(False), AlwaysDetector(False)])
    assert detector.is_anomalous(4.0, 95.0, SPEC) is False


def test_composite_detector_without_members_never_triggers() -> None:
    assert CompositeAnomalyDetector([]).is_anomalous(999.0, 0.0, SPEC) is False


def test_analyzer_combines_efficiency_and_anomaly() -> None:
    analyzer = ReadingAnalyzer(
        calculator=RatioEfficiencyCalculator(),
        detector=OverVoltageAnomalyDetector(),
    )
    result = analyzer.analyze(6.5, SPEC)

    assert result.voltage_measured == 6.5
    assert result.efficiency_percentage == 130.0
    assert result.is_anomaly is True


def test_analyzer_accepts_any_detector_implementation() -> None:
    detector: AnomalyDetector = AlwaysDetector(True)
    analyzer = ReadingAnalyzer(calculator=RatioEfficiencyCalculator(), detector=detector)

    assert analyzer.analyze(5.0, SPEC).is_anomaly is True
