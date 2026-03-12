# app/services/oauth_service.py
"""
OAuth 2.0 Service for HabitFlow
Handles Google and GitHub social sign-in using the Authorization Code flow.

How it works:
1. Generate a cryptographically secure state token (CSRF protection)
2. Open the system browser at the provider's authorization URL
3. Spin up a temporary local HTTP server on localhost:8765 to capture the callback
4. Exchange the authorization code for an access token
5. Fetch the user's profile (email, name) from the provider
6. Return structured user info to the caller
"""
import os
import secrets
import threading
import webbrowser
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
from typing import Optional, Tuple

import requests

# ── Provider endpoints ────────────────────────────────────────────────────────

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"
GITHUB_USER_EMAILS_URL = "https://api.github.com/user/emails"

# Local callback server
CALLBACK_PORT = 8765
REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}/oauth/callback"


# ── Callback HTTP handler ─────────────────────────────────────────────────────

class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that captures the OAuth redirect and responds with a
    friendly HTML page so the browser doesn't show a raw error."""

    # Class-level slot shared across all handler instances within a request
    result: Optional[dict] = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/oauth/callback":
            params = parse_qs(parsed.query)
            _OAuthCallbackHandler.result = {
                "code": params.get("code", [None])[0],
                "state": params.get("state", [None])[0],
                "error": params.get("error", [None])[0],
            }
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                b"<h2 style='color:#10B981'>Authentication successful!</h2>"
                b"<p>You may close this tab and return to HabitFlow.</p>"
                b"<script>setTimeout(()=>window.close(),1500)</script>"
                b"</body></html>"
            )
            # Shut the server down from a daemon thread so do_GET can return
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        pass  # Suppress console noise


# ── Main service class ────────────────────────────────────────────────────────

