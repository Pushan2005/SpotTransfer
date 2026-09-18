"""Transfer a Spotify playlist to YouTube Music from a local machine.

Before running this file:

1. Copy the request headers from an authenticated ``music.youtube.com``
   ``/browse`` request into ``youtubemusic.json``. Take the copy in a
   private/incognito window and close that window afterwards without
   signing out; see ``_AUTH_PASTE_HELP`` below for why that matters.
2. Choose which playlists to transfer, either by
   (a) running ``list_playlists.py`` and deleting unwanted rows from the
       generated ``playlists.csv``, or
   (b) setting ``spotify_playlist_link`` in ``setup.py`` to one playlist
       URL, or to a list of them.
   ``playlists.csv`` wins when it exists and lists at least one playlist.
3. Run this file with the Python interpreter from ``backend/venv``.

The first run converts the pasted headers in ``youtubemusic.json`` into the
ytmusicapi authentication format. Future runs can reuse that generated JSON
until the browser session expires.

Credentials are checked against YouTube Music at startup, so a stale paste
is reported before any work begins rather than part-way through a queue.

If the YouTube Music headers expire mid-transfer, the script stops and asks
for a fresh set of headers. Paste
them into ``youtubemusic.json``, SAVE the file, and run the script again; the
partial progress stored in ``transfer_progress.json`` is detected on
startup and the transfer resumes where it stopped. Setting a different
playlist link in ``setup.py`` discards the saved progress and starts a
new transfer instead.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import shlex
import shutil
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

import ytmusicapi
from spotapi import PublicPlaylist
from ytmusicapi import YTMusic
from setup import spotify_playlist_link


BASE_DIR = Path(__file__).resolve().parent
YTMUSIC_AUTH_PATH = BASE_DIR / "youtubemusic.json"
# The credentials file used to be called browser.json. It is still read when
# it is the only one present, so an existing checkout keeps working.
LEGACY_AUTH_PATH = BASE_DIR / "browser.json"
PROGRESS_PATH = BASE_DIR / "transfer_progress.json"
PLAYLISTS_PATH = BASE_DIR / "playlists.csv"
_SPOTIFY_PLAYLIST_URL = "https://open.spotify.com/playlist/{}"
_PROGRESS_VERSION = 2
_PLAYLIST_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{22}$")
_PLACEHOLDER_SPOTIFY_LINK = "https://open.spotify.com/playlist/2nncn5UUUVQdQaRb6lKwB0 "
_PROGRESS_BAR_WIDTH = 24
_AUTH_ERROR_MARKERS = ("HTTP 401", "HTTP 403", "UNAUTHENTICATED", "unauthorized")
# Cookies Google re-issues every few minutes. They authenticate nothing on
# their own, but a stale copy is treated as a reason to reject the whole
# session, which is the usual cause of credentials dying within hours.
_VOLATILE_COOKIES = frozenset(
    {
        "__Secure-1PSIDTS",
        "__Secure-3PSIDTS",
        "SIDCC",
        "__Secure-1PSIDCC",
        "__Secure-3PSIDCC",
    }
)
_AUTH_PASTE_HELP = (
    "  1. Open a PRIVATE / INCOGNITO browser window.\n"
    "  2. Sign in at music.youtube.com in that window.\n"
    "  3. Press F12 and open Network, type 'browse' in the filter box, reload\n"
    "     the page, then right-click a POST /browse request whose status is\n"
    "     200 and choose Copy -> Copy as cURL.\n"
    "  4. Delete the contents of youtubemusic.json, paste, and SAVE (Ctrl+S).\n"
    "  5. CLOSE the incognito window. Do NOT click 'Sign out'.\n"
    "\n"
    "Step 5 is the one that matters. Google advances the session for as long\n"
    "as a browser keeps using it, and that invalidates the copy you pasted.\n"
    "Closing the window leaves the session untouched so the copy keeps\n"
    "working; signing out ends it immediately and the copy dies with it."
)


class AuthExpiredError(RuntimeError):
    """YouTube Music rejected the stored headers as expired or invalid."""

    def __init__(
        self,
        message: str,
        tracks_done: int,
        tracks_total: int,
        playlist_name: str = "",
    ):
        super().__init__(message)
        self.tracks_done = tracks_done
        self.tracks_total = tracks_total
        self.playlist_name = playlist_name


def _is_auth_error(error: Exception) -> bool:
    """Return whether an exception looks like expired YouTube Music auth."""

    message = str(error)
    return any(marker in message for marker in _AUTH_ERROR_MARKERS)


def _read_raw_progress() -> dict[str, object] | None:
    """Read the progress file as-is, without validating its shape."""

    if not PROGRESS_PATH.is_file():
        return None

    try:
        progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        print(f"Could not read {PROGRESS_PATH.name}; starting a new transfer")
        return None

    return progress if isinstance(progress, dict) else None


def _migrate_v1_progress(
    progress: Mapping[str, object],
    queue_ids: list[str],
) -> dict[str, object] | None:
    """Upgrade a single-playlist v1 progress file to the v2 queue format.

    Resuming an interrupted transfer is a documented feature, so a run that
    was saved before multi-playlist support is carried over instead of being
    silently discarded.
    """

    playlist_id = progress.get("playlist_id")
    if not isinstance(playlist_id, str) or not isinstance(progress.get("tracks"), list):
        return None

    # v1 only ever described one playlist, which must be the one still pending.
    if not queue_ids or queue_ids[0] != playlist_id:
        return None

    print(f"Upgrading {PROGRESS_PATH.name} from the single-playlist format")
    return {
        "version": _PROGRESS_VERSION,
        "queue": queue_ids,
        "done": [],
        "current": {key: value for key, value in progress.items() if key != "version"},
    }


def _load_progress(queue_ids: list[str]) -> dict[str, object] | None:
    """Load saved progress for this queue, or None when nothing can resume."""

    progress = _read_raw_progress()
    if progress is None:
        return None

    if progress.get("version") == 1:
        progress = _migrate_v1_progress(progress, queue_ids)
        if progress is None:
            print(f"Ignoring unrecognized {PROGRESS_PATH.name}; starting a new transfer")
            return None

    if (
        progress.get("version") != _PROGRESS_VERSION
        or not isinstance(progress.get("queue"), list)
        or not isinstance(progress.get("done"), list)
    ):
        print(f"Ignoring unrecognized {PROGRESS_PATH.name}; starting a new transfer")
        return None

    # Changing the configured playlists discards progress for the old set.
    if progress["queue"] != queue_ids:
        print(
            f"Found incomplete progress for a different set of playlists "
            f"({len(progress['queue'])} configured then, {len(queue_ids)} now); "
            "starting a new transfer"
        )
        return None

    return progress


def _save_progress(progress: dict[str, object]) -> None:
    """Persist transfer progress atomically so an interrupted write is safe."""

    tmp_path = PROGRESS_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(progress, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp_path, PROGRESS_PATH)


def _clear_progress() -> None:
    """Remove the progress file once a transfer is complete or discarded."""

    try:
        PROGRESS_PATH.unlink()
    except FileNotFoundError:
        pass


def extract_spotify_playlist_id(playlist_link: str) -> str:
    """Validate a Spotify playlist URL and return its playlist ID."""

    if not isinstance(playlist_link, str):
        raise ValueError("spotify_playlist_link must be a Spotify playlist URL")

    value = playlist_link.strip()
    parsed = urlparse(value)
    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("spotify_playlist_link is not a valid URL") from error

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or hostname not in {"open.spotify.com", "www.open.spotify.com"}
        or port is not None
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            "spotify_playlist_link must use an open.spotify.com playlist URL"
        )

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) != 2 or path_parts[0].lower() != "playlist":
        raise ValueError(
            "spotify_playlist_link must have the form "
            "https://open.spotify.com/playlist/<playlist-id>"
        )

    playlist_id = path_parts[1]
    if not _PLAYLIST_ID_PATTERN.fullmatch(playlist_id):
        raise ValueError("spotify_playlist_link contains an invalid Spotify playlist ID")

    return playlist_id


def _normalize_playlist_links(value: object) -> list[str]:
    """Return the configured playlist link(s) as a list of non-empty strings."""

    if isinstance(value, str):
        links: list[object] = [value]
    elif isinstance(value, (list, tuple)):
        links = list(value)
    else:
        raise ValueError(
            "spotify_playlist_link must be a Spotify playlist URL, "
            "or a list of Spotify playlist URLs"
        )

    placeholder = _PLACEHOLDER_SPOTIFY_LINK.strip()
    cleaned: list[str] = []
    for link in links:
        if not isinstance(link, str):
            raise ValueError(
                "Every entry in spotify_playlist_link must be a playlist URL string"
            )
        link = link.strip()
        # Blank entries and the placeholder are treated as "not filled in yet",
        # so a half-edited list still reports the same error as an empty one.
        if link and link != placeholder:
            cleaned.append(link)

    if not cleaned:
        raise ValueError("Edit spotify_playlist_link before running the script")

    return cleaned


def _playlist_id_column(header: list[str]) -> int | None:
    """Locate the playlist ID column, so re-ordered columns still work."""

    for index, cell in enumerate(header):
        if cell.strip().lower().replace(" ", "_") in {"playlist_id", "id", "playlistid"}:
            return index
    return None


def _read_playlists_file() -> list[str]:
    """Return the playlist links left in playlists.csv, if it exists.

    The file is written by ``list_playlists.py`` and then edited by hand or in
    a spreadsheet, so it tolerates a missing or re-ordered header row, blank
    rows, stray whitespace and rows commented out with a leading ``#``.
    """

    if not PLAYLISTS_PATH.is_file():
        return []

    text = PLAYLISTS_PATH.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(text, newline="")))

    id_column = 1
    start = 0
    for number, row in enumerate(rows):
        cells = [cell.strip() for cell in row]
        if not any(cells) or cells[0].startswith("#"):
            continue
        # The first meaningful row is a header unless it already holds an ID.
        located = _playlist_id_column(cells)
        if located is not None:
            id_column = located
            start = number + 1
        elif len(cells) > 1 and _PLAYLIST_ID_PATTERN.fullmatch(cells[1]):
            start = number
        else:
            start = number
        break

    links: list[str] = []
    for number, row in enumerate(rows[start:], start=start + 1):
        cells = [cell.strip() for cell in row]
        if not any(cells) or cells[0].startswith("#"):
            continue

        if len(cells) <= id_column:
            raise ValueError(
                f"{PLAYLISTS_PATH.name} row {number} has no playlist ID column. "
                f"Each row must be: {','.join(('name', 'playlist_id'))}"
            )

        playlist_id = cells[id_column]
        # A whole URL in the ID column is accepted; people paste those.
        if "/" in playlist_id:
            links.append(playlist_id)
            continue

        if not _PLAYLIST_ID_PATTERN.fullmatch(playlist_id):
            name = cells[0] if id_column != 0 else ""
            where = f" ('{name}')" if name else ""
            raise ValueError(
                f"{PLAYLISTS_PATH.name} row {number}{where} has an invalid "
                f"Spotify playlist ID: {playlist_id!r}"
            )

        links.append(_SPOTIFY_PLAYLIST_URL.format(playlist_id))

    return links


def _validate_setup() -> list[tuple[str, str]]:
    """Validate the chosen playlist link(s) and return (link, ID) pairs.

    ``playlists.txt`` takes precedence over ``setup.py`` so that reviewing a
    generated list is all it takes to pick playlists, with no code editing.
    """

    links = _read_playlists_file()
    source = PLAYLISTS_PATH.name

    if links:
        print(f"Using {source}: {len(links)} playlist(s) listed")
    elif PLAYLISTS_PATH.is_file():
        raise ValueError(
            f"{source} lists no playlists. Every row was deleted. Run "
            "'python3 list_playlists.py' to regenerate it, add rows to it by "
            f"hand, or delete {source} to go back to using setup.py."
        )
    else:
        links = _normalize_playlist_links(spotify_playlist_link)
        source = "spotify_playlist_link"

    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for link in links:
        try:
            playlist_id = extract_spotify_playlist_id(link)
        except ValueError as error:
            if len(links) == 1 and source == "spotify_playlist_link":
                raise
            # The underlying message names the setup.py variable, which is
            # the wrong thing to point at when the links came from a file.
            message = str(error).replace("spotify_playlist_link", f"each entry in {source}")
            raise ValueError(f"{message} (check this entry: {link})") from error

        # The same playlist listed twice would otherwise transfer twice.
        if playlist_id in seen:
            print(f"Ignoring duplicate playlist link: {link}")
            continue

        seen.add(playlist_id)
        pairs.append((link, playlist_id))

    return pairs


def _write_progress(
    prefix: str,
    current: int,
    total: int,
    detail: str,
    previous_status_length: int,
    terminal_width: int,
) -> int:
    """Rewrite one width-safe progress line and return its rendered length."""

    safe_total = max(1, total)
    completed_width = min(
        _PROGRESS_BAR_WIDTH,
        int(_PROGRESS_BAR_WIDTH * current / safe_total),
    )
    progress_bar = "=" * completed_width
    progress_bar += "-" * (_PROGRESS_BAR_WIDTH - completed_width)

    status_prefix = f"{prefix} [{progress_bar}] {current}/{total}: "
    available_detail_width = max(1, terminal_width - len(status_prefix) - 1)
    if len(detail) > available_detail_width:
        detail = detail[: max(1, available_detail_width - 3)] + "..."

    status = status_prefix + detail
    padding = max(0, previous_status_length - len(status))
    sys.stdout.write(f"\r\033[2K{status}{' ' * padding}")
    sys.stdout.flush()
    return max(previous_status_length, len(status))


def get_spotify_playlist_name(playlist_link: str) -> str:
    """Fetch the playlist name from a Spotify playlist link with SpotAPI."""

    playlist_id = extract_spotify_playlist_id(playlist_link)
    terminal_width = shutil.get_terminal_size(fallback=(120, 24)).columns
    previous_status_length = _write_progress(
        "Fetching Spotify",
        0,
        1,
        "playlist metadata",
        0,
        terminal_width,
    )

    try:
        playlist = PublicPlaylist(playlist_id)
        response = playlist.get_playlist_info(limit=1)
        previous_status_length = _write_progress(
            "Fetching Spotify",
            1,
            1,
            "playlist metadata",
            previous_status_length,
            terminal_width,
        )
    finally:
        sys.stdout.write("\n")
        sys.stdout.flush()

    response_data = response.get("data")
    playlist_data = (
        response_data.get("playlistV2", {})
        if isinstance(response_data, Mapping)
        else {}
    )
    if not isinstance(playlist_data, Mapping):
        raise RuntimeError("SpotAPI returned an unexpected playlist response")

    name = playlist_data.get("name")
    if not isinstance(name, str):
        attributes = playlist_data.get("attributes")
        name = attributes.get("name") if isinstance(attributes, Mapping) else None

    if not isinstance(name, str) or not name.strip():
        raise RuntimeError("SpotAPI did not return a playlist name")

    return name.strip()


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


# curl flags that consume a following value which is not a request header.
_CURL_SKIP_VALUE_FLAGS = {
    "--url", "-d", "--data", "--data-raw", "--data-binary", "--data-urlencode",
    "-X", "--request", "-x", "--proxy", "-o", "--output", "--max-time", "-m",
}
_CURL_HEADER_FLAGS = {"-H", "--header"}
_CURL_COOKIE_FLAGS = {"-b", "--cookie"}
# A few curl flags carry a value that is really a header.
_CURL_VALUE_AS_HEADER = {"-A": "user-agent", "--user-agent": "user-agent",
                         "-e": "referer", "--referer": "referer"}


def _curl_to_raw_headers(raw_text: str) -> str | None:
    """Convert a copied ``curl`` command into raw header lines.

    Browsers offer "Copy as cURL" as the one export that is never sanitized,
    so it is the most reliable way to capture an authenticated request.
    Cookies arrive in ``-b``/``--cookie`` rather than as a ``cookie`` header,
    and the command is usually wrapped over many lines with trailing
    backslashes, so neither ytmusicapi nor the JSON paths can read it as-is.
    """

    if not isinstance(raw_text, str) or not raw_text.lstrip().startswith("curl"):
        return None

    # Unwrap shell (``\``) and cmd (``^``) line continuations before lexing.
    command = re.sub(r"[\\^]\r?\n", " ", raw_text.strip())

    try:
        tokens = shlex.split(command)
    except ValueError as error:
        raise ValueError(
            "youtubemusic.json looks like a curl command but could not be read; "
            "copy it again with 'Copy as cURL' and paste it unmodified"
        ) from error

    headers: dict[str, str] = {}
    cookie_from_flag: str | None = None

    index = 1  # token 0 is "curl" itself
    while index < len(tokens):
        token = tokens[index]

        # Support both "--header value" and "--header=value".
        flag, _, inline_value = token.partition("=")
        has_inline = bool(_) and flag.startswith("--")

        def take_value() -> str | None:
            nonlocal index
            if has_inline:
                return inline_value
            index += 1
            return tokens[index] if index < len(tokens) else None

        if flag in _CURL_HEADER_FLAGS:
            value = take_value()
            if value and ":" in value:
                name, _, header_value = value.partition(":")
                name = name.strip().lower()
                # HTTP/2 pseudo-headers are transport details, not headers.
                if name and not name.startswith(":"):
                    headers[name] = header_value.strip()
        elif flag in _CURL_COOKIE_FLAGS:
            value = take_value()
            # curl treats a value without "=" as a cookie *file*, not cookies.
            if value and "=" in value:
                cookie_from_flag = value.strip()
        elif flag in _CURL_VALUE_AS_HEADER:
            value = take_value()
            if value:
                headers.setdefault(_CURL_VALUE_AS_HEADER[flag], value.strip())
        elif flag in _CURL_SKIP_VALUE_FLAGS:
            take_value()

        index += 1

    # An explicit "cookie" header wins over -b, which curl would also do.
    if cookie_from_flag and "cookie" not in headers:
        headers["cookie"] = cookie_from_flag

    if not headers:
        raise ValueError(
            "youtubemusic.json looks like a curl command but contains no request "
            "headers; make sure you copied the whole command"
        )

    return "\n".join(f"{name}: {value}" for name, value in headers.items())


def _har_entry_headers(entry: object) -> dict[str, str] | None:
    """Return one HAR entry's request headers, or None when it has none."""

    if not isinstance(entry, Mapping):
        return None

    request = entry.get("request")
    if not isinstance(request, Mapping):
        return None

    headers: dict[str, str] = {}
    entry_headers = request.get("headers")
    if isinstance(entry_headers, list):
        for header in entry_headers:
            if not isinstance(header, Mapping):
                continue
            name = header.get("name")
            value = header.get("value")
            # HTTP/2 pseudo-headers (":authority", ":method", ...) describe the
            # transport rather than the request, and ytmusicapi discards them.
            if not isinstance(name, str) or name.startswith(":"):
                continue
            if isinstance(value, (str, int, float)):
                headers[name.lower()] = str(value)

    # Some exporters record cookies only in the separate ``cookies`` array.
    if "cookie" not in headers:
        cookies = request.get("cookies")
        if isinstance(cookies, list):
            pairs = [
                f"{cookie['name']}={cookie['value']}"
                for cookie in cookies
                if isinstance(cookie, Mapping)
                and isinstance(cookie.get("name"), str)
                and isinstance(cookie.get("value"), str)
            ]
            if pairs:
                headers["cookie"] = "; ".join(pairs)

    return headers or None


