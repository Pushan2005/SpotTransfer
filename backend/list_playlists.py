"""List every Spotify playlist in your library into a reviewable text file.

Run this before ``selfhost.py`` when you want to transfer many playlists at
once:

1. Put your Spotify session cookies in ``spotify.json``
   (copy ``spotify.json.example`` and fill it in).
2. Run ``python3 list_playlists.py``; it writes ``playlists.csv``.
3. Open ``playlists.csv``, delete the rows for playlists you do not want,
   and save the file.
4. Run ``python3 selfhost.py``; it transfers whatever is left in the file.

``playlists.csv`` has one playlist per row as
``name,playlist_id,track_count``, so reviewing it means deleting whole rows,
in a text editor or a spreadsheet. Track counts need one request per playlist;
pass ``--no-counts`` to skip them and finish in seconds.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import random
import sys
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from spotapi import Config, Login, NoopLogger, PrivatePlaylist, PublicPlaylist


BASE_DIR = Path(__file__).resolve().parent
SPOTIFY_AUTH_PATH = BASE_DIR / "spotify.json"
PLAYLISTS_PATH = BASE_DIR / "playlists.csv"

_PLAYLIST_URI_PREFIX = "spotify:playlist:"
# playlists.csv columns, in order. The name comes first so the file is
# readable at a glance and sorts naturally in a spreadsheet. track_count is
# appended rather than inserted because selfhost.py falls back to reading the
# ID from the second column when the header row has been deleted.
CSV_COLUMNS = ("name", "playlist_id", "track_count")
# Spotify caps a libraryV3 page at the requested limit and returns the real
# size in totalCount, so the library has to be walked page by page. 500 is the
# largest page size observed to come back intact.
_LIBRARY_PAGE_SIZE = 500
# Track counts cost one request per playlist. Sequentially that is roughly
# half an hour for a large account, so they are fetched in a small pool.
# Spotify throttles a sustained run of these regardless of how many threads
# are used, so the pool is deliberately small and every failure is retried
# with an exponential backoff; a throttled request succeeds moments later.
_COUNT_WORKERS = 6
_COUNT_RETRIES = 4
_COUNT_BACKOFF_SECONDS = 2.0


def _playlist_name(node: Mapping[str, object]) -> str:
    """Pull a display name out of a playlist node, whatever shape it has."""

    for key in ("name", "title"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Some responses nest the human-readable fields one level down.
    for key in ("attributes", "data", "playlist"):
        nested = node.get(key)
        if isinstance(nested, Mapping):
            name = _playlist_name(nested)
            if name != "Untitled playlist":
                return name

    return "Untitled playlist"


def _collect_playlists(
    node: object,
    found: list[dict[str, str]],
    seen: set[str],
) -> None:
    """Walk a GraphQL response and collect every playlist it mentions.

    Spotify's private library response nests playlists differently depending
    on folders and account features, so the whole payload is searched for
    playlist URIs rather than following one fixed path that could break.
    """

    if isinstance(node, Mapping):
        uri = node.get("uri")
        if isinstance(uri, str) and uri.startswith(_PLAYLIST_URI_PREFIX):
            playlist_id = uri[len(_PLAYLIST_URI_PREFIX) :].strip()
            if playlist_id and playlist_id not in seen:
                seen.add(playlist_id)
                found.append({"id": playlist_id, "name": _playlist_name(node)})

        for value in node.values():
            _collect_playlists(value, found, seen)

    elif isinstance(node, list):
        for value in node:
            _collect_playlists(value, found, seen)


def load_spotify_login() -> Login:
    """Build a logged-in SpotAPI session from the cookies in spotify.json."""

    if not SPOTIFY_AUTH_PATH.is_file():
        raise FileNotFoundError(
            f"Could not find {SPOTIFY_AUTH_PATH.name}. Copy "
            "spotify.json.example to spotify.json and fill in your Spotify "
            "account email and session cookies."
        )

    try:
        data = json.loads(SPOTIFY_AUTH_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{SPOTIFY_AUTH_PATH.name} is not valid JSON. It must look like "
            '{"identifier": "you@example.com", "cookies": "sp_dc=..."}'
        ) from error

    if not isinstance(data, Mapping):
        raise ValueError(f"{SPOTIFY_AUTH_PATH.name} must contain a JSON object")

    identifier = data.get("identifier")
    cookies = data.get("cookies")

    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError(
            f'Set "identifier" in {SPOTIFY_AUTH_PATH.name} to the email address '
            "or username of your Spotify account"
        )
    if not isinstance(cookies, (str, Mapping)) or not cookies:
        raise ValueError(
            f'Set "cookies" in {SPOTIFY_AUTH_PATH.name} to the cookie string '
            "copied from an open.spotify.com request"
        )

    cookie_text = cookies if isinstance(cookies, str) else ";".join(cookies)
    if "sp_dc" not in cookie_text:
        raise ValueError(
            f'The "cookies" value in {SPOTIFY_AUTH_PATH.name} does not contain '
            "sp_dc, which is the cookie that proves you are logged in. Copy the "
            "whole cookie header from open.spotify.com and try again."
        )

    return Login.from_cookies(
        {"identifier": identifier.strip(), "cookies": cookies},
        Config(logger=NoopLogger()),
    )


def _library_node(page: object) -> Mapping[str, object]:
    """Return the libraryV3 node of a response, or an empty mapping."""

    node: object = page
    for key in ("data", "me", "libraryV3"):
        if not isinstance(node, Mapping):
            return {}
        node = node.get(key)
    return node if isinstance(node, Mapping) else {}


def _library_page(
    library: PrivatePlaylist,
    limit: int,
    offset: int,
) -> Mapping[str, object]:
    """Fetch one page of the library.

    ``PrivatePlaylist.get_library`` hardcodes ``offset: 0``, so on its own it
    can only ever see the first page and silently drops every playlist past
    it. The same query is reissued here with the offset filled in. The
    persisted-query hash and the HTTP client are SpotAPI's own, so this keeps
    following SpotAPI when it updates them.
    """

    url = "https://api-partner.spotify.com/pathfinder/v1/query"
    params = {
        "operationName": "libraryV3",
        "variables": json.dumps(
            {
                "filters": [],
                "order": None,
                "textFilter": "",
                "features": ["LIKED_SONGS", "YOUR_EPISODES", "PRERELEASES"],
                "limit": limit,
                "offset": offset,
                "flatten": False,
                "expandedFolders": [],
                "folderUri": None,
                "includeFoldersWhenFlattening": True,
            }
        ),
        "extensions": json.dumps(
            {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": library.base.part_hash("libraryV3"),
                }
            }
        ),
    }

    response = library.login.client.post(url, params=params, authenticate=True)
    if response.fail:
        raise RuntimeError(
            f"Could not read your Spotify library: {response.error.string}"
        )
    return response.response


def fetch_library_playlists(login: Login) -> list[dict[str, str]]:
    """Return every playlist in the logged-in account's library.

    The library holds albums, artists and podcasts alongside playlists, so the
    page counts below are library entries rather than playlists; only a subset
    of each page turns into a row in playlists.csv.
    """

    library = PrivatePlaylist(login)

    found: list[dict[str, str]] = []
    seen: set[str] = set()
    offset = 0
    total = 0

    while True:
        node = _library_node(_library_page(library, _LIBRARY_PAGE_SIZE, offset))
        items = node.get("items")
        if not isinstance(items, list) or not items:
            break

        _collect_playlists(items, found, seen)

        total_count = node.get("totalCount")
        if isinstance(total_count, int) and total_count > total:
            total = total_count

        # Advance by what the server actually returned rather than by the
        # requested limit, so a short page cannot skip over entries.
        offset += len(items)
        print(f"  scanned {min(offset, total)}/{total} library entries", flush=True)

        if offset >= total:
            break

    if not found:
        raise RuntimeError(
            "No playlists were found in your Spotify library. If you do have "
            "playlists, your session cookies have probably expired; copy a "
            f"fresh set into {SPOTIFY_AUTH_PATH.name} and try again."
        )

    return found


def _playlist_track_count(playlist_id: str, retries: int) -> int | None:
    """Return one playlist's track count, retrying through throttling.

    Spotify starts refusing these after a sustained run of them. The refusal
    is temporary and not distinguishable from a genuine failure by its shape,
    so every error is retried before the count is given up on.
    """

    delay = _COUNT_BACKOFF_SECONDS
    for attempt in range(retries + 1):
        try:
            response = PublicPlaylist(playlist_id).get_playlist_info(limit=1)
            count = response["data"]["playlistV2"]["content"]["totalCount"]
            return count if isinstance(count, int) else None
        except Exception:
            if attempt == retries:
                return None
            # Jitter keeps the pool's threads from retrying in lockstep and
            # tripping the same limit again together.
            time.sleep(delay + random.uniform(0.0, 0.5))
            delay *= 2
    return None


def fetch_track_counts(
    playlists: list[dict[str, str]],
    workers: int = _COUNT_WORKERS,
    retries: int = _COUNT_RETRIES,
) -> int:
    """Fill in each playlist's ``track_count`` in place; return how many failed.

    The library response carries a count only for the pseudo-playlists (Liked
    Songs, Your Episodes), never for real playlists, so every count costs its
    own request. Playlists that already have a count are left alone, so a run
    interrupted by throttling can be topped up rather than repeated.
    """

    pending = [p for p in playlists if not str(p.get("track_count", "")).strip()]
    known = len(playlists) - len(pending)
    if known:
        print(f"  {known} playlist(s) already counted; fetching the other {len(pending)}", flush=True)
    if not pending:
        return 0

    counted = 0
    total = len(pending)

    def fetch(playlist: dict[str, str]) -> tuple[dict[str, str], int | None]:
        return playlist, _playlist_track_count(playlist["id"], retries)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for playlist, count in pool.map(fetch, pending):
            playlist["track_count"] = "" if count is None else str(count)
            counted += 1
            if counted % 25 == 0 or counted == total:
                print(f"  counted {counted}/{total} playlists", flush=True)

    failed = sum(1 for p in pending if not str(p.get("track_count", "")).strip())
    if failed:
        print(
            f"  {failed} playlist(s) still have no count. They are usually "
            "personalised playlists that cannot be read without being their "
            "owner, or Spotify is still throttling. Re-run with "
            "--counts-only to retry just those."
        )
    return failed


def read_existing_playlists() -> list[dict[str, str]]:
    """Read playlists.csv back, preserving row order.

    Used by --counts-only, which tops up missing counts without re-listing the
    library. Keeping the rows and their order identical matters: selfhost.py
    discards saved transfer progress when the set of playlist IDs changes.
    """

    if not PLAYLISTS_PATH.is_file():
        raise FileNotFoundError(
            f"Could not find {PLAYLISTS_PATH.name}. Run this script without "
            "--counts-only first to create it."
        )

    text = PLAYLISTS_PATH.read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    if not rows or "playlist_id" not in rows[0]:
        raise ValueError(
            f"{PLAYLISTS_PATH.name} needs its "
            f"'{','.join(CSV_COLUMNS)}' header row for --counts-only to "
            "know which column is which."
        )

    playlists: list[dict[str, str]] = []
    for row in rows:
        playlist_id = (row.get("playlist_id") or "").strip()
        if not playlist_id:
            continue
        playlists.append(
            {
                "id": playlist_id,
                "name": (row.get("name") or "").strip(),
                "track_count": (row.get("track_count") or "").strip(),
            }
        )
    return playlists


def render_playlists_file(playlists: list[dict[str, str]]) -> str:
    """Render the reviewable playlists.csv contents.

    Written with the csv module because playlist names routinely contain
    commas and quotes, which a hand-rolled join would corrupt.
    """

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)

    for playlist in playlists:
        # Collapse any newlines so one playlist always occupies one row.
        name = " ".join(playlist["name"].split())
        writer.writerow([name, playlist["id"], playlist.get("track_count", "")])

    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List every Spotify playlist in your library into playlists.csv"
    )
    parser.add_argument(
        "--no-counts",
        action="store_true",
        help="skip per-playlist track counts, which need one request each",
    )
    parser.add_argument(
        "--counts-only",
        action="store_true",
        help=(
            "do not re-list the library; only fill in missing track counts in "
            "the existing playlists.csv, leaving every row and its order alone"
        ),
    )
    args = parser.parse_args()

    if args.counts_only:
        try:
            playlists = read_existing_playlists()
            print(f"Topping up track counts in {PLAYLISTS_PATH.name}...")
            fetch_track_counts(playlists)
        except Exception as error:
            print(f"Could not update track counts: {error}", file=sys.stderr)
            return 1

        PLAYLISTS_PATH.write_text(
            render_playlists_file(playlists), encoding="utf-8", newline=""
        )
        filled = sum(1 for p in playlists if p.get("track_count"))
        print(f"Updated {PLAYLISTS_PATH.name}: {filled}/{len(playlists)} rows have a track count")
        return 0

    try:
        login = load_spotify_login()
        print("Fetching your Spotify library...")
        playlists = fetch_library_playlists(login)

        if not args.no_counts:
            # Counts already in the file are still valid for the same playlist,
            # so a re-list after throttling does not pay for them twice.
            if PLAYLISTS_PATH.is_file():
                try:
                    known = {
                        previous["id"]: previous["track_count"]
                        for previous in read_existing_playlists()
                        if previous.get("track_count")
                    }
                except Exception:
                    known = {}
                for playlist in playlists:
                    if playlist["id"] in known:
                        playlist["track_count"] = known[playlist["id"]]

            minutes = max(1, round(len(playlists) * 2.4 / _COUNT_WORKERS / 60))
            print(
                f"Counting tracks in {len(playlists)} playlists "
                f"(roughly {minutes} minute(s); use --no-counts to skip)..."
            )
            fetch_track_counts(playlists)
    except Exception as error:
        print(f"Could not list your playlists: {error}", file=sys.stderr)
        return 1

    if PLAYLISTS_PATH.exists():
        backup = PLAYLISTS_PATH.with_name(PLAYLISTS_PATH.name + ".previous")
        # Never silently discard a list the user may have already edited.
        backup.write_text(PLAYLISTS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Kept your previous list as {backup.name}")

    PLAYLISTS_PATH.write_text(
        render_playlists_file(playlists), encoding="utf-8", newline=""
    )

    print(f"Wrote {len(playlists)} playlist(s) to {PLAYLISTS_PATH.name}")
    print()
    print("Next steps:")
    print(f"  1. Open {PLAYLISTS_PATH.name}")
    print("  2. Delete the rows for playlists you do NOT want to transfer")
    print("  3. Save the file")
    print("  4. Run: python3 selfhost.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