class OAuthService:
    """Handles OAuth 2.0 authorization-code flows for Google and GitHub."""

    def __init__(self):
        self._state_token: Optional[str] = None

    # ── CSRF helpers ──────────────────────────────────────────────────────────

    def _generate_state(self) -> str:
        """Return a new cryptographically-secure state token and store it."""
        self._state_token = secrets.token_urlsafe(32)
        return self._state_token

    def _verify_state(self, state: str) -> bool:
        """Constant-time comparison to prevent CSRF attacks."""
        if not self._state_token or not state:
            return False
        return secrets.compare_digest(self._state_token, state)

    # ── Local callback server ─────────────────────────────────────────────────

    def _wait_for_callback(self, timeout: int = 120) -> Optional[dict]:
        """
        Start a local HTTP server on CALLBACK_PORT, wait up to *timeout* seconds
        for the OAuth provider to redirect back, then shut the server down.

        Returns the parsed query params dict, or None on timeout.
        """
        _OAuthCallbackHandler.result = None

        try:
            server = HTTPServer(("localhost", CALLBACK_PORT), _OAuthCallbackHandler)
        except OSError:
            # Port already in use – another instance may be running
            return None

        server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            server.shutdown()

        return _OAuthCallbackHandler.result

    # ── Google OAuth ──────────────────────────────────────────────────────────

    def is_google_configured(self) -> bool:
        """Return True if Google OAuth credentials are present in the environment."""
        return bool(os.getenv("GOOGLE_CLIENT_ID")) and bool(os.getenv("GOOGLE_CLIENT_SECRET"))

    def is_github_configured(self) -> bool:
        """Return True if GitHub OAuth credentials are present in the environment."""
        return bool(os.getenv("GITHUB_CLIENT_ID")) and bool(os.getenv("GITHUB_CLIENT_SECRET"))

    def _build_google_url(self) -> Optional[str]:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
            return None
        params = {
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": self._generate_state(),
            "access_type": "online",
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    def complete_google_signin(self) -> Tuple[bool, str, Optional[dict]]:
        """
        Launch the system browser for Google sign-in, wait for the callback,
        exchange the code, and return (success, message, user_info).

        user_info keys: email, name, provider, provider_id
        """
        url = self._build_google_url()
        if not url:
            return (
                False,
                "Google sign-in is not configured.\n"
                "Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file.",
                None,
            )

        webbrowser.open(url)
        callback = self._wait_for_callback()

        if callback is None:
            return False, "Authentication timed out. Please try again.", None
        if callback.get("error"):
            return False, "Google sign-in was cancelled or denied.", None
        if not self._verify_state(callback.get("state", "")):
            return False, "Security error: state token mismatch. Please try again.", None

        # Exchange authorization code for tokens
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        try:
            token_resp = requests.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": callback["code"],
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                timeout=15,
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()
        except Exception:
            return False, "Failed to exchange authorization code with Google.", None

        access_token = tokens.get("access_token")
        if not access_token:
            return False, "Google did not return an access token.", None

        # Fetch user profile
        try:
            user_resp = requests.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=15,
            )
            user_resp.raise_for_status()
            profile = user_resp.json()
        except Exception:
            return False, "Failed to retrieve profile from Google.", None

        email = profile.get("email")
        if not email:
            return False, "Google account did not provide an email address.", None
        if not profile.get("email_verified", False):
            return False, "Google account email is not verified.", None

        return True, "Google sign-in successful", {
            "email": email,
            "name": profile.get("name", ""),
            "provider": "google",
            "provider_id": profile.get("sub", ""),
        }

    # ── GitHub OAuth ──────────────────────────────────────────────────────────

    def _build_github_url(self) -> Optional[str]:
        client_id = os.getenv("GITHUB_CLIENT_ID")
        if not client_id:
            return None
        params = {
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "scope": "read:user user:email",
            "state": self._generate_state(),
        }
        return f"{GITHUB_AUTH_URL}?{urlencode(params)}"

    def complete_github_signin(self) -> Tuple[bool, str, Optional[dict]]:
        """
        Launch the system browser for GitHub sign-in, wait for the callback,
        exchange the code, and return (success, message, user_info).

        user_info keys: email, name, provider, provider_id
        """
        url = self._build_github_url()
        if not url:
            return (
                False,
                "GitHub sign-in is not configured.\n"
                "Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to your .env file.",
                None,
            )

        webbrowser.open(url)
        callback = self._wait_for_callback()

        if callback is None:
            return False, "Authentication timed out. Please try again.", None
        if callback.get("error"):
            return False, "GitHub sign-in was cancelled or denied.", None
        if not self._verify_state(callback.get("state", "")):
            return False, "Security error: state token mismatch. Please try again.", None

        # Exchange authorization code for tokens
        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        try:
            token_resp = requests.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": callback["code"],
                    "redirect_uri": REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
                timeout=15,
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()
        except Exception:
            return False, "Failed to exchange authorization code with GitHub.", None

        access_token = tokens.get("access_token")
        if not access_token:
            return False, "GitHub did not return an access token.", None

        # Fetch user profile
        gh_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        try:
            user_resp = requests.get(GITHUB_USERINFO_URL, headers=gh_headers, timeout=15)
            user_resp.raise_for_status()
            profile = user_resp.json()
        except Exception:
            return False, "Failed to retrieve profile from GitHub.", None

        # GitHub users may hide their primary email; fetch from /user/emails
        email = profile.get("email")
        if not email:
            try:
                emails_resp = requests.get(GITHUB_USER_EMAILS_URL, headers=gh_headers, timeout=15)
                emails_resp.raise_for_status()
                emails = emails_resp.json()
                primary = next(
                    (e for e in emails if e.get("primary") and e.get("verified")), None
                )
                if primary:
                    email = primary["email"]
            except Exception:
                pass

        if not email:
            return (
                False,
                "GitHub account did not expose a verified email address.\n"
                "Please make your primary email public in GitHub settings.",
                None,
            )

        return True, "GitHub sign-in successful", {
            "email": email,
            "name": profile.get("name") or profile.get("login", ""),
            "provider": "github",
            "provider_id": str(profile.get("id", "")),
        }


# Module-level singleton so the state token is preserved across calls
oauth_service = OAuthService()