def _har_to_raw_headers(value: object) -> str | None:
    """Convert a browser HAR export into raw header lines.

    A HAR holds every recorded request, so the best authenticated YouTube
    Music call is selected rather than whichever happens to be first.
    Chrome sanitizes HAR exports by default and strips exactly the cookie
    and authorization headers needed here, so a credential-free HAR gets a
    dedicated message instead of a generic "not request headers" failure.
    """

    if not isinstance(value, Mapping):
        return None

    log = value.get("log")
    if not isinstance(log, Mapping):
        return None

    entries = log.get("entries")
    if not isinstance(entries, list):
        return None

    if not entries:
        raise ValueError(
            "youtubemusic.json is a HAR export with no recorded requests; record a "
            "/browse request on music.youtube.com and export it again"
        )

    best_headers: dict[str, str] | None = None
    best_rank = -1
    saw_request = False

    for entry in entries:
        headers = _har_entry_headers(entry)
        if headers is None:
            continue
        saw_request = True
        if "cookie" not in headers:
            continue

        url = entry["request"].get("url")
        url = url.lower() if isinstance(url, str) else ""

        # Prefer an authenticated YouTube Music API call, ideally the /browse
        # request the README asks for.
        rank = 0
        if "/youtubei/v1/" in url:
            rank = 2 if "/youtubei/v1/browse" in url else 1
        if "x-goog-authuser" in headers:
            rank += 3

        if rank > best_rank:
            best_rank = rank
            best_headers = headers

    if best_headers is None:
        if not saw_request:
            return None
        raise ValueError(
            "youtubemusic.json is a HAR export whose requests carry no cookie "
            "header. Chrome sanitizes HAR exports by default, stripping the "
            "cookie and authorization headers this tool needs.\n"
            "Either re-export the request with 'Copy as HAR (with sensitive "
            "data)', or paste the raw request headers instead: open the "
            "/browse POST, go to Headers > Request Headers, switch the view "
            "to 'Raw', and copy the whole block into youtubemusic.json."
        )

    return "\n".join(f"{name}: {header}" for name, header in best_headers.items())


