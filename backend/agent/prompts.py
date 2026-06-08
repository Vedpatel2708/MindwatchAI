"""
backend/agent/prompts.py — MINDWATCH
Concise prompts for the clinical assessment agent.
Shorter prompts = faster first token, fewer parse errors.
"""

# System prompt is kept short — the ReAct agent framework adds its own
# boilerplate about tools/format, so long system prompts cause confusion.
SYSTEM_PROMPT = """You are MINDWATCH, a clinical mental health screening AI.
Analyze the submitted text and produce a structured risk assessment.
Use your tools to investigate, then output a final JSON answer.
DISCLAIMER: For screening purposes only. Not a diagnostic tool."""


ASSESSMENT_PROMPT_TEMPLATE = """ASSESSMENT: {assessment_id}
Type: {input_type} | Risk (ML): {risk_level} | Crisis score: {crisis_score:.0%}
Depression: {depression_score:.0%} | Anxiety: {anxiety_score:.0%} | Emotion: {dominant_emotion}

TEXT:
{input_text}

INSTRUCTIONS:
1. Call analyze_symptom_patterns with the text above
2. Call check_crisis_indicators with the text above
3. Call get_resource_recommendations with the identified risk level
4. Output Final Answer as valid JSON (no markdown, no extra text):
{{
  "risk_level": "safe|low|moderate|high|crisis",
  "primary_concerns": ["..."],
  "detected_patterns": ["..."],
  "protective_factors": ["..."],
  "summary": "2-3 sentence clinical summary",
  "immediate_actions": ["action 1", "action 2"],
  "resources": [{{"name": "...", "contact": "...", "type": "..."}}],
  "follow_up_suggested": true
}}"""


def format_assessment_prompt(
    assessment_id: str,
    input_text: str,
    input_type: str,
    crisis_score: float,
    depression_score: float,
    anxiety_score: float,
    crisis_signal: float,
    dominant_emotion: str,
    risk_level: str,
    detected_symptoms: list,
) -> str:
    # Cap text at 800 chars — the agent doesn't need the full text,
    # the ML pipeline already scored it. Shorter = faster LLM response.
    truncated = input_text[:800]
    if len(input_text) > 800:
        truncated += "... [truncated]"

    return ASSESSMENT_PROMPT_TEMPLATE.format(
        assessment_id=assessment_id,
        input_type=input_type,
        crisis_score=crisis_score,
        depression_score=depression_score,
        anxiety_score=anxiety_score,
        dominant_emotion=dominant_emotion,
        risk_level=risk_level,
        input_text=truncated,
    )
