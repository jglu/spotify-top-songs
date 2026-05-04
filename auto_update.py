import os
import requests
from dotenv import load_dotenv

from api import (
    run_playlist_update
)

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")

TOKEN_URL = 'https://accounts.spotify.com/api/token'

def refresh_access_token():
    request_body = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    res = requests.post(TOKEN_URL, data=request_body)
    res.raise_for_status()
    return res.json()["access_token"]

# -----------

def auto_update_playlist():
    token = refresh_access_token()
    run_playlist_update(PLAYLIST_ID, token)
    print("Playlist updated!")

if __name__ == "__main__":
    auto_update_playlist()