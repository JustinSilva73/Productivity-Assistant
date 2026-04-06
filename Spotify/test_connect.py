import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Spotify API credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:3000/callback")

# Debugging lines to print the loaded environment variables
print("SPOTIFY_CLIENT_ID:", CLIENT_ID)
print("SPOTIFY_CLIENT_SECRET:", CLIENT_SECRET)
print("SPOTIFY_REDIRECT_URI:", REDIRECT_URI)

# Initialize Spotipy with SpotifyOAuth
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="user-read-private user-read-email user-read-playback-state user-modify-playback-state"
    )
)

class SpotifyConnect:
    def __init__(self):
        self.sp = sp

    def get_track_attributes(self, track_ids):
        """
        Fetches audio features for given track IDs using the user-level token.
        """
        try:
            audio_features = self.sp.audio_features(track_ids)
            return audio_features
        except Exception as e:
            logging.error(f"Error fetching track attributes: {e}")
            raise

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    spotify_connect = SpotifyConnect()

    # Replace with valid Spotify track IDs
    track_ids = ["11dFghVXANMlKmJXsNCbNl"]  # Example track IDs
    try:
        attributes = spotify_connect.get_track_attributes(track_ids)
        print("Track Attributes:")
        print(json.dumps(attributes, indent=2))
    except Exception as e:
        logging.error(f"Error: {e}")