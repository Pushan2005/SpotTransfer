from flask import Flask, request
from flask_cors import CORS
from ytm import create_ytm_playlist
from header_parser import parse_headers, validate_required_headers
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*" : {
        "origins": [os.getenv('FRONTEND_URL')],
        "methods" : ["POST", "GET"],
        
    }
})


@app.route('/create', methods=['POST'])
def create_playlist():
    data = request.get_json()
    auth_headers = data.get('auth_headers')

    # Support both single playlist and multiple playlists
    playlist_link = data.get('playlist_link')
    playlist_links = data.get('playlist_links', [])

    if playlist_link and not playlist_links:
        playlist_links = [playlist_link]

    if not playlist_links:
        return {"message": "No playlist links provided"}, 400

    print(f"Received {len(playlist_links)} playlist(s)")

    try:
        parsed_headers = parse_headers(auth_headers)

        is_valid, missing = validate_required_headers(parsed_headers)
        if not is_valid:
            return {
                "message": f"Missing required headers: {', '.join(missing)}. Please make sure you're logged into YouTube Music and copy the headers from a valid request."
            }, 400

        auth_headers = parsed_headers
    except Exception as e:
        print(f"Error parsing headers: {e}")
        return {"message": f"Error parsing headers: {str(e)}"}, 400

    results = []
    failed_playlists = []

    for i, link in enumerate(playlist_links, 1):
        print(f"\n{'='*60}")
        print(f"Processing playlist {i}/{len(playlist_links)}: {link}")
        print(f"{'='*60}")
        try:
            result = create_ytm_playlist(link, auth_headers)
            results.append({
                "playlist_link": link,
                "playlist_name": result["playlist_name"],
                "status": "success",
                "missed_tracks": result["missed_tracks"]
            })
        except Exception as e:
            print(f"Error processing playlist {link}: {e}")
            failed_playlists.append({
                "playlist_link": link,
                "error": str(e)
            })
            results.append({
                "playlist_link": link,
                "status": "failed",
                "error": str(e)
            })

    success_count = len([r for r in results if r["status"] == "success"])

    return {
        "message": f"Processed {len(playlist_links)} playlist(s). {success_count} succeeded, {len(failed_playlists)} failed.",
        "total": len(playlist_links),
        "succeeded": success_count,
        "failed": len(failed_playlists),
        "results": results
    }, 200
    
@app.route('/', methods=['GET'])
def home():
    # Render health check endpoint
    return {"message": "Server Online"}, 200

if __name__ == '__main__':
    app.run(port=8080)