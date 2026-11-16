"""Shared HTTP client, API-key resolver, and SHA-256 disk cache for Google Maps."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import parse_qsl, urlparse

import requests

from openubem import config

_SENSITIVE_KEYS = frozenset({"key", "apikey", "api_key", "x-goog-api-key"})


def assert_no_eui_columns(columns: Iterable[Any]) -> None:
    """Enforces OpenUBEM's zero-fitted-parameters rule against EUI leakage.

    Args:
        columns: Iterable of dataframe or geodataframe column names.

    Raises:
        ValueError: If any column name contains ``"eui"`` case-insensitively.
    """
    leaked = [col for col in columns if "eui" in str(col).lower()]
    if leaked:
        raise ValueError(
            f"fusion: zero-fitted-params violation -- EUI column(s) {leaked} "
            "must never be read by a fusion source (plan §2 rule 3)."
        )


class GmapsError(RuntimeError):
    """Base exception raised for Google Maps Platform integration errors."""


class GmapsAuthError(GmapsError):
    """Raised when no valid Google Maps API key is configured or authorized."""


class GmapsOfflineError(GmapsError):
    """Raised when an uncached Google Maps request is attempted in offline mode."""


class GmapsApiError(GmapsError):
    """Raised when a Google Maps Platform HTTP call fails or returns bad data.

    Attributes:
        status_code: HTTP status code if available, otherwise ``None``.
        url: Sanitized request URL without credential query parameters.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
    ) -> None:
        """Initializes a Google Maps API error instance.

        Args:
            message: Human-readable error summary without credentials.
            status_code: Optional HTTP response status code.
            url: Optional sanitized target URL.
        """
        super().__init__(message)
        self.status_code = status_code
        self.url = url


def _read_key_from_dotenv(
    dotenv_path: Path,
    env_var: str = "GOOGLE_MAPS_API_KEY",
) -> str | None:
    """Safely parses a single environment variable from a ``.env`` file.

    Args:
        dotenv_path: Path to the ``.env`` file to inspect.
        env_var: Environment variable name to extract.

    Returns:
        Stripped credential string if found and non-empty, otherwise ``None``.
    """
    if not dotenv_path.is_file():
        return None
    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        name, val = line.split("=", 1)
        if name.strip() != env_var:
            continue
        cleaned = val.strip()
        if (
            len(cleaned) >= 2
            and cleaned[0] == cleaned[-1]
            and cleaned[0] in {"'", '"'}
        ):
            cleaned = cleaned[1:-1].strip()
        return cleaned or None
    return None


def resolve_gmaps_api_key(
    api_key: str | None = None,
    env_var: str = "GOOGLE_MAPS_API_KEY",
    dotenv_paths: Sequence[Path] | None = None,
) -> str:
    """Resolves a Google Maps API key from explicit input, env vars, or ``.env``.

    Args:
        api_key: Optional caller-provided key taking top precedence.
        env_var: Environment variable name holding the key.
        dotenv_paths: Optional override sequence of ``.env`` files to scan.

    Returns:
        Non-empty Google Maps API key string.

    Raises:
        GmapsAuthError: If no non-empty API key is available anywhere.
    """
    if api_key and api_key.strip():
        return api_key.strip()
    env_val = os.environ.get(env_var, "").strip()
    if env_val:
        return env_val

    candidates = (
        list(dotenv_paths)
        if dotenv_paths is not None
        else [
            Path.cwd() / ".env",
            Path(__file__).resolve().parents[2] / ".env",
            Path.home() / ".env",
        ]
    )
    for path in candidates:
        found = _read_key_from_dotenv(path, env_var=env_var)
        if found:
            return found

    raise GmapsAuthError(
        f"Missing {env_var}. Export {env_var} or store it safely in "
        '~/.env via: printf "Enter '
        f'{env_var} (typing hidden): " && read -s val && echo && '
        f'echo "{env_var}=$val" >> "$HOME/.env"'
    )


def _strip_sensitive_dict(data: dict[str, Any] | None) -> dict[str, Any]:
    """Returns a copy of a mapping with credential-like keys removed.

    Args:
        data: Input dictionary of query parameters or headers.

    Returns:
        Sorted dictionary excluding API key fields.
    """
    if not data:
        return {}
    return {
        str(k): v
        for k, v in sorted(data.items(), key=lambda item: str(item[0]))
        if str(k).lower() not in _SENSITIVE_KEYS
    }


