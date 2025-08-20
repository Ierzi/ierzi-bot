import discord
from discord.ext import commands
from rich.console import Console
import os
from dotenv import load_dotenv
import asyncio
import json
from openai import OpenAI

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
    marriage_file = "marriages.json"
    with open(marriage_file, "r") as f:
        global marriages
        marriages = list(json.load(f))

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send("Hello!")

# Marriage commands
async def update_marriage_list():
    with open("marriages.json", "r") as f:
        global marriages
        marriages = list(json.load(f))

async def add_marriage_list(marriage_pair: tuple):
    """Update the marriage list with a new marriage pair."""
    if marriage_pair in marriages:
        console.print(f"Marriage pair {marriage_pair} already exists in the list.")
        return
    
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
    
    await ctx.send(f"{partner.mention}, do you want to marry {proposer.mention}?", allowed_mentions=discord.AllowedMentions.none())
    await ctx.send(f"Reply with yes if you accept, or no if you decline.")
    
    def check(m: discord.Message):
        return m.author.id == partner.id and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send("Marriage proposal timed out.")
        return
    
    if msg.content.lower() == "yes":
        await ctx.send(f"Congratulations {proposer.mention} and {partner.mention}, you are now happilly married!", allowed_mentions=discord.AllowedMentions.none())
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
    
    await ctx.send(f"Are you sure you want to divorce {partner.mention}?", allowed_mentions=discord.AllowedMentions.none())
    await ctx.send(f"Reply with yes if you confirm, or no if you decline.")
    
    def check(m: discord.Message):
        return m.author.id == proposer.id and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send("Divorce request timed out.")
        return
    
    if msg.content.lower() == "yes":
        # Remove the marriage from the list
        await remove_marriage_list((proposer.id, partner.id))
        await ctx.send(f"{proposer.mention} and {partner.mention} have been divorced.", allowed_mentions=discord.AllowedMentions.none())
        await ctx.send("-# its over...")
        console.print(f"Divorce between {proposer.name} and {partner.name} has been recorded.")
    else:
        await ctx.send(f"{proposer.mention} has declined the divorce proposal.")


# TODO
@bot.command()
async def listmarriages(ctx: commands.Context, page_number: int = 1):
    """List all current marriages."""
    # Update
    await update_marriage_list()

    if not marriages:
        await ctx.send("Nobody is married yet!")
        return
    else:
        if page_number > n_pages:
            await ctx.send(f"Invalid page number. There are only {n_pages} pages of marriages.")
            return
        
        # Send some sort of message to indicate that the bot is processing the request
        think = await ctx.send("Thinking...")
        think_slow = await ctx.send("-# slow ass program (why did i make it in python)")
        # Calculate the number of pages based on the number of marriages
        n_marriages = len(marriages) 
        n_pages = round(n_marriages // 10 + 1)
        
        all_messages = ""
        start_index = (page_number - 1) * 10
        count = 0
        mess_count = 0
        for i, pair in enumerate(marriages):
            count += 1
            if count <= start_index:
                continue
            if mess_count == 10:
                # Reach the end of the page
                break

            if i % 10 == 0:
                all_messages += f"**Page {page_number}**\n"
            
            if i >= start_index:
                user_1 = bot.get_user(pair[0]) or await bot.fetch_user(pair[0])
                user_2 = bot.get_user(pair[1]) or await bot.fetch_user(pair[1])
                all_messages += f"{user_1.mention} and {user_2.mention}\n"
                mess_count += 1
        
        # After thinking, deletes the "Thinking..." message
        await think.delete()
        await think_slow.delete()
        await ctx.send(all_messages, allowed_mentions=discord.AllowedMentions.none())

@bot.command()
async def marriagestatus(ctx: commands.Context):
    """Check the marriage status of a user."""
    await update_marriage_list()
    
    user = ctx.author
    user_marriages = [pair for pair in marriages if user.id in pair]
    
    if not user_marriages:
        await ctx.send(f"{user.mention} is not married.")
        return
    
    marriage_status = ""
    for pair in user_marriages:
        partner_id = pair[0] if pair[1] == user.id else pair[1]
        partner = bot.get_user(partner_id) or await bot.fetch_user(partner_id)
        message = f"{user.mention} is married to {partner.mention}.\n"
        marriage_status += message if message not in marriage_status else ""
    
    await ctx.send(marriage_status, allowed_mentions=discord.AllowedMentions.none())

# OpenAI commands
@bot.command()
async def aiask(ctx: commands.Context, text: str):
    author = ctx.author

    client = OpenAI(api_key=openai_key)
    response = client.responses.create(
        model="gpt-5-nano",
        input=text
    )

    console.print(f"AI response: {response.output_text}")
    text = f"{author.mention}: {text} \n AI: {response.output_text}"
    await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())


# @bot.command()
# async def debug(ctx: commands.Context, fake_n_marriages: int | None = None):
#     if not fake_n_marriages:
#         n_marriages = len(marriages)
#         await ctx.send(f"Current marriages: {n_marriages} pairs.")
#         await ctx.send(marriages)
#     else:
#         n_marriages = fake_n_marriages
#         await ctx.send(f"Debugging with {n_marriages} fake marriages.")

#     number_of_pages = round(n_marriages // 10 + 1)
#     await ctx.send(number_of_pages)

bot.run(token)