import openai
import os
import time
from dotenv import load_dotenv

class JarvisAssistant:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

        # Assistant-specific attributes
        self.assistant_id = os.getenv("OPENAI_ASSISTANT_ID")  # Get assistant ID from environment
        self.thread_id = None

    def create_thread(self):
        try:
            thread = openai.beta.threads.create()
            self.thread_id = thread.id  # Correctly access the thread ID
            print(f"Thread created with ID: {self.thread_id}")
        except Exception as e:
            print(f"Failed to create a thread: {e}")
            self.thread_id = None

    def get_response(self, user_input):
        """
        Sends a user message, creates a thread if necessary, and fetches the assistant's response.
        """
        if not self.thread_id:
            self.create_thread()
        if not self.thread_id:
            return {"text": "Failed to start a conversation. Please try again."}

        try:
            # Add a user message to the thread
            message = openai.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=user_input
            )

            # Use the assistant to generate a response
            run = openai.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id  # Use the specific assistant ID
            )

            # Poll for the run to complete
            for _ in range(60):  # Poll up to 60 times
                run = openai.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                if run.status == "completed":
                    break
                time.sleep(0.2)  # Wait 0.2 seconds before polling again

            if run.status != "completed":
                return {"text": "The assistant did not complete the response in time."}

            # Fetch the messages from the thread to get the assistant's response
            messages = openai.beta.threads.messages.list(thread_id=self.thread_id)

            for msg in messages:
                if msg.role == "assistant":
                    response_text = msg.content[0].text.value.strip()  # Get the assistant's response
                    return {"text": response_text}

            return {"text": "No response from the assistant."}

        except Exception as e:
            return {"text": f"An error occurred: {e}"}

    def list_attributes(self):
        """
        Lists the attributes of the assistant.
        """
        return {
            "Assistant ID": self.assistant_id,
            "Thread ID": self.thread_id,
        }