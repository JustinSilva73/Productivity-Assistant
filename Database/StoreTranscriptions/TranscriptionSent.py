from Database.Base import Database
import logging
from datetime import datetime

class TranscriptionStore:
    def __init__(self):
        self.db = Database()

    def store_transcription(self, user_transcript, response_transcript, gen_topic):
        try:
            with self.db.open_database() as conn:
                cursor = conn.cursor()
                now = datetime.now()
                date = now.date()
                time = now.time()
                dotw = now.strftime("%A")  # Day of the week

                query = """
                INSERT INTO convo (userTranscript, responseTranscript, date, time, dotw, genTopic)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (user_transcript, response_transcript, date, time, dotw, gen_topic))
                conn.commit()
                logging.info("Transcription stored successfully.")
        except Exception as e:
            logging.error(f"Failed to store transcription: {e}")
            raise