def parse_browser_headers(raw_headers: str) -> dict[str, object]:
    """Parse pasted headers into the JSON object expected by ``YTMusic``.

    Plain request headers are intentionally allowed in ``youtubemusic.json``; the
    file does not need to be valid JSON when the user pastes them. ytmusicapi's
    setup parser also adds the derived browser-auth headers required by YTMusic.
    """

    # A copied curl command is never valid JSON, so it is resolved to raw
    # header lines before the JSON paths are attempted.
    curl_headers = _curl_to_raw_headers(raw_headers)
    if curl_headers is not None:
        raw_headers = curl_headers
        parsed_headers = None
    else:
        try:
            parsed_headers = json.loads(raw_headers)
        except json.JSONDecodeError:
            parsed_headers = None

    if parsed_headers is not None:
        if _is_auth_config(parsed_headers):
            return dict(parsed_headers)

        # A HAR export is checked first: it is also a JSON object, but its
        # headers live several levels down inside log.entries[].request.
        raw_from_object = _har_to_raw_headers(parsed_headers)
        if raw_from_object is None:
            raw_from_object = _header_object_to_raw_headers(parsed_headers)
        if raw_from_object is None:
            raise ValueError(
                "youtubemusic.json contains JSON, but not browser request headers "
                "or a ytmusicapi auth object"
            )
        raw_headers = raw_from_object

    try:
        normalized_json = ytmusicapi.setup(headers_raw=raw_headers)
        normalized_headers = json.loads(normalized_json)
    except Exception as error:
        raise ValueError(
            "Could not parse youtubemusic.json as YouTube Music request headers"
        ) from error

    if not _is_auth_config(normalized_headers):
        # ytmusicapi only insists on cookie and x-goog-authuser, so headers
        # copied without the authorization line get this far and then fail.
        # Naming the missing header saves another round of guesswork.
        present = {str(key).lower() for key in normalized_headers}
        missing = sorted({"authorization", "cookie"} - present)
        raise ValueError(
            "Parsed youtubemusic.json is missing the "
            + " and ".join(missing)
            + f" header{'s' if len(missing) > 1 else ''}. Copy the complete "
            "Request Headers block from an authenticated /browse request, "
            "including the authorization and cookie lines."
        )
    return dict(normalized_headers)


