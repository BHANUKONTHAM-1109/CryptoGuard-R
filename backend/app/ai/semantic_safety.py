"""
CryptoGuard-R - Semantic Safety Filter (Asimov Protocol)
Evaluates workspace hazard intent, aggressive commands, & human threat in origin context.
"""
import re
from typing import Tuple

from app.core.logging import get_logger

logger = get_logger("semantic_safety")

# Threat Vectors mapping specific kinetic, violent, or hazardous language
THREAT_VECTORS = [
    # Explicit Violence & Lethality
    r"\b(kill|murder|assassinate|slaughter|execute)\b",
    # Physical Harm / Aggression
    r"\b(attack|detain|hit|crush|ram|smash|shoot|strike|injure|hurt|cut|slice|chop|dismember|harm|punch|kick|break)\b",
    # Workspace & Property Hazards
    r"\b(sabotage|explode|explosive|detonate|burn|destroy|demolish|crash|shatter|damage)\b",
    # Threat / Hostage
    r"\b(hostage|kidnap|trap|capture)\b",
    # Weaponization
    r"\b(weapon|gun|blade|laser|knife|sword|bomb|poison)\b"
]

def compile_threat_pattern():
    combined = "|".join(THREAT_VECTORS)
    return re.compile(combined, re.IGNORECASE)

THREAT_REGEX = compile_threat_pattern()

def evaluate_safety(text: str) -> Tuple[bool, str]:
    """
    Evaluates whether the given text contains language indicative of
    physical violence, workspace sabotage, or kinetic threats.
    
    Returns:
        (is_safe: bool, reason: str)
    """
    if not text:
        return True, "No context provided."
        
    match = THREAT_REGEX.search(text)
    if match:
        trigger_word = match.group(0).lower()
        reason = f"ASIMOV VIOLATION: Kinetic/Workspace threat language detected ('{trigger_word}')"
        logger.warning(f"Semantic Safety Failed. Trigger: {trigger_word}")
        return False, reason
        
    return True, "Safe. No kinetic threat detected."
