from ytmusicapi import YTMusic
import ytmusicapi
import os
import tempfile
from spotify import get_all_tracks, get_playlist_name


def parse_headers(headers_text):
    """
    Convert headers from plain text format to proper HTTP header format.
    Supports both formats:
    - Standard format: "header: value"
    - Plain format: "header\\nvalue\\nheader2\\nvalue2"
    """
    if not isinstance(headers_text, str) or not headers_text.strip():
        raise Exception("Headers cannot be empty")
    
    lines = [line.strip() for line in headers_text.strip().split('\n') if line.strip()]

    # Browsers can copy a complete HTTP request, whose first line is e.g.
    # "POST /youtubei/v1/browse HTTP/2" rather than an HTTP header.
    if lines and " HTTP/" in lines[0] and lines[0].split(" ", 1)[0] in {
        "DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"
    }:
        lines = lines[1:]

    if not lines:
        raise Exception("Headers cannot be empty")
    
    # Check if headers are already in correct format
    first_line = lines[0] if lines else ""
    colon_pos = first_line.find(': ')
    
    if colon_pos > 0 and colon_pos < 50:
        return '\n'.join(lines)
    
    # Filter out the "Decoded:" section - skip lines that are part of decoded content
    cleaned_lines = []
    skip_mode = False
    
    for line in lines:
        # Start skipping when we hit "Decoded:"
        if line == 'Decoded:':
            skip_mode = True
            continue
        
        # Skip lines that look like decoded protobuf content
        if skip_mode:
            # These are characteristics of the decoded section
            if (line.startswith('message ') or 
                line.startswith('//') or 
                line.startswith('repeated ') or
                line == '}' or
                line.startswith('int32 ') or
                '{' in line):
                continue
            else:
                # Looks like a real header again, stop skipping
                skip_mode = False
        
        if not skip_mode:
            cleaned_lines.append(line)
    
    lines = cleaned_lines
    
    if len(lines) % 2 != 0:
        raise Exception(f"Invalid headers format. Each header name must have a corresponding value. Got {len(lines)} lines (should be even). Last line: '{lines[-1] if lines else 'none'}'")
    
    formatted_headers = []
    for i in range(0, len(lines), 2):
        header_name = lines[i]
        header_value = lines[i + 1]
        formatted_line = f"{header_name}: {header_value}"
        formatted_headers.append(formatted_line)
    
    return '\n'.join(formatted_headers)


def get_video_ids(ytmusic,tracks):
    video_ids = []
    missed_tracks = {
        "count": 0,
        "tracks": []
    }
    for track in tracks:
        try :
            search_string = f"{track['name']} {track['artists'][0]}"
            video_id = ytmusic.search(search_string, filter="songs")[0]["videoId"]
            video_ids.append(video_id)
        except :
            print(f"{track['name']} {track['artists'][0]} not found on YouTube Music")
            missed_tracks["count"] += 1
            missed_tracks["tracks"].append(f"{track['name']} {track['artists'][0]}")
    print(f"Found {len(video_ids)} songs on YouTube Music")
    if len(video_ids) == 0:
        raise Exception("No songs found on YouTube Music")
    return video_ids, missed_tracks


def create_ytm_playlist(playlist_link, headers):
    auth_path = None
    try:
        # ytmusicapi.setup writes a JSON file and YTMusic reads it during
        # construction. A fixed filename makes concurrent requests share
        # credentials, so allocate an exclusive per-request file instead.
        fd, auth_path = tempfile.mkstemp(
            prefix="spottransfer-auth-", suffix=".json"
        )
        os.close(fd)

        # Parse and format headers
        formatted_headers = parse_headers(headers)
        ytmusicapi.setup(filepath=auth_path, headers_raw=formatted_headers)
        ytmusic = YTMusic(auth_path)
    except Exception as e:
        raise Exception("Failed to setup YouTube Music API") from e
    finally:
        if auth_path:
            try:
                os.unlink(auth_path)
            except FileNotFoundError:
                pass

    tracks = get_all_tracks(playlist_link, "IN")
    name = get_playlist_name(playlist_link)
    video_ids, missed_tracks = get_video_ids(ytmusic, tracks)
    ytmusic.create_playlist(name, "", "PRIVATE", video_ids)
    print(f"Creating YouTube Music playlist: {name} with {len(video_ids)} songs")
    return missed_tracks

