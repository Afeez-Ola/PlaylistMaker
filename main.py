import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def create_spotify_playlist(excel_file):
    # --- CONFIGURATION ---
    # Replace these with your actual credentials from the Spotify Developer Dashboard
    CLIENT_ID = 'a9eea35b6f63478e8f6ba2232dc223ad'
    CLIENT_SECRET = 'c5096207ee114689bc0a3620f835676c'
    REDIRECT_URI = 'http://localhost:8888/callback'
    
    # Authenticate
    # Scope 'playlist-modify-public' allows us to create and add to playlists
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="playlist-modify-public"
    ))

    # --- READ DATA ---
    print(f"Reading {excel_file}...")
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        print("Error: File not found. Make sure songs.xlsx is in the same folder.")
        return

    # --- SEARCH FOR SONGS ---
    track_uris = []
    not_found = []

    print("Searching for songs on Spotify...")
    
    for index, row in df.iterrows():
        song_name = str(row['Song Name'])
        # If you have an Artist column, use it for better accuracy
        artist_name = str(row['Artist']) if 'Artist' in df.columns else ""
        
        # Construct search query
        query = f"track:{song_name} artist:{artist_name}" if artist_name else f"track:{song_name}"
        
        # Search Spotify
        results = sp.search(q=query, type='track', limit=1)
        
        try:
            # Get the ID of the first result
            uri = results['tracks']['items'][0]['uri']
            track_uris.append(uri)
            print(f"Found: {song_name}")
        except IndexError:
            print(f"XXX Could not find: {song_name}")
            not_found.append(song_name)

    if not track_uris:
        print("No songs found. Exiting.")
        return

    # --- CREATE PLAYLIST ---
    user_id = sp.current_user()['id']
    playlist_name = "Imported From Excel"
    
    print(f"Creating playlist '{playlist_name}'...")
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
    playlist_id = playlist['id']

    # --- ADD SONGS (Batching) ---
    # Spotify allows adding max 100 songs per request. We must batch them.
    print("Adding songs to playlist...")
    
    def chunk_list(data, size):
        for i in range(0, len(data), size):
            yield data[i:i + size]

    for batch in chunk_list(track_uris, 100):
        sp.playlist_add_items(playlist_id, batch)

    print("\n------------------------------------------------")
    print(f"Success! Playlist '{playlist_name}' created.")
    print(f"Added {len(track_uris)} songs.")
    if not_found:
        print(f"Songs not found: {len(not_found)}")
        print(not_found)

# Run the function
if __name__ == "__main__":
    create_spotify_playlist("songs.xlsx")