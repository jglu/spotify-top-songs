from flask import Flask, redirect, request, session

import requests
import urllib.parse
from datetime import datetime
import secrets
from dotenv import load_dotenv
import os
import re

app = Flask(__name__)

load_dotenv()  # loads variables from .env file
app.secret_key = os.getenv('FLASK_SECRET_KEY')
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

REDIRECT_URI = 'http://127.0.0.1:5000/auth/spotify/callback' # for testing

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1'

TOP_SONGS_COUNT = 50 # update the top n=50 songs

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
        raise Exception({"error": request.args['error']})
    
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
        res.raise_for_status()
        token_info = res.json()

        # store in session
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        
        # print("access token:", session['access_token']) # testing
        print("refresh token:", session['refresh_token']) # testing
        
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
        res.raise_for_status()
        token_info = res.json()

        # store again
        session['access_token'] = token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']
        return redirect('/update-playlist')

## ---

def run_playlist_update(playlist_id, token) -> None:
    """
    Main entrance for updating top 50 songs playlist.
    """
    # get top track uris
    new_uris = get_my_top_tracks_uris(token)
    
    # sync playlist (remove songs that are not in the top 50, and add the new songs that are now in the top 50)
    snapshot_id = get_playlist_snapshot_id(playlist_id, token)
    synced_uris, snapshot_id = sync_playlist(new_uris, playlist_id, token, snapshot_id)
    
    # reorder the songs around
    _ = reorder_items(synced_uris, new_uris, playlist_id, token, snapshot_id)
    
    # update playlist description to show last updated date
    update_playlist_description(playlist_id, token)
    return

@app.route('/update-playlist')
def update_playlist():
    # this is the playlist that we are updating
    playlist_id = os.getenv('SPOTIFY_PLAYLIST_ID')
    
    # before anything, ensure that access_token exists and is not expired.
    ensure_valid_access_token()
    token = session['access_token']
    
    run_playlist_update(playlist_id, token)
    
    return "done!"


def get_playlist_snapshot_id(playlist_id, token):
    """
    Given a playlist id, return its current snapshot id.
    """
    
    headers = {
        'Authorization': f"Bearer {token}",
    }
    
    url = f"{API_BASE_URL}/playlists/{playlist_id}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    
    snapshot_id = res.json()["snapshot_id"]
    return snapshot_id
    
    
# ensure unexpired access token
def ensure_valid_access_token():
    if 'access_token' not in session:
        return redirect('/auth/spotify/login')
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/auth/spotify/refresh-token')
    return


# gets existing URIs in a playlist
def get_existing_uris(playlist_id, token):
    headers = {
        'Authorization': f"Bearer {token}"
    }
    
    url = f"{API_BASE_URL}/playlists/{playlist_id}/items?fields=items%28track%28uri%29%29&limit={TOP_SONGS_COUNT}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    
    # format in the way that needs to be passed in for deleting
    track_uris = []
    for item in res.json()["items"]:
        track_uris.append(item['track']['uri'])
    return track_uris


def delete_items_from_playlist(playlist_id, item_uris, token, curr_snapshot_id):
    """
    Delete items from a playlist.
    """
    
    if not item_uris:
        return
    
    items_uri_formatted = [{"uri": uri} for uri in item_uris]
    
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json'
    }
    body = {
        'items': items_uri_formatted,
        'snapshot_id': curr_snapshot_id
    }
    
    url = f"{API_BASE_URL}/playlists/{playlist_id}/items"
    res = requests.delete(url, headers=headers, json=body)
    res.raise_for_status()
    
    new_snapshot_id = get_playlist_snapshot_id(playlist_id, token)
    return new_snapshot_id

def get_my_top_tracks_uris(token):
    headers = {
        'Authorization': f"Bearer {token}"
    }
    url = f"{API_BASE_URL}/me/top/tracks?time_range=short_term&limit={TOP_SONGS_COUNT}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    
    # don't format into a comma-separated string of uris bc there are too many
    track_uris = []
    for item in res.json()['items']:
        track_uris.append(item['uri'])
    return track_uris


