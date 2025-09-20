# Spotify Monthly Top Songs Playlist

This script updates a specified Spotify playlist with a user's top 50 songs from the past month.

- The targeted playlist should have **at most 100 songs**, since Spotify's API only allows deleting up to 100 songs at a time.
- Since the script uses exactly 50 top songs, this limitation is a non-issue.
  
## Setup and How to Run

1. Clone the repository.  
2. Create a Spotify app at https://developer.spotify.com/dashboard/applications to get the Client ID (SPOTIFY_CLIENT_ID) and Client Secret (SPOTIFY_CLIENT_SECRET).
3. Create a .env file. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.
4. In .env, set a Flask secret key (can be any string) as FLASK_SECRET_KEY
5. In .env, set your SPOTIFY_PLAYLIST_ID. Each playlist has its own unique id. To find this,

   - Right click the playlist in Spotify
   - Select > Share > Copy link to playlist
   - From the URL, copy the part after `https://open.spotify.com/playlist/` and before any `?` or query string

   ```
   For example, in 

     https://open.spotify.com/playlist/3cEYpjA9oz9GiPac4AsH4n

   the id is 3cEYpjA9oz9GiPac4AsH4n.
   Set your SPOTIFY_PLAYLIST_ID to this id.
   ```
6. Install dependencies and run the script.

   ```
   pip install -r requirements.txt
   python main.py
   ```


## What I learned in this project

- my first time implementing OAuth 2.0 flow! 
- python's requests library functions are all synchronous. i've gotten too used to await/async "garb" in js.

## Next steps

1. move REDIRECT_URI to my personal website. it's currently set to localhost.
2. currently, this script deletes and re-adds songs. i'd like to have a comparison step that only removes songs if they are no longer in the user's top 50. this would allows users to see how long a song has *stayed* in their top 50.