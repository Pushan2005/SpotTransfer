"""Spotify playlist access — the source platform.

All Spotify-specific code lives here: URL validation and playlist
fetching via SpotAPI. This is the source side of the transfer; sibling
modules (ytm.py today, future platforms like apple.py or tidal.py) hold
the destination side, and main.py composes them.

Track format returned by ``get_tracks``:

    {"name": "Song title", "artists": ["Artist One", "Artist Two"]}

spotapi is imported lazily inside the functions so importing this module
never fails before the desktop venv bootstrap (see main.ensure_deps).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from urllib.parse import urlparse

from logging_config import configure_logging, logger

configure_logging()

_PLAYLIST_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{22}$")


def extract_playlist_id(playlist_link: str) -> str:
    """Validate a Spotify playlist URL and return its playlist ID."""

    if not isinstance(playlist_link, str):
        raise ValueError("the playlist link must be a Spotify playlist URL")

    value = playlist_link.strip()
    parsed = urlparse(value)
    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("the playlist link is not a valid URL") from error

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or hostname not in {"open.spotify.com", "www.open.spotify.com"}
        or port is not None
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            "the playlist link must use an open.spotify.com playlist URL"
        )

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) != 2 or path_parts[0].lower() != "playlist":
        raise ValueError(
            "the playlist link must have the form "
            "https://open.spotify.com/playlist/<playlist-id>"
        )

    playlist_id = path_parts[1]
    if not _PLAYLIST_ID_PATTERN.fullmatch(playlist_id):
        raise ValueError("the playlist link contains an invalid Spotify playlist ID")

    return playlist_id


def get_playlist_name(playlist_link: str) -> str:
    """Fetch the playlist name from a public Spotify playlist link."""

    from spotapi import PublicPlaylist

    playlist_id = extract_playlist_id(playlist_link)
    logger.info("Fetching Spotify playlist metadata (id=%s)", playlist_id)

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

    logger.info("Spotify playlist: '%s' (id=%s)", name.strip(), playlist_id)
    return name.strip()


def _unwrap_spotify_track(item: object) -> Mapping[str, object] | None:
    """Extract the track data from the current SpotAPI GraphQL wrapper."""

    if not isinstance(item, Mapping):
        return None

    # SpotAPI currently returns itemV2.data. The fallbacks keep this module
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


def get_tracks(
    playlist_id: str,
    on_page: Callable[[int, int], None] | None = None,
) -> tuple[list[dict[str, object]], int]:
    """Fetch all playlist pages with SpotAPI and normalize playable tracks.

    ``on_page``, when given, is called as ``on_page(fetched_items,
    total_items)`` after each page. It lets callers observe fetch
    progress or abort the fetch by raising.
    """

    from spotapi import PublicPlaylist

    tracks: list[dict[str, object]] = []
    skipped_tracks = 0
    fetched_items = 0
    total_items = 0

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

        if on_page is not None:
            on_page(fetched_items, total_items)

        logger.info("Spotify page: fetched %d/%d items",
                    fetched_items, total_items)
        for item in page_items:
            track = _unwrap_spotify_track(item)
            if track is None:
                skipped_tracks += 1
                continue

            name = track.get("name")
            artists = _artist_names(track)
            if not isinstance(name, str) or not name.strip() or not artists:
                # Removed, local, or otherwise unavailable Spotify items do
                # not contain enough metadata to search a destination
                # platform such as YouTube Music reliably.
                skipped_tracks += 1
                continue

            tracks.append({"name": name.strip(), "artists": artists})

    if not tracks:
        raise RuntimeError("The Spotify playlist contains no playable tracks")

    return tracks, skipped_tracks