def add_items_to_playlist(playlist_id, item_uris, token, curr_snapshot_id):
    """
    Add items to a playlist.
    """
    
    if not item_uris:
        return
    
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json'
    }
    body = {
        'uris': item_uris,
        'snapshot_id': curr_snapshot_id
    }
    
    url = API_BASE_URL + "/playlists/" +  playlist_id + "/items"
    res = requests.post(url, headers=headers, json=body)
    res.raise_for_status()
    
    new_snapshot_id = get_playlist_snapshot_id(playlist_id, token)
    return new_snapshot_id

def update_playlist_description(playlist_id, token):
    """
    Updates playlist description to show last updated date. 
    Keeps the existing description, overwriting any previous '[last updated: ...]'.
    Month is lowercase.
    """
    
    # 1. get current existing playlist description (current_description)
    # gets existing description and updates that instead of hardcoding the description in .env
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json'
    }
    url = f"{API_BASE_URL}/playlists/{playlist_id}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    
    data = res.json()
    current_description = data.get("description", "")
    
    # remove "[last updated: ...]" suffix
    current_description = re.sub(r"\s*\[last updated: .*?\]$", "", current_description).strip()
    
    # 2. get new formatted date to use in new_description
    now = datetime.now()
    month = now.strftime('%B').lower()
    day_suffix = "th" if 11 <= now.day % 100 <= 13 else {1:"st",2:"nd",3:"rd"}.get(now.day % 10, "th")
    now_str = f'{month} {now.day}{day_suffix}, {now.year}'
    
    new_description = f"{current_description} [last updated: {now_str}]"
    
    # 3. update playlist description with new_description
    body = {
        'description': new_description,
    }
    res = requests.put(url, headers=headers, json=body)
    res.raise_for_status()
    return
    
    
def sync_playlist(target_uris, playlist_id, token, snapshot_id):
    """
    Removes stale songs (songs that are no longer top), and adds new top songs that are missing
    """
    
    existing_uris = get_existing_uris(playlist_id, token)
    
    # get uris to delete or add
    uris_to_add = list(set(target_uris).difference(existing_uris))
    uris_to_delete = list(set(existing_uris).difference(target_uris))
    
    snapshot_id = delete_items_from_playlist(playlist_id, uris_to_delete, token, snapshot_id)
    snapshot_id = add_items_to_playlist(playlist_id, uris_to_add, token, snapshot_id)
    
    return get_existing_uris(playlist_id, token), snapshot_id
    

def reorder_items(existing_uris, new_uris, playlist_id, token, snapshot_id):
    """
    Reorders the items in the playlist to correctly match the top 50 order.
    """
    
    curr_snapshot_id = snapshot_id
    
    # first get a list of reorder operations that transform existing_URIs into new_URIs
    existing_uris_copy = list(existing_uris)
    reorder_operations = []

    for i, target_uri in enumerate(new_uris):
        if existing_uris_copy[i] == target_uri:
            continue

        j = existing_uris_copy.index(target_uri)

        if j > i:
            insert_before = i
        else:
            insert_before = i + 1

        reorder_operations.append({
            "range_start": j,
            "insert_before": insert_before,
            "range_length": 1
        })

        item = existing_uris_copy.pop(j)
        existing_uris_copy.insert(insert_before, item)

    # with reorder_operations, call the reorder endpoint
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json'
    }
    url = f"{API_BASE_URL}/playlists/{playlist_id}/items"
    
    for reorder_operation in reorder_operations:
        # add snapshot_id to force correct order
        reorder_operation["snapshot_id"] = curr_snapshot_id
        res = requests.put(url, headers=headers,json=reorder_operation)
        res.raise_for_status()
        
        # get new snapshot_id
        curr_snapshot_id = res.json()["snapshot_id"]
    
    return curr_snapshot_id


if __name__ == '__main__':
    app.run(debug=True)