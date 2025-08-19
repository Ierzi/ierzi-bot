import discord
from discord.ext import commands
from rich.console import Console
import os
from dotenv import load_dotenv

console = Console()
# Load environment variables from .env file
load_dotenv()
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    console.print(f"Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")


bot.run(token)