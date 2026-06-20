"""
LinkedInPipelineOrchestrator — wires the 7-phase pipeline.

Flow:
    Hook & Angle
    → Body Write  (body only, hook locked)
    → CTA Write   (CTA + hashtags, hook + body locked)
    → Python Assembly  (no LLM)
    → [Python QA → Edit] ×≤2
    → Final QA
    → Approve  (pure Python)

Hard caps:
    - Hook is locked after Phase 1; downstream agents receive it as read-only context.
    - Body and CTA are each written in one LLM call.
    - Assembly is deterministic Python — no model arithmetic.
    - Max 2 editor rewrite cycles.
    - Python QA checker does ALL counting / measuring / detection.
    - Editor only called when Python QA finds a problem.
    - Approver is pure Python — no LLM call.
"""

import logging

from app.pipeline.approver import LinkedInApproverAgent
from app.pipeline.body_writer import BodyWriterAgent
from app.pipeline.cta_writer import CTAWriterAgent
from app.pipeline.editor import LinkedInEditorAgent
from app.pipeline.hook_finder import HookFinderAgent
from app.pipeline.post_writer import assemble_post
from app.pipeline.qa_checker import LinkedInQAChecker

logger = logging.getLogger(__name__)

MAX_REWRITE_CYCLES = 2


class LinkedInPipelineOrchestrator:
    def __init__(self, llm_provider: str, run_id: str = "default", step_callback=None):
        """
        Args:
            llm_provider:  "ollama" | "groq" | "nvidia" | "openai" | "anthropic" | "google"
            run_id:        Telemetry / logging identifier.
            step_callback: Optional sync callable(agent_name, task_name, output_str)
                           invoked after each agent so a WebSocket layer can stream progress.
        """
        self.llm_provider = llm_provider
        self.run_id = run_id
        self.step_callback = step_callback

    def _emit(self, agent_name: str, task_name: str, output) -> None:
        if not self.step_callback:
            return
        try:
            payload = (
                output.model_dump_json()
                if hasattr(output, "model_dump_json")
                else str(output)
            )
            self.step_callback(agent_name, task_name, payload)
        except Exception as exc:
            logger.debug("step_callback raised (ignored): %s", exc)

    async def run(self, topic: str, niche: str, user_id: str = "") -> dict:
        # ── ONE-TIME API HEALTH CHECK FOR SPEED OPTIMIZATION ──────────────────
        from app.utils.pipeline_utils import check_gemini_health

        logger.info(
            "Performing one-time health check on model provider: %s", self.llm_provider
        )
        is_healthy = await check_gemini_health(self.llm_provider)
        if not is_healthy:
            logger.warning(
                "Primary model health check failed. Generation will still be attempted to allow for recovery."
            )

        # ── PHASE 1 — HOOK & ANGLE ────────────────────────────────────────
        hook_finder = HookFinderAgent(self.llm_provider)
        angle_pack = await hook_finder.run(topic, niche, trending_context="")
        self._emit("LinkedIn Hook Finder", "Find Angle & Hooks", angle_pack)

        locked_hook = angle_pack.selected_hook

        # ── PHASE 2 — BODY WRITE ──────────────────────────────────────────
        body_writer = BodyWriterAgent(self.llm_provider)
        body_draft = await body_writer.write(angle_pack, niche)
        self._emit("LinkedIn Body Writer", "Write Post Body", body_draft)

        # ── PHASE 3 — CTA WRITE ───────────────────────────────────────────
        cta_writer = CTAWriterAgent(self.llm_provider)
        cta_draft = await cta_writer.write(
            locked_hook=locked_hook,
            body_text=body_draft.body,
            cta_type=angle_pack.cta_type,
        )
        self._emit("LinkedIn CTA Writer", "Write CTA & Hashtags", cta_draft)

        # ── PHASE 4 — PYTHON ASSEMBLY (no LLM) ───────────────────────────
        current_post_text = assemble_post(locked_hook, body_draft, cta_draft)
        self._emit("LinkedIn Assembler", "Assemble Full Post", current_post_text)

        # ── PHASE 5 — EDIT LOOP (max 2 cycles, only when QA finds problems)
        editor = LinkedInEditorAgent(self.llm_provider)
        qa = LinkedInQAChecker()
        still_weak = False
        cycles_taken = 0

        for cycle in range(1, MAX_REWRITE_CYCLES + 1):
            cycles_taken = cycle
            qa_results = qa.check(current_post_text)
            self._emit(
                "LinkedIn QA Checker", f"Python QA cycle {cycle}", str(qa_results)
            )

            if qa_results["overall_pass"]:
                break

            try:
                edited = await editor.edit(current_post_text, qa_results, cycle)
                self._emit("LinkedIn Editor", f"Edit cycle {cycle}", edited)
                current_post_text = edited.revised_post
                still_weak = edited.still_weak
            except Exception as exc:
                logger.warning(
                    "Editor failed on cycle %d: %s — keeping current text", cycle, exc
                )
                self._emit("LinkedIn Editor", f"Edit cycle {cycle} (failed)", str(exc))
                still_weak = cycle == MAX_REWRITE_CYCLES

            if still_weak and cycle == MAX_REWRITE_CYCLES:
                break

        # ── PHASE 6 — FINAL PYTHON QA ─────────────────────────────────────
        final_qa = qa.check(current_post_text)
        self._emit("LinkedIn QA Checker", "Final Python QA", str(final_qa))

        # ── PHASE 7 — APPROVER (pure Python) ──────────────────────────────
        approver = LinkedInApproverAgent(self.llm_provider)
        approval = await approver.approve(topic, final_qa, still_weak)
        self._emit("LinkedIn Approver", "Final Approval", approval)

        return {
            "post_text": current_post_text,
            "hook": final_qa.get("first_line", ""),
            "angle_type": angle_pack.angle_type,
            "word_count": final_qa.get("word_count", 0),
            "char_count": final_qa.get("char_count", 0),
            "hashtag_count": final_qa.get("hashtag_count", 0),
            "approved": approval.approved,
            "approval_reasons": approval.reasons,
            "qa_results": final_qa,
            "cycles_taken": cycles_taken,
        }
