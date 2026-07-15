from ..schemas import StructuredFacts, Severity, SeverityResult

def evaluate_incident_severity(facts: StructuredFacts, victim_count: int) -> SeverityResult:
    """
    Computes emergency severity based on a deterministic rubric.
    
    Returns a SeverityResult containing the mapped Severity, score, and explanation.
    
    Severity logic operates in two stages:
      1. Critical Overrides: Life-threatening conditions immediately set severity to Critical (100).
      2. Scoring Rubric: If no overrides trigger, points accumulate based on secondary injuries.
    """
    # Stage 1: Critical Overrides (immediate life threats)
    if facts.unconsciousness:
        return SeverityResult(
            severity=Severity.CRITICAL,
            score=100,
            reason="Unconsciousness / unresponsive caller reported."
        )
    if facts.breathing_difficulty:
        return SeverityResult(
            severity=Severity.CRITICAL,
            score=100,
            reason="Severe breathing difficulty or respiratory compromise."
        )
    if facts.severe_bleeding:
        return SeverityResult(
            severity=Severity.CRITICAL,
            score=100,
            reason="Uncontrolled or severe arterial bleeding reported."
        )
    if facts.suspected_cardiac_emergency:
        return SeverityResult(
            severity=Severity.CRITICAL,
            score=100,
            reason="Suspected cardiac emergency (chest pain, possible heart attack)."
        )

    # Stage 2: Point Rubric (secondary injuries and scaling factors)
    score = 0
    reasons = []
    
    if facts.head_injury:
        score += 15
        reasons.append("conscious head injury")
        
    if facts.suspected_fracture:
        score += 15
        reasons.append("suspected skeletal fracture")
        
    # Scale severity slightly for multi-victim accidents
    if victim_count > 2:
        score += 10
        reasons.append(f"multiple victims ({victim_count})")
        
    # Stage 3: Threshold Mapping & Reason Compilation
    if score >= 40:
        reason_str = "Critical severity assigned due to cumulative factors: " + ", ".join(reasons) + "."
        return SeverityResult(severity=Severity.CRITICAL, score=score, reason=reason_str)
    elif score >= 15:
        reason_str = "Urgent severity assigned due to: " + ", ".join(reasons) + "."
        return SeverityResult(severity=Severity.URGENT, score=score, reason=reason_str)
    else:
        if reasons:
            reason_str = "Stable severity assigned due to: " + ", ".join(reasons) + "."
        else:
            reason_str = "Stable severity assigned; no critical or urgent indicators reported."
        return SeverityResult(severity=Severity.STABLE, score=score, reason=reason_str)
