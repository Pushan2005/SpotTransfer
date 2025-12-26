from ytmusicapi import YTMusic
import ytmusicapi
from spotify import get_all_tracks, get_playlist_name


def get_video_ids(ytmusic,tracks):
    video_ids = []
    missed_tracks = {
        "count": 0,
        "tracks": []
    }
    total = len(tracks)
    print(f"Searching for {total} tracks on YouTube Music...")
    for i, track in enumerate(tracks, 1):
        try :
            search_string = f"{track['name']} {track['artists'][0]}"
            video_id = ytmusic.search(search_string, filter="songs")[0]["videoId"]
            video_ids.append(video_id)
            if i % 10 == 0:
                print(f"Progress: {i}/{total} tracks processed...")
        except :
            print(f"{track['name']} {track['artists'][0]} not found on YouTube Music")
            missed_tracks["count"] += 1
            missed_tracks["tracks"].append(f"{track['name']} {track['artists'][0]}")
    print(f"Found {len(video_ids)} songs on YouTube Music")
    if len(video_ids) == 0:
        raise Exception("No songs found on YouTube Music")
    return video_ids, missed_tracks


def create_ytm_playlist(playlist_link, headers):
    print("Setting up YouTube Music authentication...")

    try:
        ytmusicapi.setup(filepath="header_auth.json", headers_raw=headers)
    except Exception as e:
        print(f"Error in ytmusicapi setup: {e}")
        raise

    try:
        ytmusic = YTMusic("header_auth.json")

        try:
            ytmusic.search("test", limit=1)
        except KeyError:
            pass
        except Exception as search_err:
            if "Expecting value" in str(search_err):
                raise Exception(f"YouTube Music authentication failed. Your headers may have expired or are invalid.")
    except Exception as e:
        if "authentication failed" in str(e).lower():
            raise
        print(f"Error creating YTMusic instance: {e}")
        raise

    print("Fetching Spotify playlist...")
    tracks = get_all_tracks(playlist_link, "IN")
    name = get_playlist_name(playlist_link)
    print(f"Found playlist '{name}' with {len(tracks)} tracks")
    video_ids, missed_tracks = get_video_ids(ytmusic, tracks)
    print("Creating YouTube Music playlist...")
    ytmusic.create_playlist(name, "", "PRIVATE", video_ids)
    print("Playlist created successfully!")
    return {
        "playlist_name": name,
        "missed_tracks": missed_tracks
    }

