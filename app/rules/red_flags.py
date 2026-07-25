"""
Keyword lists used by the deterministic rule engine (app/rules/engine.py)
and, for consistency, by the Gemini-unavailable fallback
(app/ai/fallback.py). This is the SINGLE source of truth for these lists -
nothing else should keep its own separate copy, so escalation criteria
can never drift apart between the two systems that both rely on them.

Simple substring matching on purpose: this is a safety net, not an NLP
system. False positives (over-escalating) are the safe failure direction
here - it's always better to flag something as more urgent than it turns
out to be than the reverse.
"""

# Immediately life-threatening or clearly emergency-grade descriptions.
# Deliberately short and unambiguous - not meant to be exhaustive.
EMERGENCY_KEYWORDS = [
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "shortness of breath",
    "not breathing",
    "unconscious",
    "unresponsive",
    "severe bleeding",
    "uncontrolled bleeding",
    "stroke",
    "slurred speech",
    "face drooping",
    "sudden numbness",
    "severe allergic reaction",
    "anaphylaxis",
    "suicidal",
    "overdose",
    "seizure",
]

# Serious enough to warrant medical attention soon, but not on their own
# immediately life-threatening the way the emergency list is - these
# raise a symptom set to at least HIGH rather than leaving it at
# LOW/MODERATE.
HIGH_RISK_KEYWORDS = [
    "high fever",
    "blood in stool",
    "blood in vomit",
    "blood in urine",
    "coughing blood",
    "persistent vomiting",
    "severe pain",
    "severe headache",
    "worst headache",
    "signs of dehydration",
    "fainting",
    "fainted",
    "confusion",
    "disoriented",
]
