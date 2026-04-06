import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from OpenAI.Assistant import JarvisAssistant

class TestJarvisAssistant(unittest.TestCase):
    @patch('openai.beta.threads.create')
    @patch('openai.beta.threads.messages.create')
    @patch('openai.beta.threads.runs.create')
    @patch('openai.beta.threads.runs.retrieve')
    @patch('openai.beta.threads.messages.list')
    def setUp(self, mock_list, mock_retrieve, mock_run_create, mock_message_create, mock_thread_create):
        self.mock_thread_create = mock_thread_create
        self.mock_message_create = mock_message_create
        self.mock_run_create = mock_run_create
        self.mock_retrieve = mock_retrieve
        self.mock_list = mock_list

        self.mock_thread_create.return_value.id = "thread_id"
        self.mock_message_create.return_value = MagicMock()
        self.mock_run_create.return_value.id = "run_id"
        self.mock_retrieve.return_value.status = "completed"
        self.mock_list.return_value = [
            MagicMock(role="assistant", content=[MagicMock(text=MagicMock(value="response"))])
        ]

        self.assistant = JarvisAssistant()

    def test_create_thread(self):
        self.assistant.create_thread()
        self.assertEqual(self.assistant.thread_id, "thread_id")

    def test_get_response(self):
        response = self.assistant.get_response("Hello")
        self.assertEqual(response, "response")

    def test_get_response_no_thread(self):
        self.mock_thread_create.side_effect = Exception("Failed to create a thread")
        response = self.assistant.get_response("Hello")
        self.assertEqual(response, "Failed to start a conversation. Please try again.")

    def test_get_response_run_not_completed(self):
        self.mock_retrieve.return_value.status = "not_completed"
        response = self.assistant.get_response("Hello")
        self.assertEqual(response, "The assistant did not complete the response in time.")

    def test_get_response_no_assistant_response(self):
        self.mock_list.return_value = [
            MagicMock(role="user", content=[MagicMock(text=MagicMock(value="user message"))])
        ]
        response = self.assistant.get_response("Hello")
        self.assertEqual(response, "No response from the assistant.")

    def test_list_attributes(self):
        attributes = self.assistant.list_attributes()
        self.assertEqual(attributes["Assistant ID"], self.assistant.assistant_id)
        self.assertEqual(attributes["Thread ID"], self.assistant.thread_id)

if __name__ == '__main__':
    unittest.main()