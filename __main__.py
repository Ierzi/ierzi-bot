import discord
from rich.console import Console
import os
from dotenv import load_dotenv

console = Console()
# Load environment variables from .env file
load_dotenv()
token = os.getenv("TOKEN")

class IerziBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        console.print(f"Logged in as {self.user.name} (ID: {self.user.id})")
        await self.test_command()

    async def test_command(self):
        command = str(console.input("[bold green]Enter a command to execute: [/bold green]"))
        await self.handle_command(command)
    
    async def handle_command(self, command: str):
        if command.startswith("send"):
            message = command.lstrip("send ")
            channel_id = int(console.input("[bold green]Enter the channel ID: [/bold green]"))
            channel = self.get_channel(channel_id)
            if channel:
                console.print(f"[bold blue]Sending message to channel {channel.name}...[/bold blue]")
                await self.loop.create_task(channel.send(message))
            else:
                console.print("[bold red]Channel not found![/bold red]")
        
        await self.test_command()
    
    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if message.content.startswith("!test"):
            await message.channel.send("test yeah")

        # Add more commands as needed
        console.print(f"[bold yellow]Message from {message.author}: {message.content}[/bold yellow]")

if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    bot = IerziBot(intents=intents)
    bot.run(token)
