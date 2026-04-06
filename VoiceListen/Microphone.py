import sys
import threading
import queue
import time
import signal
import speech_recognition as sr
import pyaudio
import wave
import numpy as np
import noisereduce as nr  # Ensure you have installed noisereduce: pip install noisereduce

class Microphone:
    def __init__(self, activation_phrase="jarvis", amplification_factor=2.0, use_noise_reduction=True):
        """
        :param activation_phrase: Activation phrase (not used in this snippet but kept for future expansion)
        :param amplification_factor: Multiplier to amplify the raw audio input.
        :param use_noise_reduction: If True, applies noise reduction to the audio.
        """
        self.activation_phrase = activation_phrase
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.transcription_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.recording = False
        self.amplification_factor = amplification_factor
        self.use_noise_reduction = use_noise_reduction

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

    @staticmethod
    def amplify_audio(audio_data, factor=2.0):
        """
        Amplify the input audio data by a given factor.
        """
        # Convert byte data to a NumPy array of int16 values.
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        # Multiply by the factor and clip to avoid overflow.
        amplified_array = np.clip(audio_array * factor, -32768, 32767).astype(np.int16)
        return amplified_array.tobytes()

    def reduce_noise(self, audio_data):
        """
        Apply noise reduction to the provided audio data using noisereduce.
        """
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        # Apply noise reduction; you can tweak parameters if needed.
        reduced_noise = nr.reduce_noise(y=audio_array, sr=16000)
        return reduced_noise.astype(np.int16).tobytes()

    def callback(self, in_data, frame_count, time_info, status):
        if self.recording:
            # First amplify the audio.
            processed_data = self.amplify_audio(in_data, factor=self.amplification_factor)
            # Optionally, apply noise reduction per frame.
            if self.use_noise_reduction:
                processed_data = self.reduce_noise(processed_data)
            self.audio_queue.put(processed_data)
        return (in_data, pyaudio.paContinue)

    def calibrate(self, duration=1):
        """
        Calibrate the microphone to adjust for ambient noise.
        """
        with self.microphone as source:
            print("Calibrating microphone... Please be silent.")
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            # Optionally, adjust the energy threshold further.
            self.recognizer.energy_threshold *= 1.2
            print(f"Calibration complete. Energy threshold set to {self.recognizer.energy_threshold}")

    def listen(self):
        # Calibrate once before starting the listening loop.
        self.calibrate(duration=1)
        while True:
            with self.microphone as source:
                self.recognizer.pause_threshold = 2  # Adjust pause threshold as needed.
                # Use a shorter phrase_time_limit for more frequent transcriptions.
                audio = self.recognizer.listen(source, phrase_time_limit=3)
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
        """
        Save the recorded audio to a file.
        If noise reduction is enabled, the entire clip is processed before saving.
        """
        frames = []
        while not self.audio_queue.empty():
            frames.append(self.audio_queue.get())
        audio_data = b''.join(frames)
        # Optionally, apply noise reduction to the complete audio clip.
        if self.use_noise_reduction:
            audio_data = self.reduce_noise(audio_data)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(audio_data)
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
