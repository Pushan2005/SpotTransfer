import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_response_data(response, operation):
    """Return Spotify JSON or raise an error with the API's useful message."""
    try:
        data = response.json()
    except ValueError:
        data = {}

    if not response.ok:
        error = data.get("error", {}) if isinstance(data, dict) else {}
        message = error.get("message") or response.reason or "Unknown Spotify API error"
        raise Exception(f"Spotify API failed while {operation} ({response.status_code}): {message}")

    return data



def get_spotify_access_token(client_id, client_secret):
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(url, headers=headers, data=data)
    data = get_response_data(response, "getting an access token")
    return data["access_token"]


def extract_playlist_id(playlist_url):
    return playlist_url.split("/playlist/")[1].split("?")[0]

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
        response = requests.get(url, headers=headers)
        data = get_response_data(response, "retrieving playlist tracks")
        for item in data["items"]:
            track = item["track"]
            if not track or track.get("is_local") or track.get("restrictions"):
                continue
            all_tracks.append({
                "name": track["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "album": track["album"]["name"],
            })
        url = data.get("next")
        if url == 'null':
            break
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
    
    response = requests.get(url, headers=headers)
    data = get_response_data(response, "retrieving the playlist name")
    return data["name"]
    
    
    


