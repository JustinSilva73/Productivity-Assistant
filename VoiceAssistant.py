import asyncio 
import re
from fuzzywuzzy import fuzz
import azure.cognitiveservices.speech as speechsdk
import logging
from Database.StoreTranscriptions.TranscriptionSent import TranscriptionStore
from OpenAI.Assistant import JarvisAssistant
from ToDo.ToDoList import ToDoList
from ToDo.DisplayList.DisplayList import TaskDisplay
import json
from datetime import date
import threading
import queue
import datetime
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
# Set up logging to a file with timestamps
logging.basicConfig(filename='voice_assistant.log', level=logging.INFO, format='%(asctime)s %(message)s')

class ActivationManager:
    def __init__(self):
        self.active = False

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

class VoiceAssistant:
    def __init__(self, spotify, jarvis, mic, phrases_to_functions, speech_synthesizer, speech_config, volume, speed, activation_word="endeavor"):
        self.spotify = spotify
        self.jarvis = jarvis
        self.mic = mic
        self.phrases_to_functions = phrases_to_functions
        self.speech_synthesizer = speech_synthesizer
        self.speech_config = speech_config
        self.volume = volume
        self.speed = speed
        self.activation_manager = ActivationManager()
        self.activation_word = activation_word.lower()
        self.transcription_store = TranscriptionStore()
        self.todo_list = ToDoList()
        self.task_display = None  # This will be set in BackendRun.py
        self.phrase_to_function = self.create_phrase_to_function_mapping()
        self.pending_task = None
        self.bulk_add_mode = False
        self.transcription_count = 0
        self.gui_queue = queue.Queue()

    def create_phrase_to_function_mapping(self):
        phrase_to_function = {}
        for function_name, phrases in self.phrases_to_functions.items():
            for phrase in phrases:
                phrase_to_function[phrase] = function_name
        return phrase_to_function

    async def process_transcriptions(self):
        self.mic.start_recording()
        while True:
            transcription = await asyncio.to_thread(self.mic.transcription_queue.get)
            logging.info(f"Input Transcription: {transcription}")
            print(f"Input Transcription: {transcription}")

            # Check for activation word immediately.
            if self.activation_word in transcription.lower():
                self.handle_activation_trigger()

            response = self.handle_transcription(transcription)
            self.speak(response)


    def save_audio_transcription(self):
        self.transcription_count += 1
        audio_filename = f"transcription{self.transcription_count}.wav"
        self.mic.stop_recording()
        self.mic.save_audio(audio_filename)
        logging.info(f"Audio saved as {audio_filename}")
        self.mic.start_recording()

    def create_phrase_to_function_mapping(self):
        phrase_to_function = {}
        for function_name, phrases in self.phrases_to_functions.items():
            for phrase in phrases:
                phrase_to_function[phrase] = function_name
        return phrase_to_function

    async def process_transcriptions(self):
        self.mic.start_recording()
        while True:
            transcription = await asyncio.to_thread(self.mic.transcription_queue.get)
            logging.info(f"Input Transcription: {transcription}")
            print(f"Input Transcription: {transcription}")

            # Check for activation word immediately.
            if self.activation_word in transcription.lower():
                self.handle_activation_trigger()

            response = self.handle_transcription(transcription)
            self.speak(response)

    def handle_transcription(self, transcription):
        for phrase, function_name in self.phrase_to_function.items():
            if re.search(phrase, transcription, re.IGNORECASE):
                function = getattr(self, function_name, None)
                if function:
                    logging.info(f"Running function: {function_name}")
                    print(f"Running function: {function_name}")
                    return function(transcription)

        if "stop listening" in transcription.lower():
            self.deactivate_jarvis()
            return "Deactivating. I will stop listening now."

        return "Sorry, I didn't understand that."

    def deactivate_jarvis(self):
        self.activation_manager.deactivate()
        logging.info("Voice assistant deactivated.")
        print("Voice assistant deactivated.")

    def handle_bulk_add_mode(self, transcription):
        if "end bulk task" in transcription.lower():
            self.bulk_add_mode = False
            self.activation_manager.deactivate()
            return "Bulk task addition ended."
        else:
            self.todo_list.add_task(transcription)
            self.update_task_display()
            logging.info(f"Task '{transcription}' added in bulk mode.")
            return f"Task '{transcription}' added. Is there more tasks?"


    def handle_pending_task(self, transcription):
        if "yes" in transcription.lower() or "confirm" in transcription.lower():
            response = self.add_task(confirm=True)
            self.pending_task = None
        else:
            response = "Task addition cancelled."
            self.pending_task = None
        self.activation_manager.deactivate()
        return response


    def handle_function_execution(self, transcription):
        for phrase, function_name in self.phrase_to_function.items():
            if fuzz.partial_ratio(phrase, transcription.lower()) > 80:
                function = getattr(self, function_name, None)
                if function:
                    logging.info(f"Running function: {function_name}")
                    print(f"Running function: {function_name}")
                    if function_name == "bulk_add_tasks":
                        self.bulk_add_mode = True
                        self.activation_manager.activate()
                        return "Bulk task addition started. Please say your tasks one by one."
                    elif function_name == "add_task":
                        return self.add_task(transcription)
                    elif function_name == "remove_task":
                        return self.remove_task(transcription)
                    elif function_name == "list_tasks":
                        return self.list_tasks(transcription)
                    else:
                        return function(transcription) if "transcription" in function.__code__.co_varnames else function()
        logging.info("No specific function matched. Using Jarvis for default response.")
        print("No specific function matched. Using Jarvis for default response.")
        return self.jarvis_response(transcription)

    def play_music(self):
        self.spotify.play_music()

    def pause_music(self):
        self.spotify.pause_song()

    def skip_song(self):
        if self.spotify.skip_song():
            return "Skipped song successfully."
        else:
            return "Failed to skip song."

    def adjust_volume(self, change):
        self.spotify.adjust_volume(change)

    def increase_volume(self, transcription):
        change = self.extract_number(transcription)
        self.adjust_volume(change)

    def decrease_volume(self, transcription):
        change = -self.extract_number(transcription)
        self.adjust_volume(change)

    def extract_number(self, text):
        match = re.search(r'\d+', text)
        return int(match.group()) if match else 0

    def request_song(self, transcription):
        song_name = transcription.replace("endeavor play the song", "").strip()
        self.spotify.request_song(song_name)

    def list_playlists(self):
        return self.spotify.list_playlists()

    def play_playlist(self, transcription):
        # Extract the playlist name from the transcription
        with open('phrases.json', 'r') as f:
            phrases = json.load(f)
        
        for phrase in phrases.get("play_playlist", []):
            if phrase in transcription.lower():
                playlist_name = transcription.lower().split(phrase, 1)[1].split(" and", 1)[0].strip()
                return self.spotify.play_playlist(playlist_name)

    def parse_date(self, transcription):
        if "tomorrow" in transcription.lower():
            return datetime.date.today() + datetime.timedelta(days=1)
        date_match = re.search(r'on (\d{4}-\d{2}-\d{2})', transcription)
        if date_match:
            return datetime.datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
        return datetime.date.today()

    def add_task(self, transcription=None, confirm=False):
        if confirm:
            logging.info(f"Adding task: {self.pending_task}")
            self.todo_list.add_task(self.pending_task, self.pending_task_date)
            self.update_task_display()
            return f"Task '{self.pending_task}' added to your to-do list for {self.pending_task_date}."
        
        task_match = re.search(r'add task (.+?)( on \d{4}-\d{2}-\d{2}| tomorrow)?', transcription, re.IGNORECASE)
        if task_match:
            task = task_match.group(1).strip()
            self.pending_task = task
            self.pending_task_date = self.parse_date(transcription)
            logging.info(f"Pending task set: {task} for {self.pending_task_date}")
            return f"Task added will be '{task}' for {self.pending_task_date}. Confirm task?"
        return "No task found to add."

    def remove_task(self, transcription):
        task_match = re.search(r'remove tasks? (.+?)( on \d{4}-\d{2}-\d{2}| tomorrow)?', transcription, re.IGNORECASE)
        if task_match:
            task = task_match.group(1).strip()
            task_date = self.parse_date(transcription)
            if self.todo_list.remove_task(task, task_date):
                self.update_task_display()
                print(f"Task '{task}' removed from your to-do list for {task_date}.")
                return f"Task '{task}' removed from your to-do list for {task_date}."
            else:
                print(f"Task '{task}' not found in your to-do list for {task_date}.")
                return f"Task '{task}' not found in your to-do list for {task_date}."
        print("No task found to remove.")
        return "No task found to remove."


    def complete_task(self, transcription):
        task_match = re.search(r'complete task (.+?)( on \d{4}-\d{2}-\d{2}| tomorrow)?', transcription, re.IGNORECASE)
        if task_match:
            task = task_match.group(1).strip()
            task_date = self.parse_date(transcription)
            self.todo_list.complete_task(task, task_date)
            self.update_task_display()
            return f"Task '{task}' marked as completed for {task_date}."
        return "No task found to complete."

    def list_tasks(self, transcription=None):
        task_date = self.parse_date(transcription) if transcription else datetime.date.today()
        tasks = self.todo_list.get_tasks(task_date)
        task_list = "\n".join([f"{i+1}. {t['task']}" for i, t in enumerate(tasks)])
        self.gui_queue.put("display_list")
        logging.info("Added 'display_list' to GUI queue")
        logging.info(f"Task list for {task_date}: {task_list}")
        self.update_task_display(tasks)  # Update the GUI with the task list
        self.activation_manager.deactivate()  # Deactivate after listing tasks
        return f"Your to-do list for {task_date}:\n{task_list}" if tasks else f"Your to-do list for {task_date} is empty."

    def update_task_display(self, tasks=None):
        if tasks is None:
            tasks = self.todo_list.get_tasks()
        self.task_display.update_tasks([f"{i+1}. {t['task']}" for i, t in enumerate(tasks)])
        self.task_display.root.after(0, self.task_display.root.deiconify)  # Show the GUI

    def speak(self, text):
        # Save the current system volume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_volume = volume.GetMasterVolumeLevel()

        try:
            # Lower the volume
            volume.SetMasterVolumeLevel(-30.0, None)  # Lower volume to 10%
            logging.info("System volume lowered to 10%.")

            # Remove GenTopic from the text if present
            if "GenTopic:" in text:
                text = text.split("GenTopic:")[0].strip()

            ssml_template = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{self.speech_config.speech_synthesis_voice_name}">
                    <prosody volume="{self.volume}%" rate="{self.speed}%">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            result = self.speech_synthesizer.speak_ssml_async(ssml_template).get()
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logging.info("Speech synthesized for text [{}]".format(text))
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logging.error("Speech synthesis canceled: {}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logging.error("Error details: {}".format(cancellation_details.error_details))
                    print("Error details: {}".format(cancellation_details.error_details))
        finally:
            # Restore the original system volume
            volume.SetMasterVolumeLevel(current_volume, None)
            logging.info("System volume restored to original level.")

    def jarvis_response(self, transcription):
        response = self.jarvis.get_response(transcription)
        logging.info(f"Jarvis response: {response}")
        if isinstance(response, dict):
            text = response.get('text', 'I am not sure how to respond to that.')
            gen_topic = response.get('GenTopic', '')
            logging.info(f"GenTopic: {gen_topic}")
            return text
        return response
    def jarvis_response(self, transcription):
        response = self.jarvis.get_response(transcription)
        logging.info(f"Jarvis response: {response}")
        if isinstance(response, dict):
            text = response.get('text', 'I am not sure how to respond to that.')
            gen_topic = response.get('GenTopic', '')
            logging.info(f"GenTopic: {gen_topic}")
            return text
        return response

    def handle_activation_trigger(self):
        logging.info("Activation word detected! Lowering system volume.")
        print("Activation word detected! Lowering system volume.")
        self.lower_volume_immediately()
        self.activation_manager.activate()

    def lower_volume_immediately(self):
        # Lower the volume used for SSML synthesis
        self.volume = 10  # This affects only the synthesized speech volume in SSML
        logging.info("Speech synthesis volume lowered to 10%.")
        # Now lower the entire system's master volume using pycaw (Windows-only)
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            # Set system volume to 10% (0.1 as a scalar value between 0.0 and 1.0)
            volume_interface.SetMasterVolumeLevelScalar(0.1, None)
            logging.info("System volume lowered to 10%.")
        except Exception as e:
            logging.error("Failed to lower system volume: " + str(e))
    
    def restore_volume(self):
        # Restore the volume used for SSML synthesis
        self.volume = 100
        logging.info("Speech synthesis volume restored to 100%.")
        # Restore the system's master volume using pycaw (Windows-only)
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            # Restore system volume to previous level
            volume_interface.SetMasterVolumeLevelScalar(1.0, None)
            logging.info("System volume restored to 100%.")
        except Exception as e:
            logging.error("Failed to restore system volume: " + str(e))
