import discord
from discord.ext import commands
from rich.console import Console
import os
from dotenv import load_dotenv
import asyncio
import json

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
    marriage_file = "marriages.json"
    with open(marriage_file, "r") as f:
        global marriages
        marriages = list(json.load(f))

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send("Hello!")

# Marriage commands
async def add_marriage_list(marriage_pair):
    """Update the marriage list with a new marriage pair."""
    marriages.append(marriage_pair)
    marriages.append((marriage_pair[1], marriage_pair[0]))

    with open("marriages.json", "w") as f:
        json.dump(marriages, f, indent=4)
        console.print(f"Marriage list updated with {marriage_pair}.")

async def remove_marriage_list(marriage_pair):
    """Remove a marriage pair from the list."""
    if marriage_pair in marriages:
        marriages.remove(marriage_pair)
        marriages.remove((marriage_pair[1], marriage_pair[0]))
        with open("marriages.json", "w") as f:
            json.dump(marriages, f, indent=4)
            console.print(f"Marriage list updated by removing {marriage_pair}.")
    else:
        console.print(f"Marriage pair {marriage_pair} not found in the list.")

@bot.command()
async def marry(ctx: commands.Context, partner: discord.Member):
    proposer = ctx.author

    if proposer.id == partner.id:
        await ctx.send("You cannot marry yourself!")
        return
    if (proposer.id, partner.id) in marriages or (partner.id, proposer.id) in marriages:
        await ctx.send("You are already married to this person!")
        return
    
    await ctx.send(f"{partner.name}, do you want to marry {proposer.name}?", silent=True)
    await ctx.send(f"Reply with yes if you accept, or no if you decline.")
    
    def check(m: discord.Message):
        return m.author.id == partner.id and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send("Marriage proposal timed out.")
        return
    
    if msg.content.lower() == "yes":
        await ctx.send(f"Congratulations {proposer.name} and {partner.name}, you are now happilly married!", silent=True)
        console.print(f"Marriage between {proposer.name} and {partner.name} has been recorded.")
        await add_marriage_list((proposer.id, partner.id))
    else:
        await ctx.send(f"{proposer.mention} has declined the marriage proposal.")

@bot.command()
async def divorce(ctx: commands.Context, partner: discord.Member):
    proposer = ctx.author

    if (proposer.id, partner.id) not in marriages and (partner.id, proposer.id) not in marriages:
        await ctx.send("You are not married to this person!")
        return
    
    await ctx.send(f"Are you sure you want to divorce {partner.name}?")
    await ctx.send(f"Reply with yes if you accept, or no if you decline.")
    
    def check(m: discord.Message):
        return m.author.id == proposer.id and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send("Divorce request timed out.")
        return
    
    if msg.content.lower() == "yes":
        await remove_marriage_list((proposer.id, partner.id))
        await ctx.send(f"Divorce between {proposer.name} and {partner.name} has been processed.", silent=True)
        console.print(f"Divorce between {proposer.name} and {partner.name} has been recorded.")
    else:
        await ctx.send(f"{proposer.mention} has declined the divorce proposal.")


bot.run(token)