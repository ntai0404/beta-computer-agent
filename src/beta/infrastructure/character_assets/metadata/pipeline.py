"""
infrastructure/character_assets/metadata/pipeline.py

Pipeline recommendation module. Recommends the optimal voice pipeline
based on the inventory of available character assets.
"""

from __future__ import annotations


class VoicePipelineRecommender:
    """
    Evaluates the available assets and recommends a voice pipeline.
    """

    def __init__(self, asset_inventory: list[dict]):
        self.inventory = asset_inventory

    def recommend(self) -> dict:
        """
        Returns a dictionary with the recommendation and reasoning.
        """
        has_rvc = any(asset.get("detected_type") == "rvc_candidate" for asset in self.inventory)
        
        voice_assets = [a for a in self.inventory if a.get("detected_type") == "voice_candidate"]
        transcript_assets = [a for a in self.inventory if a.get("detected_type") == "transcript_candidate"]
        
        has_audio = len(voice_assets) > 0
        has_many_audio = len(voice_assets) > 50
        has_transcripts = len(transcript_assets) > 0

        # Decision Tree
        if has_rvc:
            return {
                "recommendation": "Base TTS -> RVC",
                "reasoning": "An RVC model is available. This allows real-time voice conversion using a base system TTS.",
                "confidence": "high"
            }
            
        if has_many_audio and has_transcripts:
            return {
                "recommendation": "Direct/finetuned TTS",
                "reasoning": "A large amount of audio and transcripts are available, suitable for fine-tuning a TTS model (e.g. GPT-SoVITS).",
                "confidence": "high"
            }
            
        if has_audio and not has_transcripts:
            return {
                "recommendation": "RVC training or Transcript prep",
                "reasoning": "Audio references exist but lack transcripts. You can train an RVC model, or generate transcripts using an ASR tool to train a TTS.",
                "confidence": "medium"
            }
            
        if has_audio and has_transcripts:
            return {
                "recommendation": "Zero-shot/reference-conditioned TTS",
                "reasoning": "A few clean audio clips are available. These can be used directly as reference prompts for zero-shot TTS models (e.g. F5-TTS).",
                "confidence": "medium"
            }

        return {
            "recommendation": "Windows TTS fallback",
            "reasoning": "No voice assets (audio or models) were found in the scanned sources. Using default system voice.",
            "confidence": "low"
        }
