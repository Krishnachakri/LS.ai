import sys
import os

# Ensure backend root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas import StructuredFacts, Severity
from app.services.severity_rubric import evaluate_incident_severity

def test_override_unconscious():
    facts = StructuredFacts(unconsciousness=True)
    res = evaluate_incident_severity(facts, victim_count=1)
    assert res.severity == Severity.CRITICAL
    assert res.score == 100
    assert "Unconsciousness" in res.reason

def test_override_breathing():
    facts = StructuredFacts(breathing_difficulty=True)
    res = evaluate_incident_severity(facts, victim_count=1)
    assert res.severity == Severity.CRITICAL
    assert res.score == 100
    assert "breathing difficulty" in res.reason.lower()

def test_override_bleeding():
    facts = StructuredFacts(severe_bleeding=True)
    res = evaluate_incident_severity(facts, victim_count=1)
    assert res.severity == Severity.CRITICAL
    assert res.score == 100
    assert "bleeding" in res.reason.lower()

def test_override_cardiac():
    facts = StructuredFacts(suspected_cardiac_emergency=True)
    res = evaluate_incident_severity(facts, victim_count=1)
    assert res.severity == Severity.CRITICAL
    assert res.score == 100
    assert "cardiac" in res.reason.lower()

def test_urgent_head_injury():
    facts = StructuredFacts(head_injury=True)
    res = evaluate_incident_severity(facts, victim_count=1)
    assert res.severity == Severity.URGENT
    assert res.score == 15
    assert "head injury" in res.reason.lower()

def test_urgent_fracture():
    facts = StructuredFacts(suspected_fracture=True)
    res = evaluate_incident_severity(facts, victim_count=1)
    assert res.severity == Severity.URGENT
    assert res.score == 15
    assert "fracture" in res.reason.lower()

def test_urgent_head_and_fracture():
    facts = StructuredFacts(head_injury=True, suspected_fracture=True)
    res = evaluate_incident_severity(facts, victim_count=1)
    assert res.severity == Severity.URGENT
    assert res.score == 30
    assert "head injury" in res.reason.lower()
    assert "fracture" in res.reason.lower()

def test_stable_empty():
    facts = StructuredFacts()
    res = evaluate_incident_severity(facts, victim_count=1)
    assert res.severity == Severity.STABLE
    assert res.score == 0
    assert "Stable" in res.reason

def test_stable_multi_victim():
    facts = StructuredFacts()
    res = evaluate_incident_severity(facts, victim_count=3)
    assert res.severity == Severity.STABLE
    assert res.score == 10
    assert "multiple victims" in res.reason.lower()

def test_critical_cumulative():
    # Head injury (15) + Fracture (15) + Multi-victim (10) = 40 -> Critical
    facts = StructuredFacts(head_injury=True, suspected_fracture=True)
    res = evaluate_incident_severity(facts, victim_count=3)
    assert res.severity == Severity.CRITICAL
    assert res.score == 40
    assert "cumulative" in res.reason.lower()
    assert "head injury" in res.reason.lower()
    assert "fracture" in res.reason.lower()

def test_urgent_fracture_multi_victim():
    # Fracture (15) + Multi-victim (10) = 25 -> Urgent
    facts = StructuredFacts(suspected_fracture=True)
    res = evaluate_incident_severity(facts, victim_count=3)
    assert res.severity == Severity.URGENT
    assert res.score == 25
    assert "fracture" in res.reason.lower()

def test_stable_two_victims():
    # Two victims does not trigger multi-victim escalation (>2 required) -> 0 score -> Stable
    facts = StructuredFacts()
    res = evaluate_incident_severity(facts, victim_count=2)
    assert res.severity == Severity.STABLE
    assert res.score == 0
