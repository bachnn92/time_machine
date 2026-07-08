"""Repository service API helpers for GitHub, GitLab, and Bitbucket."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import json
from urllib import error, parse, request


PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "github": {
        "label": "GitHub",
        "base_url": "https://api.github.com",
    },
    "gitlab": {
        "label": "GitLab",
        "base_url": "https://gitlab.com/api/v4",
    },
    "bitbucket": {
        "label": "Bitbucket",
        "base_url": "https://api.bitbucket.org/2.0",
    },
}


@dataclass(frozen=True)
class RepositoryActionResult:
    ok: bool
    message: str
    url: str
    status_code: int | None = None


def normalize_provider(value: str) -> str:
    return (value or "github").strip().lower()


def provider_defaults(provider: str) -> dict[str, str]:
    normalized = normalize_provider(provider)
    preset = PROVIDER_PRESETS.get(normalized, {})
    return {
        "provider": normalized,
        "label": preset.get("label", normalized.title() or "Repository"),
        "base_url": preset.get("base_url", ""),
    }


def check_repository(
    provider: str,
    base_url: str,
    owner: str,
    repo: str,
    token: str = "",
    user: str = "",
    timeout: float = 20.0,
) -> RepositoryActionResult:
    normalized = normalize_provider(provider)
    url = _build_repo_url(normalized, base_url, owner, repo, action="check")
    headers = _build_headers(normalized, token, user, include_json=False)
    status, body = _request("GET", url, headers=headers, timeout=timeout)
    if status is not None and 200 <= status < 300:
        return RepositoryActionResult(True, _success_message(normalized, "found", owner, repo), url, status)
    if status == 404:
        return RepositoryActionResult(False, _success_message(normalized, "not found", owner, repo), url, status)
    return RepositoryActionResult(False, _response_message(body, _success_message(normalized, "check failed", owner, repo)), url, status)


def create_repository(
    provider: str,
    base_url: str,
    owner: str,
    repo: str,
    token: str = "",
    user: str = "",
    private: bool = True,
    timeout: float = 20.0,
) -> RepositoryActionResult:
    normalized = normalize_provider(provider)
    url, payload = _build_create_request(
        normalized,
        base_url,
        owner,
        repo,
        token=token,
        user=user,
        private=private,
    )
    headers = _build_headers(normalized, token, user, include_json=True)
    status, body = _request("POST", url, headers=headers, data=payload, timeout=timeout)
    if status is not None and 200 <= status < 300:
        return RepositoryActionResult(True, _success_message(normalized, "created", owner, repo), url, status)
    return RepositoryActionResult(False, _response_message(body, _success_message(normalized, "create failed", owner, repo)), url, status)


def delete_repository(
    provider: str,
    base_url: str,
    owner: str,
    repo: str,
    token: str = "",
    user: str = "",
    timeout: float = 20.0,
) -> RepositoryActionResult:
    normalized = normalize_provider(provider)
    url = _build_repo_url(normalized, base_url, owner, repo, action="delete")
    headers = _build_headers(normalized, token, user, include_json=False)
    status, body = _request("DELETE", url, headers=headers, timeout=timeout)
    if status is not None and 200 <= status < 300:
        return RepositoryActionResult(True, _success_message(normalized, "deleted", owner, repo), url, status)
    return RepositoryActionResult(False, _response_message(body, _success_message(normalized, "delete failed", owner, repo)), url, status)


def _clean_base_url(base_url: str, provider: str) -> str:
    cleaned = (base_url or "").strip().rstrip("/")
    if cleaned:
        return cleaned
    defaults = provider_defaults(provider)
    if defaults["base_url"]:
        return defaults["base_url"].rstrip("/")
    raise ValueError(f"Missing API base URL for provider '{provider}'")


def _require_repo_fields(owner: str, repo: str) -> tuple[str, str]:
    clean_owner = (owner or "").strip()
    clean_repo = (repo or "").strip()
    if not clean_repo:
        raise ValueError("Repository name is required")
    return clean_owner, clean_repo


def _build_repo_url(provider: str, base_url: str, owner: str, repo: str, action: str) -> str:
    base = _clean_base_url(base_url, provider)
    owner, repo = _require_repo_fields(owner, repo)
    if provider == "github":
        repo_owner = owner
        if not repo_owner:
            repo_owner = "user"
            if action == "check":
                raise ValueError("GitHub check/delete requires an owner or organization")
        if action == "create":
            if owner:
                return f"{base}/orgs/{parse.quote(owner, safe='')}/repos"
            return f"{base}/user/repos"
        return f"{base}/repos/{parse.quote(repo_owner, safe='')}/{parse.quote(repo, safe='')}"

    if provider == "gitlab":
        encoded_project = parse.quote(f"{owner or ''}/{repo}".strip("/"), safe="")
        if action == "create":
            return f"{base}/projects"
        if not owner:
            raise ValueError("GitLab check/delete requires a namespace or owner")
        return f"{base}/projects/{encoded_project}"

    if provider == "bitbucket":
        workspace = owner
        if not workspace:
            raise ValueError("Bitbucket check/create/delete requires a workspace or owner")
        return f"{base}/repositories/{parse.quote(workspace, safe='')}/{parse.quote(repo, safe='')}"

    if action == "create":
        return f"{base}/repos/{parse.quote(owner or 'user', safe='')}/{parse.quote(repo, safe='')}"
    if not owner:
        raise ValueError(f"{provider.title()} check/delete requires an owner")
    return f"{base}/repos/{parse.quote(owner, safe='')}/{parse.quote(repo, safe='')}"


def _build_create_request(
    provider: str,
    base_url: str,
    owner: str,
    repo: str,
    token: str = "",
    user: str = "",
    private: bool = True,
) -> tuple[str, bytes]:
    base = _clean_base_url(base_url, provider)
    owner, repo = _require_repo_fields(owner, repo)
    if provider == "github":
        normalized_user = (user or "").strip().lower()
        normalized_owner = owner.lower()
        # Use the authenticated-user endpoint unless an explicit different org owner is provided.
        if owner and normalized_owner != normalized_user:
            url = f"{base}/orgs/{parse.quote(owner, safe='')}/repos"
        else:
            url = f"{base}/user/repos"
        payload = {
            "name": repo,
            "private": bool(private),
        }
        return url, json.dumps(payload).encode("utf-8")

    if provider == "gitlab":
        namespace_id = _gitlab_namespace_id(base, owner, token=token, user=user) if owner else None
        if owner and namespace_id is None and owner != (user or "").strip():
            raise ValueError(f"GitLab namespace '{owner}' was not found")
        payload: dict[str, object] = {
            "name": repo,
            "path": repo,
            "visibility": "private" if private else "public",
        }
        if namespace_id is not None:
            payload["namespace_id"] = namespace_id
        return f"{base}/projects", json.dumps(payload).encode("utf-8")

    if provider == "bitbucket":
        payload = {
            "scm": "git",
            "is_private": bool(private),
        }
        return (
            f"{base}/repositories/{parse.quote(owner, safe='')}/{parse.quote(repo, safe='')}",
            json.dumps(payload).encode("utf-8"),
        )

    payload = {
        "name": repo,
        "private": bool(private),
    }
    return f"{base}/repos/{parse.quote(owner or 'user', safe='')}/{parse.quote(repo, safe='')}", json.dumps(payload).encode("utf-8")


def _gitlab_namespace_id(base_url: str, owner: str, token: str, user: str) -> int | None:
    owner = owner.strip()
    if not owner:
        return None
    search_url = f"{_clean_base_url(base_url, 'gitlab')}/namespaces?search={parse.quote(owner, safe='')}"
    headers = _build_headers("gitlab", token, user, include_json=False)
    status, body = _request("GET", search_url, headers=headers, timeout=20.0)
    if status is None or not (200 <= status < 300):
        return None
    if not isinstance(body, list):
        return None
    for item in body:
        if not isinstance(item, dict):
            continue
        full_path = str(item.get("full_path", "")).strip()
        path = str(item.get("path", "")).strip()
        name = str(item.get("name", "")).strip()
        if owner in {full_path, path, name}:
            namespace_id = item.get("id")
            if isinstance(namespace_id, int):
                return namespace_id
            if isinstance(namespace_id, str) and namespace_id.isdigit():
                return int(namespace_id)
    return None


def _build_headers(provider: str, token: str, user: str, include_json: bool) -> dict[str, str]:
    headers = {
        "User-Agent": "time-machine/1.0",
    }
    if include_json:
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
    if provider == "github":
        if token.strip():
            headers["Authorization"] = f"Bearer {token.strip()}"
        headers["Accept"] = "application/vnd.github+json"
    elif provider == "gitlab":
        if token.strip():
            headers["PRIVATE-TOKEN"] = token.strip()
        headers["Accept"] = "application/json"
    elif provider == "bitbucket":
        if token.strip():
            auth_user = (user or "oauth2").strip() or "oauth2"
            auth_value = f"{auth_user}:{token.strip()}".encode("utf-8")
            headers["Authorization"] = f"Basic {base64.b64encode(auth_value).decode('ascii')}"
        headers["Accept"] = "application/json"
    elif token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def _request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: float = 20.0,
) -> tuple[int | None, object]:
    req = request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            payload_text = response.read().decode("utf-8", errors="replace")
            return status, _decode_payload(payload_text)
    except error.HTTPError as exc:
        payload_text = exc.read().decode("utf-8", errors="replace")
        return exc.code, _decode_payload(payload_text)
    except OSError as exc:
        return None, str(exc)


def _decode_payload(payload_text: str) -> object:
    text = payload_text.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _response_message(body: object, fallback: str) -> str:
    if isinstance(body, str) and body.strip():
        return body.strip()
    if isinstance(body, dict):
        for key in ("message", "error", "error_description", "description", "detail"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(body, ensure_ascii=False)
    if isinstance(body, list) and body:
        return json.dumps(body[0], ensure_ascii=False)
    return fallback


def _success_message(provider: str, action: str, owner: str, repo: str) -> str:
    label = provider_defaults(provider)["label"]
    repo_ref = f"{owner}/{repo}" if owner else repo
    return f"{label} {action}: {repo_ref}"