def _without_volatile_cookies(auth_config: Mapping[str, object]) -> dict[str, object]:
    """Return the auth config with Google's short-lived cookies removed."""

    cookie = auth_config.get("cookie")
    if not isinstance(cookie, str):
        return dict(auth_config)

    kept = [
        part
        for part in (piece.strip() for piece in cookie.split(";"))
        if part and part.split("=", 1)[0] not in _VOLATILE_COOKIES
    ]
    if not kept:
        return dict(auth_config)

    trimmed = dict(auth_config)
    trimmed["cookie"] = "; ".join(kept)
    return trimmed


def _signed_in_account(ytmusic: YTMusic) -> str | None:
    """Return the signed-in account name, or None when not authenticated.

    YouTube answers an unauthenticated request with HTTP 200 and a logged-out
    payload rather than a 401, so the only reliable check is asking for
    something only a signed-in account has. ytmusicapi fails while parsing
    that payload, which is why every exception counts as "not signed in".
    """

    try:
        info = ytmusic.get_account_info()
    except Exception:
        return None

    name = info.get("accountName") if isinstance(info, Mapping) else None
    return name.strip() if isinstance(name, str) and name.strip() else None


def load_ytmusic(auth_path: Path = YTMUSIC_AUTH_PATH, *, verify: bool = True) -> YTMusic:
    """Load YTMusic auth from pasted headers or an existing auth JSON file.

    ytmusicapi.setup() writes the normalized credentials back to ``auth_path``
    when the file contains raw browser request headers. A JSON auth file is
    reused directly, so rerunning the script does not try to parse JSON as
    plain-text headers.

    Unless ``verify`` is false, the credentials are checked against YouTube
    Music before returning, so a stale paste is reported at startup instead
    of part-way through a long queue of playlists.
    """

    if (
        not auth_path.is_file()
        and auth_path == YTMUSIC_AUTH_PATH
        and LEGACY_AUTH_PATH.is_file()
        and LEGACY_AUTH_PATH.read_text(encoding="utf-8-sig").strip()
    ):
        # Renamed from browser.json, which said nothing about what it holds.
        print(
            f"Reading credentials from {LEGACY_AUTH_PATH.name}, which is now "
            f"called {YTMUSIC_AUTH_PATH.name}. Rename it when convenient:\n"
            f"  git mv backend/{LEGACY_AUTH_PATH.name} backend/{YTMUSIC_AUTH_PATH.name}"
        )
        auth_path = LEGACY_AUTH_PATH

    if not auth_path.is_file():
        raise FileNotFoundError(
            f"Could not find {auth_path.name}; copy "
            f"{YTMUSIC_AUTH_PATH.name}.example to {YTMUSIC_AUTH_PATH.name} and "
            "paste your authenticated YouTube Music request headers into it"
        )

    raw_headers = auth_path.read_text(encoding="utf-8-sig")
    if not raw_headers.strip():
        raise ValueError(
            f"{auth_path.name} is empty; paste authenticated YouTube Music request headers into it"
        )

    auth_config = parse_browser_headers(raw_headers)

    # Persist the normalized object so youtubemusic.json becomes valid JSON after
    # the first run, while still accepting raw pasted headers as input.
    auth_path.write_text(
        json.dumps(auth_config, ensure_ascii=True, indent=4, sort_keys=True),
        encoding="utf-8",
    )

    if not verify:
        return YTMusic(auth_config)

    # Dropping the volatile cookies is what makes a pasted session last, but
    # it is not worth failing over: if the trimmed set is rejected, exactly
    # what the user pasted is tried before giving up.
    trimmed = _without_volatile_cookies(auth_config)
    candidates = [trimmed]
    if trimmed.get("cookie") != auth_config.get("cookie"):
        candidates.append(dict(auth_config))

    for candidate in candidates:
        ytmusic = YTMusic(candidate)
        account = _signed_in_account(ytmusic)
        if account is not None:
            print(f"YouTube Music: signed in as {account}")
            return ytmusic

    raise ValueError(
        "The credentials in youtubemusic.json are not signed in to YouTube "
        "Music. They have expired, or the copy was taken from a browser "
        "session that has since moved on.\n\n" + _AUTH_PASTE_HELP
    )


