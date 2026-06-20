"""
Agent 2 — Body Writer.

Writes ONLY the middle/body of the LinkedIn post in one call.
The hook is locked and passed as context; must NOT be rewritten.
The CTA is written separately by CTAWriterAgent.
Temperature: 0.7
"""

import logging

from app.utils.pipeline_utils import call_llm_with_retry, make_llm, make_fallback_llm
from app.pipeline.schemas import AnglePack, BodyDraft
from app.pipeline.style_spec import STYLE_WITH_EXAMPLE

logger = logging.getLogger(__name__)

BODY_WRITER_TEMPERATURE = 0.7

BODY_WRITER_PROMPT = """Write ONLY the body section of a LinkedIn post. Hook is locked — do NOT repeat it. No CTA, no hashtags.

topic: {topic} | angle: {angle_type} | niche: {niche}
locked_hook (context only): {locked_hook}

STRUCTURE: Observation → Example → Mental Model → Advice.

BLANK LINE RULE: \n\n ONLY between the 4 numbered sections below. Sentences within the same section form a paragraph — NO blank line between them.

1. OBSERVATION + EXAMPLE — a sharp observation most readers recognize, followed in the SAME paragraph by a specific concrete scenario ("A team I know…", "Most [niche] engineers I've seen…"). 3-4 sentences total, no blank line within this paragraph.

2. MENTAL MODEL — walk through the hidden mechanism step by step. 3-4 sentences in one paragraph. End with the KILLER LINE: one sentence that compresses the insight into a memorable mental model. Do NOT state it at the start — build to it.

3. ADVICE — the counterintuitive shift. Max 3 steps. Each step gets its own line with a blank line before it (these are action steps, so they DO get spacing). 12-25 words per step.

4. PAYOFF — close with a personal observation framed as something witnessed: "I watched...", "Every team I've seen try this...". 2-3 sentences, one paragraph, no blank line within.

CONSTRAINTS: 170-250 words. No "I think / maybe / could potentially". Each of the 4 sections is its own block — \n\n between sections, sentences within a section flow together.

STYLE:
{style_spec}

OUTPUT: valid JSON only, no prose, no fences.
{schema}"""

_SCHEMA_HINT = '{"body":"<body text — \\\\n\\\\n ONLY between the 4 sections, NOT between sentences within a section. No hook, no CTA, no hashtags>"}'


class BodyWriterAgent:
    def __init__(self, llm_provider: str):
        self.llm_provider = llm_provider
        self.llm = make_llm(llm_provider, BODY_WRITER_TEMPERATURE, max_tokens=1500)
        self.fallback_llm = make_fallback_llm(
            BODY_WRITER_TEMPERATURE, max_tokens=1500, primary_provider=llm_provider
        )

    async def write(self, angle_pack: AnglePack, niche: str) -> BodyDraft:
        prompt = BODY_WRITER_PROMPT.format(
            locked_hook=angle_pack.selected_hook,
            topic=angle_pack.topic,
            angle_type=angle_pack.angle_type,
            niche=niche,
            style_spec=STYLE_WITH_EXAMPLE,
            schema=_SCHEMA_HINT,
        )

        draft: BodyDraft = await call_llm_with_retry(
            self.llm,
            prompt,
            BodyDraft,
            temperature=BODY_WRITER_TEMPERATURE,
            max_retries=3,
            agent_name="BodyWriter",
            fallback_llm=self.fallback_llm,
        )
        return draft