def _sanitize_url(url: str) -> str:
    """Strips sensitive query parameters from a URL before caching or logging.

    Args:
        url: Raw request URL that might include an API key parameter.

    Returns:
        Sanitized URL string safe for logs and SHA-256 cache keys.
    """
    parsed = urlparse(url)
    safe_query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in _SENSITIVE_KEYS
    ]
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if not safe_query:
        return base
    query_str = "&".join(f"{k}={v}" for k, v in sorted(safe_query))
    return f"{base}?{query_str}"


def build_cache_key(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Computes a deterministic SHA-256 cache digest excluding API credentials.

    Args:
        method: HTTP verb (e.g., ``"GET"`` or ``"POST"``).
        url: Request URL.
        params: Optional query parameter dictionary.
        json_body: Optional JSON request body.
        headers: Optional request headers (API key headers stripped).

    Returns:
        64-character lowercase hexadecimal SHA-256 digest.
    """
    payload = {
        "method": method.upper(),
        "url": _sanitize_url(url),
        "params": _strip_sensitive_dict(params),
        "json_body": json_body or {},
        "headers": _strip_sensitive_dict(headers),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class GmapsHttpClient:
    """Deterministic disk-cached HTTP client for Google Maps Platform APIs."""

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path | None = None,
        timeout_s: float | None = None,
        offline: bool | None = None,
        session: requests.Session | None = None,
        env_var: str = "GOOGLE_MAPS_API_KEY",
    ) -> None:
        """Initializes the cached Google Maps HTTP client.

        Args:
            api_key: Optional explicit Google Maps API key.
            cache_dir: Directory for cached JSON and binary artifacts.
            timeout_s: Request timeout in seconds.
            offline: If ``True``, forbid network calls on cache misses.
            session: Optional ``requests.Session`` for HTTP transport/mocking.
            env_var: Environment variable name checked for fallback API keys.
        """
        self._explicit_api_key = api_key
        self.cache_dir = Path(cache_dir or config.GMAPS_CACHE_DIR)
        self.timeout_s = float(
            timeout_s if timeout_s is not None else config.GMAPS_TIMEOUT_S
        )
        self.offline = bool(config.OFFLINE if offline is None else offline)
        self._session = session or requests.Session()
        self._env_var = env_var

    def _get_key(self) -> str:
        """Resolves the API key lazily only when a network request is needed.

        Returns:
            Non-empty Google Maps API key string.
        """
        return resolve_gmaps_api_key(
            api_key=self._explicit_api_key,
            env_var=self._env_var,
        )

    def _prepare_request(
        self,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
        auth_mode: str,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Attaches API key credentials cleanly without mutating caller dicts.

        Args:
            params: Query parameter dictionary.
            headers: Request header dictionary.
            auth_mode: Credential placement: ``"query"``, ``"header"``, or ``"none"``.

        Returns:
            Tuple of ``(request_params, request_headers)``.

        Raises:
            ValueError: If ``auth_mode`` is unrecognized.
        """
        req_params = dict(params or {})
        req_headers = dict(headers or {})
        if auth_mode == "none":
            return req_params, req_headers
        key = self._get_key()
        if auth_mode == "query":
            req_params["key"] = key
            return req_params, req_headers
        if auth_mode == "header":
            req_headers["X-Goog-Api-Key"] = key
            return req_params, req_headers
        raise ValueError(f"Unsupported auth_mode: {auth_mode!r}")

    def _send_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth_mode: str = "query",
    ) -> requests.Response:
        """Executes an HTTP call and translates transport/status failures.

        Args:
            method: HTTP verb (``"GET"`` or ``"POST"``).
            url: Target endpoint URL.
            params: Optional query parameters.
            json_body: Optional JSON body for ``POST`` calls.
            headers: Optional HTTP headers.
            auth_mode: Authentication placement mode.

        Returns:
            Successful ``requests.Response`` object with ``status_code < 400``.

        Raises:
            GmapsAuthError: On HTTP 401/403 or missing credentials.
            GmapsApiError: On network exceptions or other HTTP errors.
        """
        clean_url = _sanitize_url(url)
        req_params, req_headers = self._prepare_request(
            params=params,
            headers=headers,
            auth_mode=auth_mode,
        )
        try:
            resp = self._session.request(
                method=method.upper(),
                url=url,
                params=req_params,
                json=json_body,
                headers=req_headers,
                timeout=self.timeout_s,
            )
        except requests.RequestException as exc:
            raise GmapsApiError(
                f"HTTP request failed for {clean_url}: {type(exc).__name__}",
                url=clean_url,
            ) from exc

        if resp.status_code in {401, 403}:
            raise GmapsAuthError(
                f"Google Maps API rejected credentials ({resp.status_code}) "
                f"for {clean_url}."
            )
        if resp.status_code >= 400:
            snippet = (resp.text or "")[:200].replace("\n", " ").strip()
            raise GmapsApiError(
                f"Google Maps API error {resp.status_code} for {clean_url}: "
                f"{snippet}",
                status_code=int(resp.status_code),
                url=clean_url,
            )
        return resp

    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth_mode: str = "query",
    ) -> dict[str, Any]:
        """Fetches JSON via HTTP GET, backed by deterministic disk caching.

        Args:
            url: Endpoint URL.
            params: Optional query parameter mapping.
            headers: Optional HTTP headers.
            auth_mode: Credential placement (``"query"``, ``"header"``, or ``"none"``).

        Returns:
            Parsed JSON response dictionary.

        Raises:
            GmapsOfflineError: On cache miss while ``self.offline`` is ``True``.
            GmapsApiError: On HTTP failure or malformed JSON payload.
        """
        return self._cached_json(
            method="GET",
            url=url,
            params=params,
            json_body=None,
            headers=headers,
            auth_mode=auth_mode,
        )

    def post_json(
        self,
        url: str,
        *,
        json_body: dict[str, Any],
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth_mode: str = "header",
    ) -> dict[str, Any]:
        """Fetches JSON via HTTP POST, backed by deterministic disk caching.

        Args:
            url: Endpoint URL.
            json_body: JSON request payload.
            params: Optional query parameter mapping.
            headers: Optional HTTP headers (e.g., ``X-Goog-FieldMask``).
            auth_mode: Credential placement (``"header"``, ``"query"``, or ``"none"``).

        Returns:
            Parsed JSON response dictionary.

        Raises:
            GmapsOfflineError: On cache miss while ``self.offline`` is ``True``.
            GmapsApiError: On HTTP failure or malformed JSON payload.
        """
        return self._cached_json(
            method="POST",
            url=url,
            params=params,
            json_body=json_body,
            headers=headers,
            auth_mode=auth_mode,
        )

    def _cached_json(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        json_body: dict[str, Any] | None,
        headers: dict[str, str] | None,
        auth_mode: str,
    ) -> dict[str, Any]:
        """Shared read-through JSON disk cache implementation for GET/POST calls.

        Args:
            method: HTTP verb.
            url: Target endpoint URL.
            params: Optional query parameters.
            json_body: Optional JSON body.
            headers: Optional HTTP headers.
            auth_mode: Authentication placement mode.

        Returns:
            Parsed JSON dictionary.
        """
        digest = build_cache_key(
            method=method,
            url=url,
            params=params,
            json_body=json_body,
            headers=headers,
        )
        cache_path = self.cache_dir / f"{digest}.json"
        if cache_path.is_file():
            return json.loads(cache_path.read_text(encoding="utf-8"))
        if self.offline:
            raise GmapsOfflineError(
                f"Offline mode forbids uncached Google Maps request to "
                f"{_sanitize_url(url)}"
            )
        resp = self._send_request(
            method=method,
            url=url,
            params=params,
            json_body=json_body,
            headers=headers,
            auth_mode=auth_mode,
        )
        try:
            payload = resp.json()
        except ValueError as exc:
            raise GmapsApiError(
                f"Invalid JSON returned from {_sanitize_url(url)}",
                status_code=int(resp.status_code),
                url=_sanitize_url(url),
            ) from exc

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def download_binary(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        dest_path: Path | None = None,
        suffix: str = ".bin",
        headers: dict[str, str] | None = None,
        auth_mode: str = "query",
    ) -> Path:
        """Downloads a binary resource (e.g., GeoTIFF) with disk caching.

        Args:
            url: Source download URL.
            params: Optional query parameters.
            dest_path: Optional explicit destination path on disk.
            suffix: Extension used for the cache file when ``dest_path`` is ``None``.
            headers: Optional HTTP headers.
            auth_mode: Credential placement mode.

        Returns:
            Path to the cached or written binary file.

        Raises:
            GmapsOfflineError: On cache miss while ``self.offline`` is ``True``.
            GmapsApiError: On HTTP transport or status error.
        """
        if dest_path is not None and dest_path.is_file():
            return dest_path

        digest = build_cache_key(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        norm_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        cache_path = self.cache_dir / f"{digest}{norm_suffix}"
        if cache_path.is_file():
            if dest_path is not None and dest_path != cache_path:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_bytes(cache_path.read_bytes())
                return dest_path
            return cache_path

        if self.offline:
            raise GmapsOfflineError(
                f"Offline mode forbids uncached binary download from "
                f"{_sanitize_url(url)}"
            )
        resp = self._send_request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            auth_mode=auth_mode,
        )
        content = resp.content
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(content)
        if dest_path is not None and dest_path != cache_path:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(content)
            return dest_path
        return cache_path
