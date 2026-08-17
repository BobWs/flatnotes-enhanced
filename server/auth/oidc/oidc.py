from datetime import datetime, timedelta

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

from helpers import get_env
from auth.models import Login, Token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token", auto_error=False)


class OIDCAuth:
    """
    Base OAuth2/OIDC auth. Shared JWT logic and authenticate().
    Subclasses implement get_authorization_url() and handle_callback().
    """
    JWT_ALGORITHM = "HS256"

    def __init__(self) -> None:
        self.client_id = get_env("OAUTH_CLIENT_ID", mandatory=True)
        self.client_secret = get_env("OAUTH_CLIENT_SECRET", mandatory=True)
        self.redirect_uri = get_env("OAUTH_REDIRECT_URI", mandatory=True)
        self.secret_key = get_env("FLATNOTES_SECRET_KEY", mandatory=True)
        self.session_expiry_days = get_env(
            "FLATNOTES_SESSION_EXPIRY_DAYS", default=30, cast_int=True
        )
        allowed = get_env("OAUTH_ALLOWED_USERS", mandatory=False, default="")
        self.allowed_users = (
            {u.strip().lower() for u in allowed.split(",") if u.strip()}
            if allowed else None
        )

    def _check_allowed(self, username: str):
        if self.allowed_users and username.lower() not in self.allowed_users:
            raise HTTPException(status_code=403, detail="User not allowed")

    def login(self, data: Login) -> Token:
        raise NotImplementedError("Use the OAuth flow.")

    def authenticate(self, request: Request, token: str = Depends(oauth2_scheme)):
        if token is None:
            for name, value in request.cookies.items():
                if (name == "token" or name.startswith("token_")) and value:
                    try:
                        self._validate_token(value)
                        token = value
                        break
                    except Exception:
                        continue
        if not self._validate_token_bool(token):
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    def _validate_token(self, token: str) -> bool:
        if token is None:
            raise ValueError("No token")
        payload = jwt.decode(token, self.secret_key, algorithms=[self.JWT_ALGORITHM])
        if payload.get("sub") is None:
            raise ValueError("Invalid subject")
        return True

    def _validate_token_bool(self, token: str) -> bool:
        try:
            return self._validate_token(token)
        except Exception:
            return False

    def _create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        to_encode["exp"] = datetime.utcnow() + timedelta(days=self.session_expiry_days)
        return jwt.encode(to_encode, self.secret_key, algorithm=self.JWT_ALGORITHM)

    def get_authorization_url(self) -> str:
        raise NotImplementedError

    async def handle_callback(self, code: str) -> Token:
        raise NotImplementedError


class GitHubAuth(OIDCAuth):
    """GitHub OAuth2 — no discovery URL needed."""

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"

    def get_authorization_url(self) -> str:
        return (
            f"{self.AUTHORIZE_URL}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope=read:user"
        )

    async def handle_callback(self, code: str) -> Token:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                self.TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            r.raise_for_status()
            github_token = r.json().get("access_token")
            if not github_token:
                raise HTTPException(status_code=401, detail="GitHub token exchange failed")

            r = await client.get(
                self.USER_URL,
                headers={"Authorization": f"Bearer {github_token}", "Accept": "application/json"},
            )
            r.raise_for_status()
            userinfo = r.json()

        username = userinfo.get("login")
        if not username:
            raise HTTPException(status_code=400, detail="Could not retrieve GitHub username")
        self._check_allowed(username)
        return Token(access_token=self._create_access_token({"sub": username}))


class GenericOIDCAuth(OIDCAuth):
    """
    Generic OIDC via discovery URL.
    Set OIDC_DISCOVERY_URL to your provider's
    /.well-known/openid-configuration endpoint.

    Client credentials priority:
      OIDC_CLIENT_ID     > OAUTH_CLIENT_ID
      OIDC_CLIENT_SECRET > OAUTH_CLIENT_SECRET
    """

    def __init__(self) -> None:
        super().__init__()
        self.client_id = get_env("OIDC_CLIENT_ID", mandatory=True)
        self.client_secret = get_env("OIDC_CLIENT_SECRET", mandatory=True)
        self.redirect_uri = get_env("OIDC_REDIRECT_URI", mandatory=True)
        self.discovery_url = get_env("OIDC_DISCOVERY_URL", mandatory=True)
        self._metadata: dict | None = None

    async def _get_metadata(self) -> dict:
        if self._metadata is None:
            async with httpx.AsyncClient() as client:
                r = await client.get(self.discovery_url)
                r.raise_for_status()
                self._metadata = r.json()
        return self._metadata

    def get_authorization_url(self) -> str:
        authorize_url = get_env("OIDC_AUTHORIZE_URL", mandatory=True)
        scope = get_env("OIDC_SCOPE", mandatory=False, default="openid email profile")
        return (
            f"{authorize_url}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope={scope}"
        )

    async def handle_callback(self, code: str) -> Token:
        meta = await self._get_metadata()
        async with httpx.AsyncClient() as client:
            r = await client.post(
                meta["token_endpoint"],
                headers={"Accept": "application/json"},
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            r.raise_for_status()
            token_data = r.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(status_code=401, detail="OIDC token exchange failed")

            r = await client.get(
                meta["userinfo_endpoint"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r.raise_for_status()
            userinfo = r.json()

        subject = userinfo.get("preferred_username") or userinfo.get("email") or userinfo.get("sub")
        if not subject:
            raise HTTPException(status_code=400, detail="No usable subject in OIDC userinfo")
        self._check_allowed(subject)
        return Token(access_token=self._create_access_token({"sub": subject}))


def make_oidc_auth() -> OIDCAuth:
    """Factory — returns the right backend based on AUTH_PROVIDER."""
    provider = get_env("AUTH_PROVIDER", mandatory=False, default="github").lower()
    if provider == "github":
        return GitHubAuth()
    elif provider == "oidc":
        return GenericOIDCAuth()
    else:
        raise ValueError(f"Unknown AUTH_PROVIDER '{provider}'. Use 'github' or 'oidc'.")
