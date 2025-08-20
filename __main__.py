import discord
from discord.ext import commands
from rich.console import Console
import os
from dotenv import load_dotenv
import asyncio
from openai import OpenAI
import psycopg2
import random

console = Console()
# Load environment variables from .env file
load_dotenv()
token = os.getenv("TOKEN")
openai_key = os.getenv("OPENAI_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Init database
conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)

cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS marriages (
        id SERIAL PRIMARY KEY,
        user1_id BIGINT NOT NULL,
        user2_id BIGINT NOT NULL
    );
""")

conn.commit()

@bot.event
async def on_ready():
    console.print(f"Logged in as {bot.user}")

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send(random.choice(["hi", "hello", "fuck you"]))

async def add_marriage_list(marriage_pair: tuple[discord.User]):
    cur.execute(
        "INSERT INTO marriages (user1_id, user2_id) VALUES (%s, %s)", 
        (marriage_pair[0].id, marriage_pair[1].id)
        )
    cur.execute(
        "INSERT INTO marriages (user1_id, user2_id) VALUES (%s, %s)", 
        (marriage_pair[1].id, marriage_pair[0].id)
        )
    conn.commit()

async def remove_marriage_list(marriage_pair: tuple[discord.User]):
    cur.execute(
        "DELETE FROM marriages WHERE user1_id = %s AND user2_id = %s",
        (marriage_pair[0].id, marriage_pair[1].id)
    )
    cur.execute(
        "DELETE FROM marriages WHERE user1_id = %s AND user2_id = %s",
        (marriage_pair[1].id, marriage_pair[0].id)
    )
    conn.commit()


async def get_marriages():
    cur.execute("SELECT * FROM marriages")
    marriages = cur.fetchall()
    return marriages

@bot.command()
async def marry(ctx: commands.Context, partner: discord.Member):
    proposer = ctx.author
    marriages = await get_marriages()

    if proposer.id == partner.id:
        await ctx.send("...")
        return
    if partner.id == bot.user.id:
        await ctx.send("faggot")
        return
    if partner.bot:
        await ctx.send("dumbass")
        return
    if (proposer.id, partner.id) in marriages or (partner.id, proposer.id) in marriages:
        await ctx.send("does he know?")
        return
    
    await ctx.send(f"{partner.mention}, do you want to marry {proposer.mention}? \n Reply with yes if you accept, or no if you decline.", allowed_mentions=discord.AllowedMentions.none())

    def check(m: discord.Message):
        return m.author.id == partner.id and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send(f"Marriage proposal for {partner.id} timed out.", allowed_mentions=discord.AllowedMentions.none())
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
    marriages = await get_marriages()

    if (proposer.id, partner.id) not in marriages and (partner.id, proposer.id) not in marriages:
        await ctx.send("You are not married to this person!")
        return
    
    await ctx.send(f"Are you sure you want to divorce {partner.mention}? \n Reply with yes if you confirm, or no if you changed your mind. ", allowed_mentions=discord.AllowedMentions.none())
    
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
        await ctx.send(f"{proposer.mention} and {partner.mention} have been divorced. \n -# its over...", allowed_mentions=discord.AllowedMentions.none())
        console.print(f"Divorce between {proposer.name} and {partner.name} has been recorded.")
    else:
        await ctx.send(f"{proposer.mention} has canceled the divorce proposal.")


@bot.command()
async def listmarriages(ctx: commands.Context, page_number: int = 1):
    marriages = await get_marriages()
        
    if not marriages:
        await ctx.send("Nobody is married yet!")
        return
    else:
        n_marriages = len(marriages) 
        n_pages = round(n_marriages // 10 + 1)
        
        if page_number > n_pages or page_number < 1:
            await ctx.send(f"Invalid page number. There are {n_pages} pages of marriages.")
            return
        
        # Send some sort of message to indicate that the bot is processing the request
        think = await ctx.send("Thinking...")
        think_slow = await ctx.send("-# slow ass program (why did i make it in python)")

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
        
        await think.delete()
        await think_slow.delete()
        await ctx.send(all_messages, allowed_mentions=discord.AllowedMentions.none())

@bot.command()
async def marriagestatus(ctx: commands.Context):
    user = ctx.author
    marriages = await get_marriages()
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

@bot.command()
async def forcemarry(ctx: commands.Context, user1: discord.Member, user2: discord.Member):
    marriages = await get_marriages()
    if (user1.id, user2.id) in marriages or (user2.id, user1.id) in marriages:
        await ctx.send("does he know?")
        return
    if user1.id == user2.id:
        await ctx.send("dumbass")
        return
    if ctx.author.id != 966351518020300841:
        await ctx.send("no.")
        return
    
    await add_marriage_list((user1.id, user2.id))
    await ctx.send(f"{user1.mention} and {user2.mention} are now married!", allowed_mentions=discord.AllowedMentions.none())
    console.print(f"Forced marriage between {user1.name} and {user2.name} has been recorded.")

@bot.command()
async def forcedivorce(ctx: commands.Context, user1: discord.Member, user2: discord.Member):
    marriages = await get_marriages()
    if (user1.id, user2.id) not in marriages and (user2.id, user1.id) not in marriages:
        await ctx.send("they are not married lmao")
        return
    if ctx.author.id != 966351518020300841:
        await ctx.send("no.")
        return
    
    await remove_marriage_list((user1.id, user2.id))
    await ctx.send(f"{user1.mention} and {user2.mention} have been divorced.", allowed_mentions=discord.AllowedMentions.none())
    console.print(f"Forced divorce between {user1.name} and {user2.name} has been recorded.")

# OpenAI commands
@bot.command()
async def aiask(ctx: commands.Context, *, text: str):
    author = ctx.author
    thinking = await ctx.send("The ai is thinking...")

    client = OpenAI(api_key=openai_key)
    response = client.responses.create(
        model="gpt-5-nano",
        input=text
    )

    console.print(f"AI response: {response.output_text}")
    text = f"{author.mention}: {text} \n \n AI: {response.output_text}"
    await thinking.delete()
    await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

# Other commands
@bot.command()
async def id(ctx: commands.Context, user: discord.Member):
    """Get the ID of a user."""
    await ctx.send(f"{user.id}")

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