def _unwrap_spotify_track(item: object) -> Mapping[str, object] | None:
    """Extract the track data from the current SpotAPI GraphQL wrapper."""

    if not isinstance(item, Mapping):
        return None

    # SpotAPI currently returns itemV2.data. The fallbacks keep this script
    # readable if SpotAPI returns one of its older or simpler representations.
    candidate: object = item
    for key in ("itemV2", "item", "track"):
        if isinstance(candidate, Mapping) and isinstance(candidate.get(key), Mapping):
            candidate = candidate[key]
            break

    if isinstance(candidate, Mapping) and isinstance(candidate.get("data"), Mapping):
        candidate = candidate["data"]

    return candidate if isinstance(candidate, Mapping) else None


def _artist_names(track: Mapping[str, object]) -> list[str]:
    artists = track.get("artists")
    if isinstance(artists, Mapping):
        artists = artists.get("items")
    if not isinstance(artists, list):
        return []

    names = []
    for artist in artists:
        if not isinstance(artist, Mapping):
            continue
        profile = artist.get("profile")
        name = artist.get("name")
        if not isinstance(name, str) and isinstance(profile, Mapping):
            name = profile.get("name")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
    return names


def get_spotify_tracks(playlist_id: str) -> tuple[list[dict[str, object]], int]:
    """Fetch all playlist pages with SpotAPI and normalize playable tracks."""

    tracks: list[dict[str, object]] = []
    skipped_tracks = 0
    fetched_items = 0
    total_items = 0
    terminal_width = shutil.get_terminal_size(fallback=(120, 24)).columns
    previous_status_length = _write_progress(
        "Fetching Spotify",
        0,
        1,
        "playlist tracks",
        0,
        terminal_width,
    )

    try:
        playlist = PublicPlaylist(playlist_id)
        for page in playlist.paginate_playlist():
            if not isinstance(page, Mapping) or not isinstance(page.get("items"), list):
                raise RuntimeError("SpotAPI returned an unexpected playlist response")

            page_items = page["items"]
            fetched_items += len(page_items)
            page_total = page.get("totalCount")
            if isinstance(page_total, int) and page_total >= fetched_items:
                total_items = page_total
            elif total_items == 0:
                total_items = fetched_items

            previous_status_length = _write_progress(
                "Fetching Spotify",
                fetched_items,
                total_items,
                "playlist tracks",
                previous_status_length,
                terminal_width,
            )

            for item in page_items:
                track = _unwrap_spotify_track(item)
                if track is None:
                    skipped_tracks += 1
                    continue

                name = track.get("name")
                artists = _artist_names(track)
                if not isinstance(name, str) or not name.strip() or not artists:
                    # Removed, local, or otherwise unavailable Spotify items do not
                    # contain enough metadata to search YouTube Music reliably.
                    skipped_tracks += 1
                    continue

                tracks.append({"name": name.strip(), "artists": artists})
    finally:
        sys.stdout.write("\n")
        sys.stdout.flush()

    # SpotAPI advances its paging offset by the page size it asked for rather
    # than by the number of items Spotify actually returned, so a short page
    # would silently skip tracks. Compare against the playlist's own total so
    # that loss is reported rather than quietly accepted.
    if total_items and fetched_items < total_items:
        print(
            f"  Warning: Spotify returned {fetched_items} of {total_items} "
            "items for this playlist; the rest could not be read and will be "
            "missing from the transfer."
        )

    if not tracks:
        raise RuntimeError("The Spotify playlist contains no playable tracks")

    return tracks, skipped_tracks


