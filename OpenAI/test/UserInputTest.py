import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from OpenAI.Assistant import JarvisAssistant

def main():
    assistant = JarvisAssistant()

    print("Welcome to the Jarvis Assistant Tester!")
    print("Type 'exit' to quit the program.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        response = assistant.get_response(user_input)
        print(f"Jarvis: {response}")

if __name__ == "__main__":
    main()