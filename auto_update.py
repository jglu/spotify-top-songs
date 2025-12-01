import os
import requests
from datetime import datetime
from dotenv import load_dotenv

from api import (
    get_existing_URIs,
    delete_existing_songs,
    get_new_URIs,
    add_new_songs,
    update_playlist_description
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

    existing_URIs = get_existing_URIs(PLAYLIST_ID, token)
    delete_existing_songs(PLAYLIST_ID, existing_URIs, token)
    new_URIs = get_new_URIs(token)
    add_new_songs(PLAYLIST_ID, new_URIs, token)
    update_playlist_description(PLAYLIST_ID, token)

    print("Playlist updated!")

if __name__ == "__main__":
    auto_update_playlist()