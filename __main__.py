import discord
from discord.ext import commands
from discord.ui import Button, View
from rich.console import Console
import os
from dotenv import load_dotenv
import asyncio

console = Console()
# Load environment variables from .env file
load_dotenv()
token = os.getenv("TOKEN")
openai_key = os.getenv("OPENAI_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    console.print(f"Logged in as {bot.user}")

async def load_extensions():
    console.print("Loading cogs...")
    await bot.load_extension("fun")
    await bot.load_extension("marriages")
    await bot.load_extension("ai")
    await bot.load_extension("reactions")
    console.print("All cogs loaded.")

# Other commands
@bot.command()
async def id(ctx: commands.Context, user: discord.Member):
    await ctx.send(f"{user.id}")

@bot.command()
async def wiki(ctx: commands.Context):
    """cool github wiki"""
    await ctx.send("https://github.com/Ierzi/ierzi-bot/wiki/")

@bot.command()
async def github(ctx: commands.Context):
    """cool github repo"""
    await ctx.send("https://github.com/Ierzi/ierzi-bot \nbtw i have no fucking clue how contributing on github works")

# @bot.command()
# async def debug(ctx: commands.Context, fake_n_marriages: int | None = None):
#     """Ignore this"""
#     marriages = await get_marriages()
#     console.print(marriages)

async def main():
    await load_extensions()
    await bot.start(token)
    console.print("Bot is ready.")

asyncio.run(main())