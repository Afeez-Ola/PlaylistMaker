import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def create_spotify_playlist(excel_file):
    # --- CONFIGURATION ---
    CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

    # Basic check to ensure .env is loaded
    if not CLIENT_ID:
        print("Error: Credentials not found. Please check your .env file.")
        return

    # Authenticate
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
    missing_songs = [] # List to store dictionaries of missing songs

    print(f"Processing {len(df)} songs...")
    
    for index, row in df.iterrows():
        song_name = str(row['Song Name'])
        # Handle cases where Artist might be empty/NaN
        artist_name = str(row['Artist']) if 'Artist' in df.columns and pd.notna(row['Artist']) else ""
        
        # Construct search query
        query = f"track:{song_name} artist:{artist_name}" if artist_name else f"track:{song_name}"
        
        # Search Spotify
        try:
            results = sp.search(q=query, type='track', limit=1)
            # Get the ID of the first result
            uri = results['tracks']['items'][0]['uri']
            track_uris.append(uri)
            print(f"Found: {song_name}")
            
        except (IndexError, TypeError):
            print(f"XXX Could not find: {song_name}")
            # Add to missing list with details
            missing_songs.append({
                "Song Name": song_name, 
                "Artist": artist_name
            })

    # --- HANDLE MISSING SONGS ---
    if missing_songs:
        print(f"\nSaving {len(missing_songs)} missing songs to 'songs_not_found.xlsx'...")
        df_missing = pd.DataFrame(missing_songs)
        df_missing.to_excel("songs_not_found.xlsx", index=False)
    else:
        print("\nPerfect run! All songs were found.")

    if not track_uris:
        print("No songs found at all. Exiting.")
        return

    # --- CREATE PLAYLIST ---
    user_id = sp.current_user()['id']
    playlist_name = "Imported From Excel"
    
    print(f"\nCreating playlist '{playlist_name}'...")
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
    playlist_id = playlist['id']

    # --- ADD SONGS (Batching) ---
    print("Adding songs to playlist...")
    
    def chunk_list(data, size):
        for i in range(0, len(data), size):
            yield data[i:i + size]

    for batch in chunk_list(track_uris, 100):
        sp.playlist_add_items(playlist_id, batch)

    print("\n------------------------------------------------")
    print(f"Success! Playlist '{playlist_name}' created.")
    print(f"Added {len(track_uris)} songs.")
    if missing_songs:
        print(f"Check 'songs_not_found.xlsx' for the {len(missing_songs)} tracks that failed.")

# Run the function
if __name__ == "__main__":
    create_spotify_playlist("songs.xlsx")