def get_video_ids(
    ytmusic: YTMusic,
    tracks: list[dict[str, object]],
    progress: dict[str, object],
) -> tuple[list[str], list[str]]:
    """Search YouTube Music for each Spotify track, preserving playlist order.

    Every completed track updates ``progress["current"]`` and the whole
    queue file is written immediately, so an auth expiry, crash, or Ctrl+C
    never loses more than the single track being searched. Resuming starts
    after the last track recorded for the current playlist.
    """

    current = progress["current"]
    video_ids: list[str] = list(current.get("video_ids") or [])
    missed_tracks: list[str] = list(current.get("missed_tracks") or [])
    start_index = int(current.get("searched") or 0)
    if not 0 <= start_index <= len(tracks):
        start_index = 0

    started_at = time.monotonic()
    terminal_width = shutil.get_terminal_size(fallback=(120, 24)).columns
    previous_status_length = 0

    if start_index:
        print(
            f"Resuming search from track {start_index + 1} of {len(tracks)} "
            f"({len(video_ids)} already found, {len(missed_tracks)} not on YouTube Music)"
        )
    else:
        print(f"Searching for {len(tracks)} songs on YouTube Music")

    for index in range(start_index, len(tracks)):
        track = tracks[index]
        name = str(track["name"])
        artists = track.get("artists")
        artist_names = artists if isinstance(artists, list) else []
        search_string = " ".join([name, *[str(artist) for artist in artist_names]])
        label = f"{name} - {', '.join(str(artist) for artist in artist_names)}"
        previous_status_length = _write_progress(
            "Searching",
            index + 1,
            len(tracks),
            label,
            previous_status_length,
            terminal_width,
        )

        try:
            results = ytmusic.search(search_string, filter="songs")
            video_id = next(
                (
                    result.get("videoId")
                    for result in results
                    if isinstance(result, Mapping)
                    and isinstance(result.get("videoId"), str)
                    and result["videoId"]
                ),
                None,
            )
        except Exception as error:
            if _is_auth_error(error):
                raise AuthExpiredError(
                    "your YouTube Music headers have expired or are no longer valid",
                    index,
                    len(tracks),
                    str(current.get("playlist_name") or ""),
                ) from error
            video_id = None

        if video_id is None:
            missed_tracks.append(label)
        else:
            video_ids.append(video_id)

        # Persist immediately so restarting never repeats finished searches.
        current["video_ids"] = video_ids
        current["missed_tracks"] = missed_tracks
        current["searched"] = index + 1
        _save_progress(progress)

    sys.stdout.write("\n")
    sys.stdout.flush()
    elapsed = time.monotonic() - started_at
    print(
        f"Found {len(video_ids)}/{len(tracks)} songs on YouTube Music in "
        f"{elapsed:.2f} seconds. {len(missed_tracks)} songs not found."
    )

    if not video_ids:
        raise RuntimeError("No Spotify tracks were found on YouTube Music")

    return video_ids, missed_tracks


