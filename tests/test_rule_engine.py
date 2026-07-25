from app.models.symptom import Severity, SymptomAnalysisRequest
from app.rules.engine import evaluate, more_urgent


def _request(**overrides):
    defaults = {"symptoms": "Feeling a bit tired", "duration": "1 day"}
    defaults.update(overrides)
    return SymptomAnalysisRequest(**defaults)


def test_more_urgent_picks_the_higher_severity():
    assert more_urgent(Severity.LOW, Severity.HIGH) == Severity.HIGH
    assert more_urgent(Severity.EMERGENCY, Severity.LOW) == Severity.EMERGENCY
    assert more_urgent(Severity.MODERATE, Severity.MODERATE) == Severity.MODERATE


def test_benign_symptoms_stay_low():
    result = evaluate(_request(symptoms="Mild tiredness", duration="1 day", age=30))
    assert result.severity == Severity.LOW
    assert result.sos_recommended is False
    assert result.fired_rules == []


def test_emergency_keyword_forces_emergency_and_sos():
    result = evaluate(_request(symptoms="Sudden chest pain and sweating"))
    assert result.severity == Severity.EMERGENCY
    assert result.sos_recommended is True
    assert len(result.fired_rules) == 1
    assert "chest pain" in result.fired_rules[0]


def test_high_risk_keyword_bumps_to_high_without_sos():
    result = evaluate(_request(symptoms="I have a high fever and feel awful"))
    assert result.severity == Severity.HIGH
    assert result.sos_recommended is False


def test_emergency_keyword_takes_priority_over_high_risk_keyword():
    result = evaluate(_request(symptoms="High fever along with chest pain"))
    assert result.severity == Severity.EMERGENCY
    # Only the (higher-priority) emergency rule should fire, not both.
    assert len(result.fired_rules) == 1


def test_infant_age_bumps_low_to_moderate():
    result = evaluate(_request(symptoms="Mild fussiness", age=1))
    assert result.severity == Severity.MODERATE
    assert "infant" in result.fired_rules[0].lower()


def test_elderly_age_bumps_low_to_moderate():
    result = evaluate(_request(symptoms="Feeling a bit dizzy", age=70))
    assert result.severity == Severity.MODERATE


def test_working_age_adult_with_mild_symptoms_stays_low():
    result = evaluate(_request(symptoms="Mild tiredness", age=35))
    assert result.severity == Severity.LOW


def test_age_modifier_does_not_apply_when_already_above_low():
    # A high-risk keyword already pushed this to HIGH - age shouldn't
    # then downgrade or re-fire on top of it.
    result = evaluate(_request(symptoms="High fever", age=70))
    assert result.severity == Severity.HIGH
    assert len(result.fired_rules) == 1


def test_missing_age_is_handled_gracefully():
    # age can be None (anonymous callers without a passport still hit
    # validation before this runs in practice, but the engine itself
    # must not crash if it's ever called without one).
    result = evaluate(_request(symptoms="Mild tiredness", age=None))
    assert result.severity == Severity.LOW


def test_prolonged_duration_bumps_moderate_to_high():
    # age=70 -> MODERATE baseline, then duration bumps to HIGH.
    result = evaluate(_request(symptoms="Feeling dizzy", age=70, duration="3 weeks"))
    assert result.severity == Severity.HIGH
    assert len(result.fired_rules) == 2


def test_prolonged_duration_does_not_raise_an_already_low_result():
    # Duration only escalates MODERATE -> HIGH, it should never turn a
    # LOW result into anything higher on its own.
    result = evaluate(_request(symptoms="Mild tiredness", age=30, duration="3 weeks"))
    assert result.severity == Severity.LOW
