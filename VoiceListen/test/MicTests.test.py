import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from VoiceListen.Microphone import Microphone
from flask_socketio import SocketIO

class TestWaitMic(unittest.TestCase):
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def setUp(self, MockRecognizer, MockMicrophone):
        self.mock_recognizer = MockRecognizer.return_value
        self.mock_microphone = MockMicrophone.return_value
        self.mock_socketio = MagicMock(spec=SocketIO)
        self.mock_obj = MagicMock()
        self.wait_mic = Microphone(self.mock_obj, self.mock_socketio)

    def test_signal_handler(self):
        with self.assertRaises(SystemExit):
            self.wait_mic.signal_handler(None, None)

    @patch('speech_recognition.Recognizer.listen')
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_listen(self, mock_recognize_google, mock_listen):
        mock_recognize_google.return_value = "jarvis"
        mock_listen.return_value = MagicMock()

        with patch('queue.Queue.put') as mock_put:
            self.wait_mic.listen()
            mock_put.assert_called_with("jarvis")

    @patch('queue.Queue.get')
    def test_process_transcriptions(self, mock_get):
        mock_get.return_value = "jarvis"
        self.mock_obj.get_response.return_value = "response"

        with patch('VoiceListen.Microphone.Microphone.listen_for_following_speech') as mock_listen_for_following_speech:
            self.wait_mic.process_transcriptions()
            self.mock_socketio.emit.assert_called_with("response", "response")
            mock_listen_for_following_speech.assert_called()

    @patch('speech_recognition.Recognizer.listen')
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_listen_for_following_speech(self, mock_recognize_google, mock_listen):
        mock_recognize_google.return_value = "response"
        mock_listen.return_value = MagicMock()

        with patch('queue.Queue.put') as mock_put:
            self.wait_mic.listen_for_following_speech()
            mock_put.assert_called_with("response")

    def test_start(self):
        with patch('threading.Thread.start') as mock_start:
            self.wait_mic.start()
            self.assertEqual(mock_start.call_count, 2)

if __name__ == '__main__':
    unittest.main()