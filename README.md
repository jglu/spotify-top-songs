# Spotify Monthly Top Songs Playlist

This script updates a specified Spotify playlist with a user's top 50 songs from the past month.

- The targeted playlist should have **at most 100 songs**, since Spotify's API only allows deleting up to 100 songs at a time.
- Since the script uses exactly 50 top songs, this limitation is a non-issue.
  
## Setup and How to Run

1. Clone the repository  
2. Create a Spotify app at https://developer.spotify.com/dashboard/applications to get the Client ID (SPOTIFY_CLIENT_ID) and Client Secret (SPOTIFY_CLIENT_SECRET)  
3. In .env, set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
4. In .env, set any string as FLASK_SECRET_KEY
5. Install dependencies and run the script

   ```
   pip install -r requirements.txt
   python main.py
   ```