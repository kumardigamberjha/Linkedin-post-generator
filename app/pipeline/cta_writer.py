"""
Agent 3 — CTA & Hashtag Writer.

Writes ONLY the closing call-to-action and hashtags.
Receives the locked hook and body text as context for coherence.
Must NOT rewrite either — only add the ending.
Temperature: 0.7
"""

import logging

from app.utils.pipeline_utils import call_llm_with_retry, make_llm, make_fallback_llm
from app.pipeline.schemas import CTADraft

logger = logging.getLogger(__name__)

CTA_WRITER_TEMPERATURE = 0.7

CTA_WRITER_PROMPT = """Write ONLY the closing CTA and hashtags for a LinkedIn post. Do NOT reproduce the hook or body. Do NOT provide critique, suggestions, or conversational text.

hook (context): {locked_hook}
body (context): {body_text}
cta_type: {cta_type}

RULES:
• CTA: exactly one {cta_type}. Max 20-30 words. No stacked asks ("Like AND comment AND share").
  - question → genuine question inviting replies
  - soft-ask → one ask: save, follow, or repost
  - observation → closing thought that invites reflection
• Hashtags: 3-5 lowercase, own final line, space-separated. Match the niche of the post.
• Voice: Hormozi × Fireship × Shaan Puri — punchy, direct, sounds like a real person.
• Example of a strong Shaan/Hormozi-style ending (observation):
  "People don't buy AI. They buy status.
  The fastest-growing AI products simply package that status into something users can share."

OUTPUT: valid JSON only, no prose, no critique, no fences.
{schema}"""

_SCHEMA_HINT = (
    '{"cta":"<one closing line, no hashtags>","hashtags":["tag1","tag2","tag3"]}'
)


class CTAWriterAgent:
    def __init__(self, llm_provider: str):
        self.llm_provider = llm_provider
        self.llm = make_llm(llm_provider, CTA_WRITER_TEMPERATURE, max_tokens=1024)
        self.fallback_llm = make_fallback_llm(
            CTA_WRITER_TEMPERATURE, max_tokens=1024, primary_provider=llm_provider
        )

    async def write(self, locked_hook: str, body_text: str, cta_type: str) -> CTADraft:
        prompt = CTA_WRITER_PROMPT.format(
            locked_hook=locked_hook,
            body_text=body_text,
            cta_type=cta_type,
            schema=_SCHEMA_HINT,
        )

        draft: CTADraft = await call_llm_with_retry(
            self.llm,
            prompt,
            CTADraft,
            temperature=CTA_WRITER_TEMPERATURE,
            max_retries=3,
            agent_name="CTAWriter",
            fallback_llm=self.fallback_llm,
        )
        return draft
