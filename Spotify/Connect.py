from dotenv import load_dotenv, find_dotenv, set_key
import os
import base64
import requests
import json
import time
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import logging
from Spotify.PlaylistBuilder.PlaylistAlgo import PlaylistAlgo

# Load environment variables from .env file
env_path = find_dotenv()
load_dotenv(env_path)

class SpotifyConnect:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = "http://localhost:3000/callback"
        self.access_token = os.getenv('SPOTIPY_ACCESS_TOKEN')
        self.refresh_token = os.getenv('SPOTIPY_REFRESH_TOKEN')
        self.playlist_uri = os.getenv('SPOTIFY_PLAYLIST')
        self.default_device_id = os.getenv('SPOTIFY_DEVICE_ID')
        self.auth_code = None
        self.algo_thread = None
        self.algo_running = False
        self.token_expiration_time = 0

    def ensure_valid_token(self):
        if time.time() > self.token_expiration_time:
            logging.info("Access token expired or about to expire. Refreshing access token...")
            if not self.refresh_token:
                raise Exception("Refresh token not available. Reauthenticate the application.")
            self.refresh_access_token()

    def refresh_access_token(self):
        auth_string = self.client_id + ':' + self.client_secret
        auth_base64 = str(base64.b64encode(auth_string.encode('utf-8')), 'utf-8')
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code != 200:
            logging.error(f"Failed to refresh token: {response.content}")
            raise Exception("Could not refresh the access token")
        
        json_result = response.json()
        self.access_token = json_result.get("access_token")
        self.token_expiration_time = time.time() + json_result.get("expires_in", 3600) - 60  # Refresh 1 minute before expiration
        self.save_access_token(self.access_token)

    def get_auth_header(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_auth_url(self):
        auth_url = "https://accounts.spotify.com/authorize"
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": (
                "user-read-playback-state user-modify-playback-state user-read-private "
                "user-library-read user-read-currently-playing user-read-recently-played "
                "playlist-read-private playlist-modify-public playlist-modify-private "
                "user-top-read user-follow-read user-follow-modify"
            ),
        }
        url = f"{auth_url}?{urlencode(params)}"
        return url

    def get_spotify_token(self, auth_code):
        auth_string = self.client_id + ':' + self.client_secret
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')

        url = 'https://accounts.spotify.com/api/token'
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri
        }

        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            logging.error(f"Failed to get token: {response.content}")
            raise Exception("Could not get the access token")

        json_result = response.json()
        self.access_token = json_result.get("access_token")
        self.refresh_token = json_result.get("refresh_token")
        self.token_expiration_time = time.time() + json_result.get("expires_in", 3600) - 60  # Refresh 1 minute before expiration
        self.save_access_token(self.access_token)
        self.save_refresh_token(self.refresh_token)

    def run_server(self):
        class SpotifyAuthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                query_components = parse_qs(urlparse(self.path).query)
                if 'code' in query_components:
                    auth_code = query_components['code'][0]
                    self.server.auth_code = auth_code
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"Authorization successful. You can close this window.")
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"Authorization failed. No code provided.")

        server_address = ('', 3000)
        httpd = HTTPServer(server_address, SpotifyAuthHandler)
        logging.info("Starting server on port 3000...")
        httpd.handle_request()  # Handle a single request and then stop

        if hasattr(httpd, 'auth_code'):
            self.get_spotify_token(httpd.auth_code)
        else:
            raise Exception("Authorization failed. No code received.")

    def authorize(self):
        auth_url = self.get_auth_url()
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(auth_url)

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(os.getenv('SPOTIFY_USERNAME'))
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(os.getenv('SPOTIFY_PASSWORD'))
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login-button"))).click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "auth-accept"))).click()
        except Exception as e:
            logging.error(f"Authorization failed: {e}")
        finally:
            driver.quit()

    def save_access_token(self, token):
        set_key(env_path, "SPOTIPY_ACCESS_TOKEN", token)

    def save_refresh_token(self, token):
        set_key(env_path, "SPOTIPY_REFRESH_TOKEN", token)

    def get_user_profile(self):
        url = "https://api.spotify.com/v1/me"
        headers = self.get_auth_header()
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception("Invalid access token")
        return response.json()

    def get_current_track(self):
        self.ensure_valid_token()
        url = "https://api.spotify.com/v1/me/player/currently-playing"
        headers = self.get_auth_header()
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and response.json():
            data = response.json()
            if data['is_playing']:
                current_track = data['item']
                current_position = data['progress_ms']
                return current_track, current_position
        return None, None

    def get_track_genre(self, track_id):
        self.ensure_valid_token()
        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        headers = self.get_auth_header()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            artist_id = data['artists'][0]['id']
            artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
            artist_response = requests.get(artist_url, headers=headers)
            if artist_response.status_code == 200:
                artist_data = artist_response.json()
                genres = artist_data.get('genres', [])
                logging.info(f"Genres for track {track_id}: {genres}")
                return genres
        logging.warning(f"Failed to get genres for track {track_id}")
        return []

    def get_active_device(self):
        url = "https://api.spotify.com/v1/me/player/devices"
        headers = self.get_auth_header()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            devices = response.json().get('devices', [])
            for device in devices:
                if device.get('is_active'):
                    return device.get('id')
        return None

    def activate_device(self, device_id):
        url = "https://api.spotify.com/v1/me/player"
        headers = self.get_auth_header()
        data = json.dumps({"device_ids": [device_id], "play": False})
        response = requests.put(url, headers=headers, data=data)
        if response.status_code != 204:
            raise Exception(f"Failed to activate device: {response.content}")

    def play_music(self):
        self.ensure_valid_token()
        url = "https://api.spotify.com/v1/me/player/play"
        headers = self.get_auth_header()
        device_id = self.get_active_device()
        
        if not device_id:
            logging.warning("No active device found. Using default device.")
            device_id = self.default_device_id
            self.activate_device(device_id)
            device_id = self.get_active_device()
            if not device_id:
                raise Exception("Failed to activate default device.")
    
        logging.info(f"Using device ID: {device_id}")
        
        response = requests.put(url, headers=headers)
        print("Response: ", response.status_code)
        if response.status_code != 204 and response.status_code != 202 and response.status_code != 200:
            logging.error(f"Failed to play music: {response.content}")
            return False, "Failed to play music"
        
        # Get the current track after playing music
        current_track, _ = self.get_current_track()
        if current_track:
            track_name = current_track['name']
            artist_name = current_track['artists'][0]['name']
            return True, f"{track_name} by {artist_name}"
        return True, "Unknown track"
    
    def skip_song(self):
        self.ensure_valid_token()
        url = "https://api.spotify.com/v1/me/player/next"
        headers = self.get_auth_header()
        response = requests.post(url, headers=headers)
        if response.status_code != 204:
            logging.error(f"Failed to skip song: {response.content}")
            return False
        return True

    def pause_song(self):
        self.ensure_valid_token()
        url = "https://api.spotify.com/v1/me/player/pause"
        headers = self.get_auth_header()
        response = requests.put(url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to pause music: {response.content}")
            return False
        return True

    def adjust_volume(self, change):
        self.ensure_valid_token()
        current_volume_url = "https://api.spotify.com/v1/me/player"
        headers = self.get_auth_header()
        
        # Get the current volume
        response = requests.get(current_volume_url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to get current volume: {response.content}")
            return False
        
        current_volume = response.json().get('device', {}).get('volume_percent')
        if current_volume is None:
            logging.error("Current volume not found")
            return False
        
        # Calculate the new volume
        new_volume = max(0, min(100, current_volume + change))
        
        # Set the new volume
        volume_url = "https://api.spotify.com/v1/me/player/volume"
        response = requests.put(volume_url, headers=headers, params={"volume_percent": new_volume})
        if response.status_code != 204:
            logging.error(f"Failed to adjust volume: {response.content}")
            return False
        return True
    
    def play_playlist(self, playlist_name):
        self.ensure_valid_token()
        url = "https://api.spotify.com/v1/me/player/play"
        headers = self.get_auth_header()
        device_id = self.get_active_device()
        
        if not device_id:
            logging.warning("No active device found. Using default device.")
            device_id = self.default_device_id
            self.activate_device(device_id)
            device_id = self.get_active_device()
            if not device_id:
                raise Exception("Failed to activate default device.")

        logging.info(f"Using device ID: {device_id}")
        
        # Retrieve the user's playlists
        playlists_url = "https://api.spotify.com/v1/me/playlists"
        playlists_response = requests.get(playlists_url, headers=headers)
        if playlists_response.status_code == 200:
            playlists_data = playlists_response.json()
            logging.info(f"Retrieved playlists: {playlists_data}")
            for playlist in playlists_data['items']:
                logging.info(f"Checking playlist: {playlist['name']}")
                if playlist_name.lower() in playlist['name'].lower():
                    playlist_uri = playlist['uri']
                    data = json.dumps({
                        "context_uri": playlist_uri,
                        "device_id": device_id
                    })
                    response = requests.put(url, headers=headers, data=data)
                    if response.status_code == 403:
                        logging.error("403 Forbidden: Regrabbing access token and retrying...")
                        self.refresh_access_token()
                        headers = self.get_auth_header()
                        response = requests.put(url, headers=headers, data=data)
                    if response.status_code != 204:
                        logging.error(f"Failed to play playlist: {response.content}")
                        raise Exception(f"Failed to play playlist: {response.content}")
                    logging.info(f"Playing playlist: {playlist_name}")
                    return True
            logging.error(f"Playlist '{playlist_name}' not found.")
            raise Exception(f"Failed to find playlist: {playlist_name}")
        else:
            logging.error(f"Failed to retrieve playlists: {playlists_response.content}")
            raise Exception(f"Failed to get playlists: {playlists_response.content}")


    def list_playlists(self):
        self.ensure_valid_token()
        url = "https://api.spotify.com/v1/me/playlists"
        headers = self.get_auth_header()
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get playlists: {response.content}")

        playlists = response.json().get('items')
        if not playlists:
            raise Exception("No playlists found")
        
        return playlists

    def request_song(self, song_name):
        self.ensure_valid_token()
        url = f"https://api.spotify.com/v1/search?q={song_name}&type=track&limit=5"
        headers = self.get_auth_header()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['tracks']['items']:
                track = data['tracks']['items'][0]
                track_uri = track['uri']
                device_id = self.get_active_device() or self.default_device_id
                logging.info(f"Using device ID: {device_id}")
                play_url = f"https://api.spotify.com/v1/me/player/play?device_id={device_id}"
                play_data = json.dumps({"uris": [track_uri]})
                play_response = requests.put(play_url, headers=headers, data=play_data)
                if play_response.status_code != 204:
                    raise Exception(f"Failed to play song: {play_response.content}")
                return True
        return False

    def add_track_to_playlist(self, playlist_id, track_id):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = self.get_auth_header()
        data = {
            "uris": [f"spotify:track:{track_id}"]
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"Added track {track_id} to playlist {playlist_id}")

    def remove_track_from_playlist(self, playlist_id, track_id):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = self.get_auth_header()
        data = {
            "tracks": [{"uri": f"spotify:track:{track_id}"}]
        }
        response = requests.delete(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"Removed track {track_id} from playlist {playlist_id}")

    def extract_playlist_id(self, playlist_uri):
        if 'spotify:playlist:' in playlist_uri:
            return playlist_uri.split(':')[-1]
        elif 'open.spotify.com/playlist/' in playlist_uri:
            return playlist_uri.split('/')[-1].split('?')[0]
        else:
            raise ValueError("Invalid playlist URI")

    def run_playlist_algo(self):
        playlist_id = self.extract_playlist_id(self.playlist_uri)
        algo = PlaylistAlgo(playlist_id)
        current_track_id = None

        while self.algo_running:
            current_track, current_position = self.get_current_track()
            if current_track:
                if current_track_id != current_track['id']:  # Only fetch attributes if the track changes
                    current_track_id = current_track['id']
                    attributes = self.get_track_attributes(current_track_id)
                    logging.info(f"Attributes for current track: {attributes}")
                    result = algo.manage_playlist(current_track, current_position, attributes)

                    if result == 'add':
                        self.add_track_to_playlist(playlist_id, current_track_id)
                    elif result == 'remove':
                        self.remove_track_from_playlist(playlist_id, current_track_id)

            time.sleep(10)  # Wait 10 seconds before checking again

    def start_playlist_algo(self):
        if not self.algo_running:
            self.algo_running = True
            self.algo_thread = threading.Thread(target=self.run_playlist_algo)
            self.algo_thread.start()
            print("Playlist algorithm started.")

    def stop_playlist_algo(self):
        if self.algo_running:
            self.algo_running = False
            if self.algo_thread:
                self.algo_thread.join()
            print("Playlist algorithm stopped.")