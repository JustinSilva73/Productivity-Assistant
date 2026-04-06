import sys
import os
import threading

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from VoiceListen.Microphone import Microphone

def print_transcriptions(mic):
    while True:
        transcription = mic.transcription_queue.get()
        print(f"Transcription: {transcription}")

if __name__ == "__main__":
    mic = Microphone()

    # Start the listen method in a separate thread
    threading.Thread(target=mic.listen, daemon=True).start()

    # Start a thread to print transcriptions
    threading.Thread(target=print_transcriptions, args=(mic,), daemon=True).start()

    # Keep the main thread alive
    while True:
        pass