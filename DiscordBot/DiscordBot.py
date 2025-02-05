import discord
from discord.ext import commands

class DiscordBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        # Initialize the bot with the given command prefix and intents.
        super().__init__(command_prefix=command_prefix, intents=intents)

    async def on_ready(self):
        # This method is called when the bot has successfully connected.
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def send_message_to_user(self, user_id: int, message: str):
        """
        Sends a direct message to the user with the given user_id.

        Parameters:
        - user_id (int): The Discord ID of the user to message.
        - message (str): The message content to send.
        """
        # Try to get the user from the cache.
        user = self.get_user(user_id)
        if user is None:
            try:
                # If the user is not in cache, fetch the user.
                user = await self.fetch_user(user_id)
            except discord.NotFound:
                print(f"User with ID {user_id} not found.")
                return

        try:
            await user.send(message)
            print(f"Message sent to user {user.name} (ID: {user.id}).")
        except Exception as e:
            print(f"Failed to send message to user {user_id}: {e}")

if __name__ == '__main__':
    # Set up the required intents. 'members' intent can help ensure we can fetch users.
    intents = discord.Intents.default()
    intents.members = True

    # Create an instance of the bot with the desired command prefix.
    bot = DiscordBot(command_prefix="!", intents=intents)
    token = "YOUR_BOT_TOKEN"  # Replace with your actual bot token.

    # Optional: Create a command for demonstration purposes.
    @bot.command()
    async def dm(ctx, user_id: int, *, message: str):
        """
        Command to send a DM to a specified user.
        Usage: !dm <user_id> <message>
        """
        await bot.send_message_to_user(user_id, message)
        await ctx.send(f"Attempted to send DM to user with ID {user_id}.")

    bot.run(token)
