import os
import re
import threading
import time
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_TIMEOUT_SECONDS = float(os.getenv("SPOTIFY_TIMEOUT_SECONDS", 10))
_PLAYLIST_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{22}$")
_token_cache = {
    "access_token": None,
    "expires_at": 0.0,
}
_token_cache_lock = threading.Lock()


class SpotifyAPIError(Exception):
    """An upstream failure without exposing Spotify response contents."""


def _raise_for_spotify_error(response, operation):
    if response.ok:
        return

    retry_after = response.headers.get("Retry-After")
    message = f"Spotify {operation} failed (HTTP {response.status_code})"
    if retry_after:
        message += f"; retry after {retry_after} seconds"
    raise SpotifyAPIError(message)


def get_spotify_access_token(client_id, client_secret):
    if not client_id or not client_secret:
        raise SpotifyAPIError("Spotify credentials are not configured")

    with _token_cache_lock:
        if (
            _token_cache["access_token"]
            and time.monotonic() < _token_cache["expires_at"]
        ):
            return _token_cache["access_token"]

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                timeout=SPOTIFY_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise SpotifyAPIError("Spotify token service is unavailable") from exc

        _raise_for_spotify_error(response, "token request")
        try:
            payload = response.json()
            access_token = payload["access_token"]
            expires_in = float(payload.get("expires_in", 3600))
        except (ValueError, TypeError, KeyError) as exc:
            raise SpotifyAPIError("Spotify returned an invalid token response") from exc

        _token_cache["access_token"] = access_token
        # Refresh one minute early so a token cannot expire during a transfer.
        _token_cache["expires_at"] = time.monotonic() + max(1, expires_in - 60)
        return access_token


def extract_playlist_id(playlist_url):
    if not isinstance(playlist_url, str):
        raise ValueError("Invalid Spotify playlist URL")

    parsed = urlparse(playlist_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Invalid Spotify playlist URL")
    if parsed.netloc.lower() not in {"open.spotify.com", "spotify.com"}:
        raise ValueError("Invalid Spotify playlist URL")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) != 2 or path_parts[0].lower() != "playlist":
        raise ValueError("Invalid Spotify playlist URL")

    playlist_id = path_parts[1]
    if not _PLAYLIST_ID_PATTERN.fullmatch(playlist_id):
        raise ValueError("Invalid Spotify playlist ID")
    return playlist_id


def _spotify_json(response, operation):
    _raise_for_spotify_error(response, operation)
    try:
        return response.json()
    except ValueError as exc:
        raise SpotifyAPIError(f"Spotify returned invalid data for {operation}") from exc


def _spotify_get(url, headers, operation):
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=SPOTIFY_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise SpotifyAPIError(f"Spotify {operation} is unavailable") from exc
    return _spotify_json(response, operation)


def get_all_tracks(link, market):
    playlist_id = extract_playlist_id(link)
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    access_token = get_spotify_access_token(client_id, client_secret)

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?market={market}&limit=100"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    all_tracks = []

    while url:
        data = _spotify_get(url, headers, "playlist tracks request")
        items = data.get("items")
        if not isinstance(items, list):
            raise SpotifyAPIError("Spotify returned an invalid playlist response")

        for item in items:
            track = item.get("track") if isinstance(item, dict) else None
            if not track or track.get("is_local") or track.get("restrictions"):
                continue
            all_tracks.append({
                "name": track["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "album": track["album"]["name"],
            })
        url = data.get("next")
        if url == 'null':
            url = None
    return all_tracks


def get_playlist_name(link):
    playlist_id = extract_playlist_id(link)
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    access_token = get_spotify_access_token(client_id, client_secret)

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    data = _spotify_get(url, headers, "playlist request")
    name = data.get("name")
    if not isinstance(name, str) or not name:
        raise SpotifyAPIError("Spotify returned an invalid playlist name")
    return name
