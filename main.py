from flask import Flask, redirect, request, jsonify, session

import requests
import urllib.parse
from datetime import datetime
import secrets
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()  # loads variables from .env file
app.secret_key = os.getenv('FLASK_SECRET_KEY')
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

REDIRECT_URI = 'http://127.0.0.1:5000/auth/spotify/callback' # for testing

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1'

@app.route('/')
def index():
    return "Update top 50 songs playlist <a href='/auth/spotify/login'>Login with Spotify</a>"

@app.route('/auth/spotify/login')
def login():
    state = secrets.token_urlsafe(32)
    session['state'] = state

    scope = 'user-top-read playlist-read-private playlist-modify-private playlist-modify-public'
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        # 'show_dialog': True, # true for testing
        'state': state
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/auth/spotify/callback')
def callback():
    # compare states
    request_state = request.args.get('state')
    if request_state != session.get('state'):
        return 403

    # error
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    # no error
    if 'code' in request.args:
        request_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }

        res = requests.post(TOKEN_URL, data=request_body)
        if res.status_code != 200:
            return jsonify({"error": f"Request failed with status {res.status_code}"}), res.status_code

        token_info = res.json()

        # store in session
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']
        return redirect('/update-playlist')
    
@app.route('/auth/spotify/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/auth/spotify/login')
    if datetime.now().timestamp() > session['expires_at']:
        request_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        res = requests.post(TOKEN_URL, data=request_body)
        token_info = res.json()

        # store again
        session['access_token'] = token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']
        return redirect('/update-playlist')

## ---

# this is the main function that will call other functions. 
# what do i need ?
@app.route('/update-playlist')
def update_playlist():
    # this is the playlist that we are updating
    playlist_id = os.getenv('SPOTIFY_PLAYLIST_ID')
    
    # before anything, ensure that access_token exists and is not expired.
    ensure_valid_access_token()
    
    # get all 50 URIs of the songs in a specific playlist
    #   ensure that the 50 URIs are in order from most to least listened; 
    #   will make it easier to change code later 
    existing_URIs = get_existing_URIs(playlist_id)
    
    # then delete the 50 tracks from them
    delete_existing_songs(playlist_id, existing_URIs)
    
    # now the playlist is empty.
    # get new 50 URIs of the top songs
    new_URIs = get_new_URIs()
    
    # and add these new 50 tracks from the uris
    add_new_songs(playlist_id, new_URIs)
    
    return "done!"

# 0. ensure unexpired access token
def ensure_valid_access_token():
    if 'access_token' not in session:
        return redirect('/auth/spotify/login')
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/auth/spotify/refresh-token')
    return


# 1. gets existing URIs of 50 tracks
def get_existing_URIs(playlist_id):
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    
    # tmp (sep 20 2025, 09/20/2025): abstract away the 50 track limit away later
    url = API_BASE_URL + "/playlists/" +  playlist_id + "/tracks?fields=items(track(uri))&limit=50"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return jsonify({"error": f"Request failed with status {res.status_code}"}), res.status_code
    
    # format in the way that needs to be passed in for deleting
    track_URIs = []
    for item in res.json()["items"]:
        track_URIs.append({"uri": item['track']['uri']})
    return track_URIs


# 2. delete all tracks in the playlist 
def delete_existing_songs(playlist_id, track_URIs):
    headers = {
        'Authorization': f"Bearer {session['access_token']}",
        'Content-Type': 'application/json'
    }
    body = {
        'tracks': track_URIs
    }
    
    url = API_BASE_URL + "/playlists/" +  playlist_id + "/tracks"
    res = requests.delete(url, headers=headers, json=body)
    if res.status_code != 200:
        return jsonify({"error": f"Request failed with status {res.status_code}"}), res.status_code
    return

# 3. get URIs for the short_term top tracks
def get_new_URIs():
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    url = API_BASE_URL + "/me/top/tracks?time_range=short_term&limit=50"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return jsonify({"error": f"Request failed with status {res.status_code}"}), res.status_code
    
    # don't format into a comma-separated string of uris bc there are too many
    track_URIs = []
    for item in res.json()['items']:
        track_URIs.append(item['uri'])
    return track_URIs

# 4. add tracks to playlist
def add_new_songs(playlist_id, track_URIs):
    headers = {
        'Authorization': f"Bearer {session['access_token']}",
        'Content-Type': 'application/json'
    }
    body = {
        'uris': track_URIs
    }
    url = API_BASE_URL + "/playlists/" +  playlist_id + "/tracks"
    res = requests.post(url, headers=headers, json=body)
    if res.status_code != 200:
        return jsonify({"error": f"Request failed with status {res.status_code}"}), res.status_code
    return

if __name__ == '__main__':
    app.run(debug=True)
    