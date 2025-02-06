import discord
import asyncio
import os
from datetime import datetime
from VoiceAssistant import VoiceAssistant
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DiscordBot:
    def __init__(self, voice_assistant):
        self.token = os.getenv('DISCORD_TOKEN')
        self.application_id = os.getenv('DISCORD_APPLICATION_ID')
        self.public_key = os.getenv('DISCORD_PUBLIC_KEY')
        self.voice_assistant = voice_assistant
        self.client = discord.Client()

        @self.client.event
        async def on_ready():
            print(f'Logged in as {self.client.user}')
            await self.send_daily_todo_list()

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return

            if isinstance(message.channel, discord.DMChannel):
                response = self.voice_assistant.handle_transcription(message.content)
                await message.channel.send(response)

    async def send_daily_todo_list(self):
        await self.client.wait_until_ready()
        while not self.client.is_closed():
            now = datetime.now()
            if now.hour == 5 and now.minute == 0:
                tasks = self.voice_assistant.list_tasks()
                user = await self.client.fetch_user()  # Replace with your user ID
                await user.send(f"Good morning! Here is your to-do list for today:\n{tasks}")
                await asyncio.sleep(60)  # Wait a minute to avoid sending multiple messages
            await asyncio.sleep(1)  # Check every second

    def run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.send_daily_todo_list())
        self.client.run(self.token)
