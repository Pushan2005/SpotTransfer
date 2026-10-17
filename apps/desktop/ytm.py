"""YouTube Music playlist creation — the destination platform.

All YouTube Music-specific code lives here: request-header parsing, the
``YTMusic`` client, per-track search, and playlist creation. This is the
destination side of the transfer; sibling modules (spotify.py today,
future platforms like apple.py or tidal.py) hold the source side, and
main.py composes them.

Auth expiry: the pasted request headers expire periodically. When that
happens, ``search_track`` and ``create_playlist`` raise
``AuthExpiredError``. The driver turns that into its "paste fresh
headers" prompt; partial progress is kept and a retry resumes where the
transfer stopped. Generic search failures are deliberately tolerated
(logged + treated as "not found") so one flaky request cannot abort a
whole playlist.

ytmusicapi is imported lazily inside the functions so importing this
module never fails before the desktop venv bootstrap (see
main.ensure_deps).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING

from logging_config import configure_logging, logger

configure_logging()

if TYPE_CHECKING:
    from ytmusicapi import YTMusic

_AUTH_ERROR_MARKERS = ("HTTP 401", "HTTP 403", "UNAUTHENTICATED", "unauthorized")


class AuthExpiredError(RuntimeError):
    """YouTube Music rejected the headers as expired or invalid."""


def is_auth_error(error: Exception) -> bool:
    """Return whether an exception looks like expired YouTube Music auth."""

    message = str(error)
    return any(marker in message for marker in _AUTH_ERROR_MARKERS)


def _is_auth_config(value: object) -> bool:
    """Return whether a JSON object looks like a ytmusicapi auth config."""

    if not isinstance(value, Mapping):
        return False

    keys = {str(key).lower() for key in value}
    return {"authorization", "cookie"}.issubset(keys)


def _header_object_to_raw_headers(value: object) -> str | None:
    """Convert a JSON/JavaScript-style header object to raw header lines."""

    if not isinstance(value, Mapping):
        return None

    # Some browser tools copy a complete request object with headers nested
    # under a ``headers`` property. Only the header mapping is relevant here.
    header_object = value.get("headers", value)
    if not isinstance(header_object, Mapping):
        return None

    lines = []
    for key, header_value in header_object.items():
        if not isinstance(key, str) or not isinstance(header_value, (str, int, float)):
            continue
        lines.append(f"{key}: {header_value}")

    return "\n".join(lines) if lines else None


def parse_headers(raw_headers: str) -> dict[str, object]:
    """Parse pasted headers into the JSON object expected by ``YTMusic``.

    Plain request headers, JSON header objects copied from browser
    developer tools, and pre-normalized ytmusicapi auth objects are all
    accepted. ytmusicapi's setup parser also adds the derived
    browser-auth headers required by YTMusic.
    """

    import ytmusicapi

    try:
        parsed_headers = json.loads(raw_headers)
    except json.JSONDecodeError:
        parsed_headers = None

    if parsed_headers is not None:
        if _is_auth_config(parsed_headers):
            return dict(parsed_headers)

        raw_from_object = _header_object_to_raw_headers(parsed_headers)
        if raw_from_object is None:
            raise ValueError(
                "The pasted headers contain JSON, but not browser request "
                "headers or a YouTube Music auth object"
            )
        raw_headers = raw_from_object

    try:
        normalized_json = ytmusicapi.setup(headers_raw=raw_headers)
        normalized_headers = json.loads(normalized_json)
    except Exception as error:
        raise ValueError(
            "Could not parse the pasted headers as YouTube Music request headers"
        ) from error

    if not _is_auth_config(normalized_headers):
        raise ValueError("The parsed headers do not contain YouTube Music auth data")
    return dict(normalized_headers)


def create_client(auth_config: dict[str, object]) -> "YTMusic":
    """Create the ``YTMusic`` client from parsed auth headers."""

    from ytmusicapi import YTMusic

    return YTMusic(auth_config)


def search_track(client: "YTMusic", track: Mapping[str, object]) -> str | None:
    """Search YouTube Music for one track and return its video ID.

    ``track`` is the normalized source-tracks format documented in
    spotify.py. Returns None when nothing was found. Generic failures are
    logged and treated as "not found"; expired auth raises
    ``AuthExpiredError`` so the driver can stop and prompt for fresh
    headers.
    """

    name = str(track.get("name", ""))
    artists = track.get("artists") or []
    search_string = " ".join([name, *(str(artist) for artist in artists)])

    try:
        results = client.search(search_string, filter="songs")
    except Exception as error:
        if is_auth_error(error):
            raise AuthExpiredError(
                "your YouTube Music headers have expired or are no longer valid"
            ) from error
        logger.exception(
            "YouTube Music search failed for '%s'; treating as not found",
            search_string)
        return None

    return next(
        (
            result.get("videoId")
            for result in results
            if isinstance(result, Mapping)
            and isinstance(result.get("videoId"), str)
            and result["videoId"]
        ),
        None,
    )


def create_playlist(
    client: "YTMusic",
    playlist_name: str,
    video_ids: list[str],
) -> str:
    """Create a private YouTube Music playlist and return its playlist ID.

    Raises ``AuthExpiredError`` on expired headers; every other failure
    propagates to the driver.
    """

    logger.info("Creating YouTube Music playlist '%s' with %d tracks",
                playlist_name, len(video_ids))
    try:
        created_playlist_id = client.create_playlist(
            playlist_name,
            "",
            "PRIVATE",
            video_ids,
        )
    except Exception as error:
        if is_auth_error(error):
            raise AuthExpiredError(
                "your YouTube Music headers have expired or are no longer valid"
            ) from error
        raise
    if not isinstance(created_playlist_id, str) or not created_playlist_id:
        raise RuntimeError("YouTube Music did not return a playlist ID")

    logger.info("Created YouTube Music playlist '%s' -> %s",
                playlist_name, created_playlist_id)
    return created_playlist_id
