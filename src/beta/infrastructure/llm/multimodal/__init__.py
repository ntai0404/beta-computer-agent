"""
infrastructure/llm/multimodal — multimodal LLM abstraction for voice analysis.

Public exports:
  - MultimodalVoiceAnalyzer (abstract base)
  - AnalysisCapabilities
  - AnalysisRequest
  - AnalysisResult
  - VoiceHintAnalyzer (orchestrator)
  - VoiceHint, SpeakingStyleHint, AudioQualityAssessment (contracts)
  - ANALYSIS_PROMPT_TEMPLATE
"""
from beta.infrastructure.llm.multimodal.base import (
    AnalysisCapabilities,
    AnalysisRequest,
    AnalysisResult,
    MultimodalVoiceAnalyzer,
)
from beta.infrastructure.llm.multimodal.voice_hint_contracts import (
    AudioQualityAssessment,
    SpeakingStyleHint,
    SourceReference,
    VoiceHint,
)
from beta.infrastructure.llm.multimodal.voice_hint_analyzer import (
    ANALYSIS_PROMPT_TEMPLATE,
    VoiceHintAnalyzer,
    build_analysis_prompt,
)

__all__ = [
    "MultimodalVoiceAnalyzer",
    "AnalysisCapabilities",
    "AnalysisRequest",
    "AnalysisResult",
    "VoiceHint",
    "SpeakingStyleHint",
    "AudioQualityAssessment",
    "SourceReference",
    "VoiceHintAnalyzer",
    "ANALYSIS_PROMPT_TEMPLATE",
    "build_analysis_prompt",
]
