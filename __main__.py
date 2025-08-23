import discord
from discord.ext import commands
from discord.ui import Button, View
from rich.console import Console
import os
from dotenv import load_dotenv
import asyncio
from cogs.ai import AI
from cogs.economy import Economy
from cogs.fun import Fun
from cogs.marriages import Marriages
from cogs.reactions import Reactions

console = Console()

load_dotenv()
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    console.print(f"Logged in as {bot.user}")

async def load_cogs():
    console.print("Loading cogs...")
    await bot.add_cog(AI(bot))
    console.print("AI cog loaded.")
    await bot.add_cog(Economy(bot))
    console.print("Economy cog loaded.")
    await bot.add_cog(Fun(bot))
    console.print("Fun cog loaded.")
    await bot.add_cog(Marriages(bot))
    console.print("Marriages cog loaded.")
    await bot.add_cog(Reactions(bot))
    console.print("Reactions cog loaded.")
    console.print("All cogs loaded.")

# Other commands
@bot.command()
async def id(ctx: commands.Context, user: discord.Member):
    if not user:
        await ctx.send(ctx.author.id)
        return
    
    await ctx.send(user.id)

@bot.command()
async def wiki(ctx: commands.Context):
    """cool github wiki"""
    view = View()
    wiki_button = Button(
        label="Wiki",
        url="https://github.com/Ierzi/ierzi-bot/wiki/"
    )
    view.add_item(wiki_button)
    await ctx.send(view=view)

@bot.command()
async def github(ctx: commands.Context):
    """cool github repo"""
    await ctx.send("https://github.com/Ierzi/ierzi-bot \n-# btw i have no fucking clue how contributing on github works")

@bot.command()
async def roadmap(ctx: commands.Context):
    """features i wanna add"""
    features = [
        "cool typing animations", "fix !work", "add more reactions", 
        "!listmarrriages", "fix ai commands that works half the time", "custom emojis"
    ] # the cat command is gonna piss off fact lmao
    message = "Features I wanna add: \n"
    for feature in features:
        message += f"- {feature}\n"
    await ctx.send(message)


# @bot.command()
# async def debug(ctx: commands.Context, fake_n_marriages: int | None = None):
#     """Ignore this"""
#     marriages = await get_marriages()
#     console.print(marriages)

async def main():
    await load_cogs()
    await bot.start(token)
    console.print("Bot is ready.")

asyncio.run(main())