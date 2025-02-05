import sys
import threading
import queue
import time
import signal
import speech_recognition as sr
import pyaudio
import wave

class Microphone:
    def __init__(self, activation_phrase="jarvis"):
        self.activation_phrase = activation_phrase
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.transcription_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.recording = False

        signal.signal(signal.SIGINT, self.signal_handler)

        # Initialize PyAudio
        self.pyaudio = pyaudio.PyAudio()
        self.input_stream = self.pyaudio.open(format=pyaudio.paInt16,
                                              channels=1,
                                              rate=16000,
                                              input=True,
                                              frames_per_buffer=1024,
                                              stream_callback=self.callback)
        self.output_stream = self.pyaudio.open(format=pyaudio.paInt16,
                                               channels=1,
                                               rate=16000,
                                               output=True)

    def signal_handler(self, sig, frame):
        print("\nExiting...")
        self.input_stream.stop_stream()
        self.input_stream.close()
        self.output_stream.stop_stream()
        self.output_stream.close()
        self.pyaudio.terminate()
        sys.exit(0)

    def callback(self, in_data, frame_count, time_info, status):
        if self.recording:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def listen(self):
        while True:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                self.recognizer.pause_threshold = 2  # Adjust pause threshold for end of phrase detection
                audio = self.recognizer.listen(source, phrase_time_limit=10)  # Adjust phrase_time_limit as needed

            try:
                transcription = self.recognizer.recognize_google(audio).lower()
                self.transcription_queue.put(transcription)
            except sr.UnknownValueError:
                continue
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
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        while not self.audio_queue.empty():
            wf.writeframes(self.audio_queue.get())
        wf.close()

    def play_audio(self, filename):
        wf = wave.open(filename, 'rb')
        stream = self.pyaudio.open(format=self.pyaudio.get_format_from_width(wf.getsampwidth()),
                                   channels=wf.getnchannels(),
                                   rate=wf.getframerate(),
                                   output=True)
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
        stream.stop_stream()
        stream.close()
        wf.close()