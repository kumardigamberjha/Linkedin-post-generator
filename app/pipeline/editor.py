"""
Agent 4 — Editor.

Critiques AND fixes the post against the style spec and QA failures in a single call.
Called at most twice (orchestrator enforces the 2-cycle hard cap).
Temperature: 0.3
"""

import logging

from app.utils.pipeline_utils import call_llm_with_retry, make_llm, make_fallback_llm
from app.pipeline.schemas import EditedPost
from app.pipeline.style_spec import STYLE_COMPACT

logger = logging.getLogger(__name__)

EDITOR_TEMPERATURE = 0.3

EDITOR_PROMPT = """Fix the LinkedIn post below so it resolves every violation listed. Keep the original meaning.
Target: 200-280 words, under 3,000 characters. Return the complete rewritten post.

VIOLATIONS TO FIX:
{failed_rules}

POST (cycle {rewrite_cycle}/2):
{post_text}

VOICE & RULES:
{style_spec}

OUTPUT: valid JSON only, no prose, no fences.
{schema}"""

_SCHEMA_HINT = '{"revised_post":"<full corrected post>","hook_line":"<first line>","violations_fixed":[{"rule":"","offending_text":"","fix_applied":""}],"still_weak":false}'


class LinkedInEditorAgent:
    def __init__(self, llm_provider: str):
        self.llm_provider = llm_provider
        self.llm = make_llm(llm_provider, EDITOR_TEMPERATURE, max_tokens=2500)
        self.fallback_llm = make_fallback_llm(
            EDITOR_TEMPERATURE, max_tokens=2500, primary_provider=llm_provider
        )

    async def edit(self, post_text: str, qa_results: dict, cycle: int) -> EditedPost:
        failed_rules = [
            key
            for key, passed in qa_results.items()
            if key.startswith("passes_") and not passed
        ]

        error_context = "Failed Rules:\n" + "\n".join(f"- {r}" for r in failed_rules)
        if qa_results.get("long_lines"):
            error_context += "\n\nLines exceeding 12 words:\n" + "\n".join(
                f"- {line}" for line in qa_results["long_lines"]
            )
        if qa_results.get("packed_lines"):
            error_context += (
                "\n\nLines with multiple tips/sentences on one line (split each onto its own line):\n"
                + "\n".join(f"- {line}" for line in qa_results["packed_lines"])
            )
        if qa_results.get("banned_words_found"):
            error_context += "\n\nBanned words found:\n" + ", ".join(
                qa_results["banned_words_found"]
            )
        if qa_results.get("fake_stat_lines"):
            error_context += (
                "\n\nSuspected invented statistics (remove if not provided by the user):\n"
                + "\n".join(f"- {line}" for line in qa_results["fake_stat_lines"])
            )

        prompt = EDITOR_PROMPT.format(
            post_text=post_text,
            failed_rules=error_context,
            rewrite_cycle=cycle,
            style_spec=STYLE_COMPACT,
            schema=_SCHEMA_HINT,
        )

        edited: EditedPost = await call_llm_with_retry(
            self.llm,
            prompt,
            EditedPost,
            temperature=EDITOR_TEMPERATURE,
            max_retries=3,
            agent_name="Editor",
            fallback_llm=self.fallback_llm,
        )
        if not edited.revised_post.strip():
            edited.revised_post = post_text
        if not edited.hook_line:
            for line in edited.revised_post.split("\n"):
                if line.strip():
                    edited.hook_line = line.strip()
                    break
        return edited
