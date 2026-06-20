"""
LinkedIn API client — pure functions, no state, no LLM.

Uses the OAuth 2.0 Authorization Code flow and the REST Posts API.
All credentials are read from environment via app.config.Settings.
"""

from urllib.parse import urlencode

import httpx

_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
_POSTS_URL = "https://api.linkedin.com/rest/posts"
_LI_VERSION = "202605"


def get_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile w_member_social",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def exchange_code(
    code: str, client_id: str, client_secret: str, redirect_uri: str
) -> dict:
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            _TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


def get_userinfo(access_token: str) -> dict:
    with httpx.Client(timeout=15) as client:
        resp = client.get(
            _USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


def post_content(access_token: str, author_urn: str, text: str) -> str:
    """Post text content to LinkedIn. Returns the post ID from the response header."""
    payload = {
        "author": author_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            _POSTS_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "LinkedIn-Version": _LI_VERSION,
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        resp.raise_for_status()
        return resp.headers.get("x-restli-id", "")
