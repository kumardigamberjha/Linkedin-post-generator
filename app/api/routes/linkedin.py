"""
LinkedIn OAuth 2.0 + posting routes.

Routes (all mounted at app root — no /api prefix — so /callback matches the
redirect URI already registered in the LinkedIn Developer Portal):

  GET  /api/linkedin/auth     → redirects to LinkedIn consent screen
  GET  /callback              → receives auth code, exchanges for token,
                                redirects to frontend with ?li_token=...&li_uid=...
  POST /api/linkedin/post     → posts generated content to LinkedIn
"""

import logging
import secrets

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.linkedin_client import (
    exchange_code,
    get_auth_url,
    get_userinfo,
    post_content,
)

router = APIRouter()
logger = logging.getLogger(__name__)

_FRONTEND_URL = "http://localhost:5173"

# In-memory CSRF state store — single-user tool, process lifetime is fine
_pending_states: set[str] = set()


@router.get("/api/linkedin/auth")
def linkedin_auth():
    settings = get_settings()
    if not settings.linkedin_client_id:
        raise HTTPException(
            status_code=500, detail="LINKEDIN_CLIENT_ID is not configured in .env"
        )
    state = secrets.token_urlsafe(16)
    _pending_states.add(state)
    url = get_auth_url(
        settings.linkedin_client_id, settings.linkedin_redirect_uri, state
    )
    return RedirectResponse(url)


def _popup_html(payload_js: str) -> HTMLResponse:
    """Return a minimal HTML page that postMessages payload to the opener and closes."""
    html = f"""<!doctype html><html><head><title>LinkedIn Auth</title></head><body>
<p style="font-family:sans-serif;text-align:center;padding:40px;color:#555">
  Completing sign-in…
</p>
<script>
(function(){{
  var target = window.opener || window.parent;
  try {{
    target.postMessage({payload_js}, "{_FRONTEND_URL}");
  }} catch(e) {{}}
  window.close();
}})();
</script>
</body></html>"""
    return HTMLResponse(html)


@router.get("/callback")
def linkedin_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
):
    if error:
        logger.warning("LinkedIn OAuth error: %s", error)
        return _popup_html('{"type":"li_error","error":"access_denied"}')

    if not code or not state:
        return _popup_html('{"type":"li_error","error":"missing_params"}')

    if state not in _pending_states:
        return _popup_html('{"type":"li_error","error":"invalid_state"}')
    _pending_states.discard(state)

    settings = get_settings()
    try:
        token_data = exchange_code(
            code,
            settings.linkedin_client_id,
            settings.linkedin_client_secret,
            settings.linkedin_redirect_uri,
        )
        access_token = token_data["access_token"]
        userinfo = get_userinfo(access_token)
        user_id = userinfo["sub"]
    except Exception as exc:
        logger.error("LinkedIn token exchange failed: %s", exc)
        return _popup_html('{"type":"li_error","error":"token_exchange_failed"}')

    import json as _json

    payload = _json.dumps({"type": "li_auth", "token": access_token, "uid": user_id})
    return _popup_html(payload)


class LinkedInPostRequest(BaseModel):
    post_text: str
    access_token: str
    author_urn: str


@router.post("/api/linkedin/post")
def linkedin_post(req: LinkedInPostRequest):
    if not req.post_text.strip():
        raise HTTPException(status_code=400, detail="post_text is empty")
    try:
        post_id = post_content(req.access_token, req.author_urn, req.post_text)
        return {"success": True, "post_id": post_id}
    except Exception as exc:
        logger.error("LinkedIn post failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"LinkedIn API error: {exc}")
