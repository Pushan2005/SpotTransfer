from flask import Flask, request
from flask_cors import CORS
from ytm import create_ytm_playlist
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*" : {
        "origins": [os.getenv('FRONTEND_URL', 'http://localhost:5173')],
        "methods" : ["POST", "GET"],
        
    }
})


@app.route('/create', methods=['POST'])
def create_playlist():
    data = request.get_json()
    playlist_link = data.get('playlist_link')
    auth_headers = data.get('auth_headers')
    
    try:
        missed_tracks = create_ytm_playlist(playlist_link, auth_headers)
        return {"message": "Playlist created successfully!",
                "missed_tracks": missed_tracks
        }, 200
    except Exception as e:
        return {"message": str(e)}, 500
    
@app.route('/', methods=['GET'])
def home():
    # Render health check endpoint
    return {"message": "Server Online"}, 200

if __name__ == '__main__':
    app.run(port=8080)