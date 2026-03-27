import os
import requests
from dotenv import load_dotenv

load_dotenv()




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
    if response.status_code != 200:
        raise Exception(f"Failed to get access token: {response.json()}")
    
    return response.json()["access_token"]


def extract_playlist_id(playlist_url):
    return playlist_url.split("/playlist/")[1].split("?")[0]

def get_all_tracks(link, market):

    playlist_id = extract_playlist_id(link)
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    access_token = get_spotify_access_token(client_id, client_secret)
    
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items?market={market}&limit=100"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    all_tracks = []
    
    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
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
    data = response.json()
    return data["name"]
    
    
    


