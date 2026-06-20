"""
Deterministic Python assembly — no LLM.

Concatenates the three locked sections (hook, body, CTA) and hashtags
into the final full_post string. Called by the orchestrator after the
BodyWriterAgent and CTAWriterAgent have each produced their section.
"""

from app.pipeline.schemas import BodyDraft, CTADraft


def assemble_post(hook: str, body: BodyDraft, cta: CTADraft) -> str:
    """Join hook + body + cta + hashtags with double newlines. Pure Python, no LLM."""
    tags = " ".join(f"#{t}" for t in cta.hashtags)
    parts = [p for p in (hook.strip(), body.body.strip(), cta.cta.strip(), tags) if p]
    return "\n\n".join(parts)
