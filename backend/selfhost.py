"""Transfer a Spotify playlist to YouTube Music from a local machine.

Before running this file:

1. Copy the request headers from an authenticated ``music.youtube.com``
   ``/browse`` request into ``browser.json``.
2. Set ``spotify_playlist_link`` in ``setup.py``.
3. Run this file with the Python interpreter from ``backend/venv``.

The first run converts the pasted headers in ``browser.json`` into the
ytmusicapi authentication format. Future runs can reuse that generated JSON
until the browser session expires.
"""

from __future__ import annotations

import json
import re
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
BROWSER_AUTH_PATH = BASE_DIR / "browser.json"
_PLAYLIST_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{22}$")
_PLACEHOLDER_SPOTIFY_LINK = "Replace this with the Spotify playlist link"


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


def _validate_setup() -> str:
    """Validate the editable setup values and return the Spotify playlist ID."""

    if (
        not isinstance(spotify_playlist_link, str)
        or not spotify_playlist_link.strip()
        or spotify_playlist_link.strip() == _PLACEHOLDER_SPOTIFY_LINK
    ):
        raise ValueError("Edit spotify_playlist_link before running the script")

    return extract_spotify_playlist_id(spotify_playlist_link)


def get_spotify_playlist_name(playlist_link: str) -> str:
    """Fetch the playlist name from a Spotify playlist link with SpotAPI."""

    playlist_id = extract_spotify_playlist_id(playlist_link)
    playlist = PublicPlaylist(playlist_id)
    response = playlist.get_playlist_info(limit=1)

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


def parse_browser_headers(raw_headers: str) -> dict[str, object]:
    """Parse pasted headers into the JSON object expected by ``YTMusic``.

    Plain request headers are intentionally allowed in ``browser.json``; the
    file does not need to be valid JSON when the user pastes them. ytmusicapi's
    setup parser also adds the derived browser-auth headers required by YTMusic.
    """

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
                "browser.json contains JSON, but not browser request headers "
                "or a ytmusicapi auth object"
            )
        raw_headers = raw_from_object

    try:
        normalized_json = ytmusicapi.setup(headers_raw=raw_headers)
        normalized_headers = json.loads(normalized_json)
    except Exception as error:
        raise ValueError(
            "Could not parse browser.json as YouTube Music request headers"
        ) from error

    if not _is_auth_config(normalized_headers):
        raise ValueError("Parsed browser headers do not contain YouTube Music auth data")
    return dict(normalized_headers)


def load_ytmusic(auth_path: Path = BROWSER_AUTH_PATH) -> YTMusic:
    """Load YTMusic auth from pasted headers or an existing auth JSON file.

    ytmusicapi.setup() writes the normalized credentials back to ``auth_path``
    when the file contains raw browser request headers. A JSON auth file is
    reused directly, so rerunning the script does not try to parse JSON as
    plain-text headers.
    """

    if not auth_path.is_file():
        raise FileNotFoundError(
            f"Could not find {auth_path.name}; create it and paste your "
            "authenticated YouTube Music request headers into it"
        )

    raw_headers = auth_path.read_text(encoding="utf-8-sig")
    if not raw_headers.strip():
        raise ValueError(
            f"{auth_path.name} is empty; paste authenticated YouTube Music request headers into it"
        )

    auth_config = parse_browser_headers(raw_headers)

    # Persist the normalized object so browser.json becomes valid JSON after
    # the first run, while still accepting raw pasted headers as input.
    auth_path.write_text(
        json.dumps(auth_config, ensure_ascii=True, indent=4, sort_keys=True),
        encoding="utf-8",
    )
    return YTMusic(auth_config)


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

    playlist = PublicPlaylist(playlist_id)
    tracks: list[dict[str, object]] = []
    skipped_tracks = 0

    for page in playlist.paginate_playlist():
        if not isinstance(page, Mapping) or not isinstance(page.get("items"), list):
            raise RuntimeError("SpotAPI returned an unexpected playlist response")

        for item in page["items"]:
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

    if not tracks:
        raise RuntimeError("The Spotify playlist contains no playable tracks")

    return tracks, skipped_tracks


def get_video_ids(ytmusic: YTMusic, tracks: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    """Search YouTube Music for each Spotify track, preserving playlist order."""

    video_ids: list[str] = []
    missed_tracks: list[str] = []
    started_at = time.monotonic()

    print(f"Searching for {len(tracks)} songs on YouTube Music")
    for index, track in enumerate(tracks, start=1):
        name = str(track["name"])
        artists = track.get("artists")
        artist_names = artists if isinstance(artists, list) else []
        search_string = " ".join([name, *[str(artist) for artist in artist_names]])
        label = f"{name} - {', '.join(str(artist) for artist in artist_names)}"
        print(f"Searching for song {index}/{len(tracks)}: {label}")

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
        except Exception:
            video_id = None

        if video_id is None:
            print(f"Not found on YouTube Music: {label}")
            missed_tracks.append(label)
            continue

        video_ids.append(video_id)

    elapsed = time.monotonic() - started_at
    print(
        f"Found {len(video_ids)}/{len(tracks)} songs on YouTube Music in "
        f"{elapsed:.2f} seconds. {len(missed_tracks)} songs not found."
    )

    if not video_ids:
        raise RuntimeError("No Spotify tracks were found on YouTube Music")

    return video_ids, missed_tracks


def transfer_playlist() -> tuple[str, list[str], str]:
    """Run the complete local Spotify-to-YouTube Music transfer."""

    playlist_id = _validate_setup()
    playlist_name = get_spotify_playlist_name(spotify_playlist_link)
    ytmusic = load_ytmusic()
    tracks, skipped_tracks = get_spotify_tracks(playlist_id)
    if skipped_tracks:
        print(f"Skipped {skipped_tracks} Spotify playlist item(s) without usable metadata")

    video_ids, missed_tracks = get_video_ids(ytmusic, tracks)
    created_playlist_id = ytmusic.create_playlist(
        playlist_name,
        "",
        "PRIVATE",
        video_ids,
    )
    if not isinstance(created_playlist_id, str) or not created_playlist_id:
        raise RuntimeError("YouTube Music did not return a playlist ID")

    return created_playlist_id, missed_tracks, playlist_name


def main() -> int:
    try:
        created_playlist_id, missed_tracks, playlist_name = transfer_playlist()
    except Exception as error:
        print(f"Transfer failed: {error}", file=sys.stderr)
        return 1

    print(f"Created private YouTube Music playlist: {playlist_name}")
    print(f"Playlist ID: {created_playlist_id}")
    if missed_tracks:
        print("Tracks not added:")
        for track in missed_tracks:
            print(f"- {track}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
