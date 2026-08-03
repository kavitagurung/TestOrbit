"""Verification for GitHub Actions OpenID Connect scheduler requests."""
import os

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
GITHUB_JWKS_URL = f"{GITHUB_ISSUER}/.well-known/jwks"
_jwks_client = PyJWKClient(GITHUB_JWKS_URL, cache_keys=True)


def verify_scheduler_oidc(authorization: str | None) -> None:
    """Accept only an OIDC token issued to this repository's GitHub Action."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing GitHub Actions identity")
    audience = os.getenv("GITHUB_OIDC_AUDIENCE", "")
    repository = os.getenv("GITHUB_OIDC_REPOSITORY", "")
    if not audience or not repository:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub OIDC scheduler is not configured")
    token = authorization.removeprefix("Bearer ")
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, signing_key, algorithms=["RS256"], audience=audience, issuer=GITHUB_ISSUER)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid GitHub Actions identity") from exc
    if claims.get("repository") != repository or claims.get("ref") != "refs/heads/main":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="GitHub Actions identity is not authorized")
