"""Prompts package for MCP server."""

from .sequence_analysis import (
    SEQUENCE_ANALYSIS_PROMPT,
    SequenceAnalysisPrompt,
    SequenceAnalysisPromptArgs,
    SequenceAnalysisType,
    SequenceScope
)

# Available prompts for MCP server
AVAILABLE_PROMPTS = {
    "d365fo_sequence_analysis": SEQUENCE_ANALYSIS_PROMPT
}

# Future: Additional prompt handlers will be implemented here
# Following the specification patterns for:
# - Entity analysis prompts
# - Query builder prompts  
# - Integration planning prompts
# - Troubleshooting prompts

__all__ = [
    "SEQUENCE_ANALYSIS_PROMPT",
    "SequenceAnalysisPrompt", 
    "SequenceAnalysisPromptArgs",
    "SequenceAnalysisType",
    "SequenceScope",
    "AVAILABLE_PROMPTS"
]