"""
infrastructure/character_assets/metadata/identity.py

Identity resolution module. Gathers evidence from various sources
and attempts to determine the canonical character identity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ResolutionStatus(str, Enum):
    UNRESOLVED = "unresolved"
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    CONFLICTING = "conflicting"


@dataclass(frozen=True)
class IdentityEvidence:
    source_name: str
    """E.g., 'desktop-gremlin', 'voice-dataset', 'user-alias'"""
    
    value: str
    """The character ID or name found, e.g. 'matikanetannhauser'"""
    
    confidence: str
    """'high' (direct ID), 'medium' (folder name), 'low' (file name)"""
    
    context: str
    """Specific context, e.g. 'Found in config.txt'"""


class IdentityResolver:
    """
    Aggregates evidence to determine canonical character ID.
    """
    
    def __init__(self, persona_alias: str):
        self.persona_alias = persona_alias
        self.evidence_list: list[IdentityEvidence] = []
        
        # Add alias as baseline low-confidence evidence
        self.add_evidence(
            source_name="user-alias",
            value=persona_alias.lower(),
            confidence="low",
            context="User provided alias"
        )
        
    def add_evidence(self, source_name: str, value: str, confidence: str, context: str) -> None:
        """Add a piece of evidence for canonical identity."""
        ev = IdentityEvidence(
            source_name=source_name,
            value=value.lower().strip(),
            confidence=confidence,
            context=context
        )
        self.evidence_list.append(ev)
        logger.debug(f"Added identity evidence: {ev}")
        
    def resolve(self) -> tuple[ResolutionStatus, Optional[str]]:
        """
        Analyze evidence to determine the canonical character ID and status.
        
        Rules:
        - "verified" requires at least 1 'high' confidence, OR 2 matching 'medium'.
        - "conflicting" occurs if high/medium evidence point to different IDs.
        - "candidate" if there is only 1 'medium' or multiple 'low'.
        - "unresolved" otherwise.
        """
        
        high_evidence = [e for e in self.evidence_list if e.confidence == "high"]
        medium_evidence = [e for e in self.evidence_list if e.confidence == "medium"]
        
        # Check for conflicts among high evidence
        high_values = set(e.value for e in high_evidence)
        if len(high_values) > 1:
            return ResolutionStatus.CONFLICTING, None
            
        if len(high_values) == 1:
            return ResolutionStatus.VERIFIED, high_values.pop()
            
        # Check medium evidence
        medium_values = set(e.value for e in medium_evidence)
        if len(medium_values) > 1:
            return ResolutionStatus.CONFLICTING, None
            
        if len(medium_values) == 1:
            val = medium_values.pop()
            if len(medium_evidence) >= 2:
                return ResolutionStatus.VERIFIED, val
            return ResolutionStatus.CANDIDATE, val
            
        # Only low evidence remains
        low_values = set(e.value for e in self.evidence_list if e.confidence == "low")
        if len(low_values) == 1:
            # If the only low evidence is the alias, it's unresolved.
            # If there's other low evidence matching the alias, maybe candidate.
            non_alias_low = [e for e in self.evidence_list if e.confidence == "low" and e.source_name != "user-alias"]
            if non_alias_low:
                return ResolutionStatus.CANDIDATE, low_values.pop()
            return ResolutionStatus.UNRESOLVED, None
            
        if len(low_values) > 1:
            return ResolutionStatus.CONFLICTING, None
            
        return ResolutionStatus.UNRESOLVED, None
        
    def get_all_evidence(self) -> list[dict]:
        """Return a serialized list of evidence for reporting."""
        return [
            {
                "source": e.source_name,
                "value": e.value,
                "confidence": e.confidence,
                "context": e.context
            }
            for e in self.evidence_list
        ]
