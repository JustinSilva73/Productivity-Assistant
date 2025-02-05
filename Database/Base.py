import pymysql
from contextlib import contextmanager
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))  # Default MySQL port
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Debug logging to verify environment variables
logging.basicConfig(level=logging.DEBUG)

class Database:
    def __init__(self):
        self.connection = None

    @contextmanager
    def open_database(self):
        """
        Context manager to open and close the database connection.
        """
        try:
            self.connection = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            yield self.connection
        except pymysql.MySQLError as e:
            logging.error(f"MySQL Error: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def close_database(self):
        """
        Close the database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None