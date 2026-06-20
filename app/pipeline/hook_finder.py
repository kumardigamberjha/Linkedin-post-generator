"""
Agent 1 — Hook & Angle Finder.

Analyzes a topic and produces an angle strategy plus 3 hook options.
Temperature: 0.8 (highest — most creative agent)
"""

import json
import logging

from app.utils.pipeline_utils import call_llm_with_retry, make_llm, make_fallback_llm
from app.pipeline.schemas import AnglePack

logger = logging.getLogger(__name__)

HOOK_FINDER_TEMPERATURE = 0.8

HOOK_FINDER_PROMPT = """
ROLE: You do exactly one thing: analyze a topic and generate 3 LinkedIn hook options with an angle strategy.

INPUT:
- topic: {topic}
- niche: {niche}
- trending_context: {trending_context}

RULES:
- Generate exactly 3 hook options. Each hook must be under 15 words.
- Each hook must use a different style: one = number/stat, one = micro-story, one = contrarian claim.
- angle_type must be exactly one of: story / contrarian / how-to / lesson-learned
- cta_type must be exactly one of: question / soft-ask / observation
- selected_hook must be the strongest of the 3 for LinkedIn engagement (pick the most scroll-stopping).
- Do not write the full post. Only hooks and angle metadata.
- The most important rule: hooks must be SPECIFIC to the topic — no generic hooks that could apply to anything.

EXAMPLE of correct output for topic "vector databases":
{{
  "topic": "vector databases in production",
  "angle_type": "lesson-learned",
  "hook_options": [
    "We switched from Pinecone to Qdrant. Cut costs by 60%.",
    "3 months ago I had no idea what a vector database was. Now it runs our entire search.",
    "Everyone's adding vector search. Almost nobody is chunking their data correctly."
  ],
  "selected_hook": "Everyone's adding vector search. Almost nobody is chunking their data correctly.",
  "cta_type": "question"
}}

CRITICAL: Your response must be a JSON object {{ ... }}, NOT a JSON array [ ... ].

OUTPUT: Return ONLY valid JSON matching this schema exactly. No prose. No markdown fences.
{schema}
"""

_SCHEMA_HINT = json.dumps(
    {
        "topic": "string (the topic, possibly sharpened)",
        "angle_type": "one of: story | contrarian | how-to | lesson-learned",
        "hook_options": [
            "hook 1 (<15 words)",
            "hook 2 (<15 words)",
            "hook 3 (<15 words)",
        ],
        "selected_hook": "the single strongest hook copied verbatim from hook_options",
        "cta_type": "one of: question | soft-ask | observation",
    },
    indent=2,
)


class HookFinderAgent:
    def __init__(self, llm_provider: str):
        self.llm_provider = llm_provider
        self.llm = make_llm(llm_provider, HOOK_FINDER_TEMPERATURE, max_tokens=1024)
        self.fallback_llm = make_fallback_llm(
            HOOK_FINDER_TEMPERATURE, max_tokens=1024, primary_provider=llm_provider
        )

    async def run(
        self, topic: str, niche: str, trending_context: str = ""
    ) -> AnglePack:
        prompt = HOOK_FINDER_PROMPT.format(
            topic=topic,
            niche=niche,
            trending_context=trending_context or "(none)",
            schema=_SCHEMA_HINT,
        )

        angle: AnglePack = await call_llm_with_retry(
            self.llm,
            prompt,
            AnglePack,
            temperature=HOOK_FINDER_TEMPERATURE,
            max_retries=3,
            agent_name="HookFinder",
            fallback_llm=self.fallback_llm,
        )
        if not angle.topic:
            angle.topic = topic
        if angle.selected_hook not in angle.hook_options and angle.hook_options:
            angle.selected_hook = angle.hook_options[0]
        return angle
