from collections import defaultdict, deque
from math import ceil
import logging
import threading
import time

from flask import Flask, request
from flask_cors import CORS
from ytm import create_ytm_playlist
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# The endpoint accepts only a playlist URL and a browser-header dump. A 1 MiB
# limit leaves ample room for real browser headers while preventing Werkzeug
# from buffering attacker-controlled multi-gigabyte bodies in memory.
app.config["MAX_CONTENT_LENGTH"] = int(
    os.getenv("MAX_CONTENT_LENGTH", 1 * 1024 * 1024)
)

MAX_AUTH_HEADERS_LENGTH = int(
    os.getenv("MAX_AUTH_HEADERS_LENGTH", 256 * 1024)
)
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 30))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 10))

logger = logging.getLogger(__name__)
_rate_limit_lock = threading.Lock()
_request_times = defaultdict(deque)

CORS(app, resources={
    r"/*" : {
        "origins": [os.getenv('FRONTEND_URL', 'http://localhost:5173')],
        "methods" : ["POST", "GET"],
        
    }
})


@app.before_request
def limit_create_requests():
    """Apply a small per-client guard before any expensive work starts.

    The reverse proxy should enforce the same policy globally. This in-process
    limit still protects direct Flask/Gunicorn deployments and each worker
    process from a basic anonymous request flood.
    """
    if request.endpoint != "create_playlist":
        return None

    client = request.remote_addr or "unknown"
    now = time.monotonic()

    with _rate_limit_lock:
        timestamps = _request_times[client]
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
            retry_after = max(
                1, ceil(RATE_LIMIT_WINDOW_SECONDS - (now - timestamps[0]))
            )
            return {
                "message": "Too many transfer requests. Please try again later."
            }, 429, {"Retry-After": str(retry_after)}

        timestamps.append(now)

    return None


@app.errorhandler(413)
def request_too_large(_error):
    return {"message": "Request body is too large."}, 413


@app.route('/create', methods=['POST'])
def create_playlist():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"message": "Request must contain a JSON object."}, 400

    playlist_link = data.get('playlist_link')
    auth_headers = data.get('auth_headers')
    if not isinstance(playlist_link, str) or not playlist_link.strip():
        return {"message": "A Spotify playlist URL is required."}, 400
    if not isinstance(auth_headers, str) or not auth_headers.strip():
        return {"message": "YouTube Music headers are required."}, 400
    if len(auth_headers.encode("utf-8")) > MAX_AUTH_HEADERS_LENGTH:
        return {"message": "YouTube Music headers are too large."}, 413

    try:
        missed_tracks = create_ytm_playlist(playlist_link, auth_headers)
        return {"message": "Playlist created successfully!",
                "missed_tracks": missed_tracks
        }, 200
    except Exception as error:
        # Do not reflect authentication, cookie, or upstream details to an
        # anonymous caller. Those messages can become a credential-race oracle.
        logger.warning("Playlist transfer failed: %s", type(error).__name__)
        return {"message": "Playlist transfer failed. Please try again later."}, 500
    
@app.route('/', methods=['GET'])
def home():
    # Render health check endpoint
    return {"message": "Server Online"}, 200

if __name__ == '__main__':
    app.run(port=8080)