def _create_playlist_with_auth_check(
    ytmusic: YTMusic,
    playlist_name: str,
    video_ids: list[str],
) -> str:
    """Create the YouTube Music playlist, raising AuthExpiredError on bad auth."""

    try:
        created_playlist_id = ytmusic.create_playlist(
            playlist_name,
            "",
            "PRIVATE",
            video_ids,
        )
    except Exception as error:
        if _is_auth_error(error):
            raise AuthExpiredError(
                "your YouTube Music headers have expired or are no longer valid",
                len(video_ids),
                len(video_ids),
                playlist_name,
            ) from error
        raise
    if not isinstance(created_playlist_id, str) or not created_playlist_id:
        raise RuntimeError("YouTube Music did not return a playlist ID")

    return created_playlist_id


def _transfer_current(ytmusic: YTMusic, progress: dict[str, object]) -> dict[str, object]:
    """Transfer the playlist held in ``progress["current"]`` and describe it."""

    current = progress["current"]
    playlist_name = str(current["playlist_name"])
    tracks = list(current["tracks"])
    skipped_tracks = int(current.get("skipped_tracks") or 0)

    if skipped_tracks:
        print(f"Skipped {skipped_tracks} Spotify playlist item(s) without usable metadata")

    video_ids, missed_tracks = get_video_ids(ytmusic, tracks, progress)
    current["search_complete"] = True
    _save_progress(progress)

    created_playlist_id = _create_playlist_with_auth_check(
        ytmusic,
        playlist_name,
        video_ids,
    )

    return {
        "playlist_id": current["playlist_id"],
        "playlist_name": playlist_name,
        "created_playlist_id": created_playlist_id,
        "missed_tracks": missed_tracks,
    }


