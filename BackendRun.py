import threading
import time
import os
import asyncio
import json
from VoiceAssistant import VoiceAssistant
from VoiceListen.Microphone import Microphone
from OpenAI.Assistant import JarvisAssistant
from Spotify.Connect import SpotifyConnect
import azure.cognitiveservices.speech as speechsdk
import logging
from ToDo.ToDoList import ToDoList
from ToDo.DisplayList.DisplayList import TaskDisplay
import tkinter as tk

logging.basicConfig(filename='backend_run.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Suppress debug messages from specific libraries
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

# Initialize Azure Cognitive Services Speech SDK
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
speech_config.speech_synthesis_voice_name = 'en-GB-ThomasNeural'
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# Set volume and speed
volume = 1  # Volume percentage (0 to 100)
speed = 30  # Speed percentage (-100 to 100)

# Load phrases and functions from JSON file
with open('phrases.json', 'r') as f:
    phrases_to_functions = json.load(f)

# Initialize components
spotify = SpotifyConnect()
jarvis = JarvisAssistant()
mic = Microphone()
todo = ToDoList()
activation_word = "jarvis"  # Set your activation word here
voice_assistant = VoiceAssistant(spotify, jarvis, mic, phrases_to_functions, speech_synthesizer, speech_config, volume, speed, activation_word)

def gui_handler():
    while True:
        command = voice_assistant.gui_queue.get()
        logging.info(f"GUI handler received command: {command}")
        if command == "display_list":
            tasks = voice_assistant.todo_list.get_tasks()
            voice_assistant.task_display.update_tasks(tasks)
            voice_assistant.task_display.root.after(0, voice_assistant.task_display.root.deiconify)  # Show the GUI

async def main():
    mic.listen_in_background()

    # Start processing transcriptions
    await voice_assistant.process_transcriptions()

if __name__ == "__main__":
    try:
        logging.info("Starting BackendRun")

        # Initialize the TaskDisplay
        task_display = TaskDisplay(todo)
        voice_assistant.task_display = task_display

        # Start the GUI handler in a separate thread
        gui_thread = threading.Thread(target=gui_handler, daemon=True)
        gui_thread.start()

        # Start the main async function in a separate thread
        main_thread = threading.Thread(target=lambda: asyncio.run(main()), daemon=True)
        main_thread.start()

        # Run the Tkinter main loop in the main thread
        task_display.root.withdraw()  # Hide the GUI initially
        task_display.run()

        logging.info("BackendRun finished")
    except KeyboardInterrupt:
        logging.info("Exiting BackendRun")
        print("Exiting BackendRun")
        # Perform any necessary cleanup here
        gui_thread.join()
        main_thread.join()
        os._exit(0)  # Force exit the program
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")
        gui_thread.join()
        main_thread.join()
        os._exit(1)  # Exit the program with an error code