import sys
import threading
import queue
import time
import signal
import speech_recognition as sr
import pyaudio
import wave
import logging

class Microphone:
    def __init__(self, activation_phrase="jarvis"):
        self.activation_phrase = activation_phrase
        self.recognizer = sr.Recognizer()
        # Enable dynamic energy threshold adjustment
        self.recognizer.dynamic_energy_threshold = True

        self.microphone = sr.Microphone()
        self.transcription_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.recording = False
        self.listening_for_activation = True
        self.cleaned_up = False  # Flag to indicate if cleanup has been performed

        signal.signal(signal.SIGINT, self.signal_handler)

        # Perform one-time ambient noise calibration
        with self.microphone as source:
            print("Calibrating for ambient noise... Please wait.")
            self.recognizer.adjust_for_ambient_noise(source, duration=5)  # Increase calibration duration
            print(f"Set energy threshold to {self.recognizer.energy_threshold}")

    def signal_handler(self, sig, frame):
        if not self.cleaned_up:
            print("\nExiting...")
            logging.info("Exiting...")
            self.cleanup()

    def cleanup(self):
        if not self.cleaned_up:
            # Perform any necessary cleanup here
            self.recording = False
            self.listening_for_activation = False
            logging.info("Cleanup completed.")
            self.cleaned_up = True

    def listen(self):
        while True:
            with self.microphone as source:
                # Adjust thresholds based on state
                if self.listening_for_activation:
                    self.recognizer.pause_threshold = 0.7      # Increase pause threshold for better detection
                    self.recognizer.non_speaking_duration = 0.5  # Increase non_speaking_duration
                    phrase_time_limit = 3                        # Expect a very short utterance
                else:
                    self.recognizer.pause_threshold = 1.0
                    self.recognizer.non_speaking_duration = 0.7
                    phrase_time_limit = 10

                # Listen for speech (you may adjust phrase_time_limit as needed)
                try:
                    audio = self.recognizer.listen(source, phrase_time_limit=phrase_time_limit)
                    transcription = self.recognizer.recognize_google(audio, language="en-US").lower()
                    print(f"Transcription: {transcription}")

                    if self.listening_for_activation:
                        if transcription.strip() == self.activation_phrase:
                            self.transcription_queue.put(self.activation_phrase)
                            self.listening_for_activation = False
                            logging.info("Activation word detected. Listening for next phrase.")
                    else:
                        self.transcription_queue.put(transcription)
                        self.listening_for_activation = True  # Reset to listen for activation word again
                except sr.UnknownValueError:
                    pass  # Suppress "Could not understand audio" message
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")

    def listen_in_background(self):
        listen_thread = threading.Thread(target=self.listen, daemon=True)
        listen_thread.start()

    def start_recording(self):
        self.recording = True

    def stop_recording(self):
        self.recording = False

    def save_audio(self, filename):
        # Save any recorded audio from the queue
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        while not self.audio_queue.empty():
            wf.writeframes(self.audio_queue.get())
        wf.close()

    def play_audio(self, filename):
        wf = wave.open(filename, 'rb')
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                         channels=wf.getnchannels(),
                         rate=wf.getframerate(),
                         output=True)
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
        stream.stop_stream()
        stream.close()
        pa.terminate()
        wf.close()

    def reset_listening_state(self):
        self.listening_for_activation = True