def transfer_playlists() -> list[dict[str, object]]:
    """Transfer every configured Spotify playlist, resuming where needed.

    Playlists are transferred in the order listed in ``setup.py``. Each one
    that finishes is recorded in ``transfer_progress.json``, so an auth
    expiry part-way through a queue only ever repeats the playlist that was
    in flight, never the ones already created.
    """

    queue = _validate_setup()
    queue_ids = [playlist_id for _, playlist_id in queue]

    progress = _load_progress(queue_ids)
    if progress is None:
        progress = {
            "version": _PROGRESS_VERSION,
            "queue": queue_ids,
            "done": [],
            "current": None,
        }

    done: list[dict[str, object]] = [
        entry for entry in progress["done"] if isinstance(entry, Mapping)
    ]
    completed_ids = {entry.get("playlist_id") for entry in done}
    pending = [pair for pair in queue if pair[1] not in completed_ids]

    if not pending:
        print("Every configured playlist has already been transferred")
        _clear_progress()
        return done

    if len(queue) > 1:
        if done:
            print(
                f"{len(queue)} playlists configured: {len(done)} already "
                f"transferred, {len(pending)} to go"
            )
        else:
            print(f"{len(queue)} playlists configured")

    # youtubemusic.json is re-read and re-parsed on every run, so headers pasted
    # after an auth expiry are always picked up before resuming.
    ytmusic = load_ytmusic()

    for position, (link, playlist_id) in enumerate(pending, start=1):
        if position > 1:
            print()

        # Counted against the whole queue rather than the pending slice, so
        # the number does not restart at 1 after a resume.
        marker = f"[playlist {len(done) + 1}/{len(queue)}]"

        saved = progress.get("current")
        resuming = (
            isinstance(saved, Mapping)
            and saved.get("playlist_id") == playlist_id
            and isinstance(saved.get("tracks"), list)
        )

        if resuming:
            current = dict(saved)
            print(
                f"{marker} Resuming '{current['playlist_name']}' "
                f"({current.get('searched') or 0}/{len(current['tracks'])} "
                "tracks already searched)"
            )
        else:
            playlist_name = get_spotify_playlist_name(link)
            print(f"{marker} {playlist_name}")
            tracks, skipped_tracks = get_spotify_tracks(playlist_id)
            current = {
                "playlist_id": playlist_id,
                "playlist_link": link,
                "playlist_name": playlist_name,
                "tracks": tracks,
                "skipped_tracks": skipped_tracks,
                "video_ids": [],
                "missed_tracks": [],
                "searched": 0,
                "search_complete": False,
            }

        progress["current"] = current
        _save_progress(progress)

        result = _transfer_current(ytmusic, progress)

        # Only record the playlist as done once YouTube Music has created it.
        done.append(result)
        progress["done"] = done
        progress["current"] = None
        _save_progress(progress)

        print(f"Created private YouTube Music playlist: {result['playlist_name']}")
        if len(queue) > 1:
            remaining = len(queue) - len(done)
            print(
                f"  Progress: {len(done)}/{len(queue)} playlists transferred"
                + (f", {remaining} remaining" if remaining else " - all done")
            )

    # Every playlist succeeded; nothing left to resume.
    _clear_progress()
    return done


def _print_auth_expired_instructions(error: AuthExpiredError) -> None:
    """Tell the user how to refresh youtubemusic.json and resume the transfer."""

    progress = _read_raw_progress()
    current = progress.get("current") if isinstance(progress, Mapping) else None
    search_complete = bool(isinstance(current, Mapping) and current.get("search_complete"))

    print(
        "\nTransfer paused: your YouTube Music request headers have expired "
        "or are no longer valid.",
        file=sys.stderr,
    )
    if error.playlist_name:
        print(f"Stopped while transferring '{error.playlist_name}'.", file=sys.stderr)
    if search_complete:
        print(
            f"All {error.tracks_done} tracks were already searched, only the "
            "final playlist needs to be created.",
            file=sys.stderr,
        )
    else:
        print(
            f"Progress was saved at track {error.tracks_done} of "
            f"{error.tracks_total}; nothing found so far will be lost.",
            file=sys.stderr,
        )

    if isinstance(progress, Mapping):
        queue = progress.get("queue")
        finished = progress.get("done")
        if isinstance(queue, list) and isinstance(finished, list) and len(queue) > 1:
            print(
                f"{len(finished)} of {len(queue)} playlists are already finished "
                "and will not be transferred again.",
                file=sys.stderr,
            )

    print("\nTo continue:", file=sys.stderr)
    print(_AUTH_PASTE_HELP, file=sys.stderr)
    print(
        "\nThen run this script again. It picks up the new credentials and\n"
        "resumes exactly where the transfer stopped. There is no need to press\n"
        "anything here.",
        file=sys.stderr,
    )


def main() -> int:
    try:
        results = transfer_playlists()
    except AuthExpiredError as error:
        _print_auth_expired_instructions(error)
        return 1
    except Exception as error:
        print(f"Transfer failed: {error}", file=sys.stderr)
        return 1

    if not results:
        print("Nothing to transfer")
        return 0

    print()
    if len(results) == 1:
        result = results[0]
        print(f"Created private YouTube Music playlist: {result['playlist_name']}")
        print(f"Playlist ID: {result['created_playlist_id']}")
    else:
        print(f"Transferred {len(results)} playlists:")
        for result in results:
            missed = result["missed_tracks"]
            print(
                f"- {result['playlist_name']} "
                f"(ID: {result['created_playlist_id']}, "
                f"{len(missed)} track(s) not found)"
            )

    for result in results:
        missed_tracks = result["missed_tracks"]
        if missed_tracks:
            print(f"\nTracks not added from '{result['playlist_name']}':")
            for track in missed_tracks:
                print(f"- {track}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
