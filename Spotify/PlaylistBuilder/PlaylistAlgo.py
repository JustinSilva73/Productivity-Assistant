import time
from Database.Base import Database  # Assuming you have a Database class for handling connections

class PlaylistAlgo:
    def __init__(self, playlist_id):
        self.playlist_id = playlist_id
        self.db = Database()  # Initialize your database connection
        self.create_table()
        self.previous_track_id = None
        self.previous_position = 0

    def create_table(self):
        with self.db.open_database() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS track_stats (
                    track_id VARCHAR(255) PRIMARY KEY,
                    skipped INT,
                    listened_fully INT,
                    requested INT,
                    genre VARCHAR(255),
                    popularity INT,
                    tempo FLOAT,
                    `key` INT,
                    danceability FLOAT,
                    energy FLOAT,
                    valence FLOAT,
                    acousticness FLOAT,
                    instrumentalness FLOAT,
                    liveness FLOAT,
                    speechiness FLOAT,
                    artist VARCHAR(255),
                    length INT
                )
            ''')
            conn.commit()

    def update_track_stats(self, track_id, action, attributes):
        with self.db.open_database() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM track_stats WHERE track_id = %s', (track_id,))
            row = cursor.fetchone()
            if row is None:
                cursor.execute('''
                    INSERT INTO track_stats (track_id, skipped, listened_fully, requested, genre, popularity, tempo, `key`, danceability, energy, valence, acousticness, instrumentalness, liveness, speechiness, artist, length)
                    VALUES (%s, 0, 0, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    track_id,
                    attributes.get('genre', 'Unknown'),
                    attributes.get('popularity', 0),
                    attributes.get('tempo', 0),
                    attributes.get('key', 0),
                    attributes.get('danceability', 0),
                    attributes.get('energy', 0),
                    attributes.get('valence', 0),
                    attributes.get('acousticness', 0),
                    attributes.get('instrumentalness', 0),
                    attributes.get('liveness', 0),
                    attributes.get('speechiness', 0),
                    attributes.get('artist', ''),
                    attributes.get('length', 0)
                ))
            if action == 'skipped':
                cursor.execute('UPDATE track_stats SET skipped = skipped + 1 WHERE track_id = %s', (track_id,))
            elif action == 'listened_fully':
                cursor.execute('UPDATE track_stats SET listened_fully = listened_fully + 1 WHERE track_id = %s', (track_id,))
            elif action == 'requested':
                cursor.execute('UPDATE track_stats SET requested = requested + 1 WHERE track_id = %s', (track_id,))
            conn.commit()


    def manage_playlist(self, current_track, current_position, attributes):
        track_id = current_track['id']
        duration = current_track['duration_ms']

        if self.previous_track_id and self.previous_track_id != track_id:
            # Check if the previous track was skipped
            if self.previous_position < duration - 10000:  # Consider it skipped if less than 10 seconds remaining
                self.update_track_stats(self.previous_track_id, 'skipped', attributes)
            else:
                self.update_track_stats(self.previous_track_id, 'listened_fully', attributes)

        self.previous_track_id = track_id
        self.previous_position = current_position

        with self.db.open_database() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM track_stats WHERE track_id = %s', (track_id,))
            row = cursor.fetchone()
            if row is None:
                cursor.execute('''
                    INSERT INTO track_stats (track_id, skipped, listened_fully, requested, genre, popularity, tempo, `key`, danceability, energy, valence, acousticness, instrumentalness, liveness, speechiness, artist, length)
                    VALUES (%s, 0, 0, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    track_id,
                    attributes.get('genre', 'Unknown'),
                    attributes.get('popularity', 0),
                    attributes.get('tempo', 0),
                    attributes.get('key', 0),
                    attributes.get('danceability', 0),
                    attributes.get('energy', 0),
                    attributes.get('valence', 0),
                    attributes.get('acousticness', 0),
                    attributes.get('instrumentalness', 0),
                    attributes.get('liveness', 0),
                    attributes.get('speechiness', 0),
                    attributes.get('artist', ''),
                    attributes.get('length', 0)
                ))
                conn.commit()
                return 'add'
            else:
                skipped, listened_fully, requested, genre, popularity, tempo, key, danceability, energy, valence, acousticness, instrumentalness, liveness, speechiness, artist, length = row[1:]
                # Example logic to remove a track if skipped more than 3 times
                if skipped > 3:
                    return 'remove'
                # Example logic to add a track if listened to fully more than 5 times
                if listened_fully > 5:
                    return 'add'
        return 'none'


    def add_track_to_playlist(self, track_id):
        # Placeholder for adding a track to the playlist
        pass

    def remove_track_from_playlist(self, track_id):
        # Placeholder for removing a track from the playlist
        pass