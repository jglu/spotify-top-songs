# Spotify Monthly Top Songs Playlist

This project updates a specified Spotify playlist with a user's top 50 songs from the past month.

It supports two modes of operation:
1. **Interactive Web App**: A local Flask server that you can log into to update the playlist manually.
2. **Automated Script**: A standalone script that can be run periodically (e.g., via cron) to update the playlist automatically without user interaction.

## Prerequisites

1. **Spotify Developer Account**:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) and create an app.
   - Note down the `Client ID` and `Client Secret`.
   - In the app settings, add `http://127.0.0.1:5000/auth/spotify/callback` to the **Redirect URIs**.

2. **Python Installed**: ensure you have Python 3 installed.

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jglu/spotify-top-songs.git
   cd spotify-top-songs
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   - Create a `.env` file in the root directory (you can copy `.env.template`).
   - Fill in the following variables:
     ```bash
     SPOTIFY_CLIENT_ID=your_spotify_client_id_here
     SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
     FLASK_SECRET_KEY=any_random_string_here
     SPOTIFY_PLAYLIST_ID=your_spotify_playlist_id_here
     ```
   
   **How to find your Playlist ID**:
   - Create a new playlist in Spotify (or use an existing one).
   - Right-click the playlist > **Share** > **Copy link to playlist**.
   - The ID is the part between `/playlist/` and `?`.
     - Example: `https://open.spotify.com/playlist/3cEYpjA9oz9GiPac4AsH4n?si=...` -> ID is `3cEYpjA9oz9GiPac4AsH4n`.
     - **Note**: The playlist must be owned by you or editable by you.

## How to Run

### Option 1: Interactive Mode (manual updating)

This starts a local web server to handle authentication and update the playlist.

1. Run the application:
   ```bash
   python api.py
   ```
2. Open your browser and go to `http://127.0.0.1:5000`.
3. Click "Login with Spotify".
4. After logging in, the script will update your playlist and display "done!".
5. **Important**: Check your terminal output. The script will print your **Refresh Token**. Copy this refresh token if you want to use the automated script (Option 2).

### Option 2: Automated Mode (what you probably want)

This runs the update script directly using a refresh token, without starting a web server. Scheduled to run daily at 6:00 AM UTC via the included GitHub Actions workflow.

1. Ensure you have obtained your `SPOTIFY_REFRESH_TOKEN` using Option 1.
2. Add the environment variables to your cloned repository.

   - In Settings > Secrets and variables > Actions, click "New repository secret".
   - Add four repository secrets: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_PLAYLIST_ID`, `SPOTIFY_REFRESH_TOKEN`
   - Option 2 no longer requires `FLASK_SECRET_KEY`.

3. That's it! The workflow will now run automatically on schedule.

## Notes

- The script deletes all existing tracks in the target playlist and replaces them with your current top 50 songs.
- Spotify's API limits batch deletion to 100 songs, but since top tracks are limited to 50, this is handled automatically.
- The playlist description is updated with the last update date.
- Automated script runs at 6:00 AM UTC. Time can be changed in [daily_update.yaml](./.github/workflows/daily_update.yaml).

## What I Learned

- Implementing complete OAuth 2.0 flow with Spotify.
- Managing environment variables and secrets in GitHub Actions.

## License

[MIT](LICENSE)