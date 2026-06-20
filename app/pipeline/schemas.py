"""
Pydantic JSON contracts for the 5-stage LinkedIn pipeline.

All LLM outputs are parsed and validated against one of these models before
flowing to the next stage (see app.pipeline.utils.call_llm_with_retry).
"""

from pydantic import BaseModel, Field, field_validator

ANGLE_TYPES = {"story", "contrarian", "how-to", "lesson-learned"}
CTA_TYPES = {"question", "soft-ask", "observation"}


class AnglePack(BaseModel):
    topic: str
    angle_type: str
    hook_options: list[str] = Field(default_factory=list)
    selected_hook: str
    cta_type: str

    @field_validator("angle_type")
    @classmethod
    def validate_angle(cls, v: str) -> str:
        if v not in ANGLE_TYPES:
            raise ValueError(f"angle_type must be one of {sorted(ANGLE_TYPES)}")
        return v

    @field_validator("cta_type")
    @classmethod
    def validate_cta(cls, v: str) -> str:
        if v not in CTA_TYPES:
            raise ValueError(f"cta_type must be one of {sorted(CTA_TYPES)}")
        return v

    @field_validator("hook_options")
    @classmethod
    def validate_hooks(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError("hook_options must contain exactly 3 hooks")
        return v


class BodyDraft(BaseModel):
    body: str


class CTADraft(BaseModel):
    cta: str
    hashtags: list[str] = Field(default_factory=list)

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, v: list[str]) -> list[str]:
        if not (3 <= len(v) <= 5):
            raise ValueError("hashtags must have 3 to 5 items")
        return [tag.lower().lstrip("#") for tag in v]


class StyleViolation(BaseModel):
    rule: str = ""
    offending_text: str = ""
    fix_applied: str = ""


class EditedPost(BaseModel):
    revised_post: str
    hook_line: str = ""
    violations_fixed: list[StyleViolation] = Field(default_factory=list)
    still_weak: bool = False


class ApprovalResult(BaseModel):
    approved: bool = False
    reasons: list[str] = Field(default_factory=list)
    checklist: dict[str, bool] = Field(default_factory=dict)
