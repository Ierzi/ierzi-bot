import discord
from discord.ext import commands

import asyncio
import aiohttp
from aiogoogletrans import Translator
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os
from pathlib import Path
from pydantic import BaseModel
import random
from rich.console import Console
from typing import Optional

console = Console()
load_dotenv()

class WhatBeatsRockResponse(BaseModel):
    decision: bool
    reason: str

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.cat_vid_names: list[Path] = []
        self.car_vids_folder = Path(__file__).resolve().parent.parent / "car_vids"
        self.openai_api_key = os.getenv("OPENAI_KEY")
        self.fetch_cat_vids()

    @commands.command()
    async def istrans(self, ctx: commands.Context, user: discord.Member = None):
        """https://amitrans.org/"""
        if user is None:
            user = ctx.author
        
        if user.id in [966351518020300841, 1399689963284467723]: #apex, ierzi and the bot
            await ctx.send("no")
            return
        if user.id == [902148645753856020, 1153301933231181824]: #maja, apex
            await ctx.send("yes")
            return
        if user.id == 1206615811792576614: #fa*t
            await ctx.send("yes, transfem. yes, fact she/her is real. yes, this message is personalized just for her <33")
            return
        
        await ctx.send(random.choice(["no", "yes"]))
    
    @commands.command()
    async def isgay(self, ctx: commands.Context, user: discord.Member = None):
        """https://www.amigay.org/"""
        if user is None:
            user = ctx.author
        
        if user.id == 1399689963284467723: #the bot
            await ctx.send("no")
            return
        if user.id in [
            1279666598441123840, 1120940924910977064, 955623247725072476, 747918143745294356, 
            893298676003393536, 980436567531335700, 730885117656039466, 1220973198875693156, 966351518020300841    
            ]: # way too many people (including me)
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["no", "yes"]))
    
    @commands.command(aliases=("gaytector",))
    async def gaydar(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        """Sends a percentage based on how gay someone is."""
        if user is None:
            user = ctx.author
        
        if user.id in [
            747918143745294356, # ludwig
            893298676003393536, # guest
            902296627325317150, # masternigwardofthefifth (long ass name)
            1259095685207425036, # winter (old)
            1245098829116866560, #winter (new)
            ]: 
            await ctx.send(f"{user.mention} is 100% gay! 🌈", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == 1399689963284467723: #the bot
            await ctx.send("0%")
            return
        
        percentage = random.randint(0, 100)

        await ctx.send(f"{user.mention} is {percentage}% gay! 🌈", allowed_mentions=discord.AllowedMentions.none())


    @commands.command()
    async def isrich(self, ctx: commands.Context, user: discord.Member = None):
        """no"""
        if user is None:
            user = ctx.author
        
        if user.id in [1206615811792576614, 1344010392506208340, 902296627325317150]: #fa*t
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["yes", "no"]))

    @commands.command()
    async def ishomophobic(self, ctx: commands.Context, user: discord.Member = None):
        """i hope not?? :sob:"""
        if user is None:
            user = ctx.author
        
        if user.id in [1206615811792576614, 1344010392506208340]: #fa*t
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["yes", "no"]))
    
    @commands.command()
    async def islesbian(self, ctx: commands.Context, user: discord.Member = None):
        """women loves women"""
        if user is None:
            user = ctx.author
        
        if user.id in [1387497689259835563, 1076823281442754652, 953630995830165514, 1206615811792576614, 1344010392506208340]: #ace (both accounts), syndey (lmao) and fa*t (both accounts)
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["yes", "no"]))

    @commands.command()
    async def roll(self, ctx: commands.Context, sides: int = 6):
        """Roll a dice."""
        roll = random.randint(1, sides)
        await ctx.send(f"You rolled a {roll}")

    @commands.command()
    async def d20(self, ctx: commands.Context):
        """Dice 20"""
        roll = random.randint(1, 20)
        await ctx.send(f"{roll}")
    
    @commands.command()
    async def coinflip(self, ctx: commands.Context):
        """Flip a coin."""
        result = random.choice(["heads", "tails"])
        await ctx.send(result)
    
    @commands.command()
    async def hello(self, ctx: commands.Context):
        """hiiii"""
        await ctx.send(random.choice(["hi", "hello", "fuck you"]))
    
    @commands.command(name="2ball")
    async def twoball(self, ctx: commands.Context):
        """8ball but only 2 options, yes and no."""
        result = random.choice(["yes", "no"])
        await ctx.send(result)

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def guessnumber(self, ctx: commands.Context, guess: int):
        """Guess the number between 0 and 10000."""
        number = random.randint(0, 10000)
        if number == guess:
            await ctx.send(f"Congrats {ctx.author.mention}, you guessed the right number {number}!")
            return
        
        await ctx.send("no.")

    @commands.command()
    async def cat(self, ctx: commands.Context):
        """Shows a cute cat picture :3"""
        request_url = "https://api.thecatapi.com/v1/images/search"

        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as r:
                r = await r.json()
        
        cat_url = r[0]['url']

        embed = discord.Embed(
            title="Meow :3", 
            color=discord.Color.yellow()
        )
        embed.set_image(url=cat_url)
        await ctx.send(embed=embed)

    def fetch_cat_vids(self):   
        for video in self.car_vids_folder.glob("*.mp4"):
            self.cat_vid_names.append(video)

    @commands.command()
    async def catvid(self, ctx: commands.Context):
        """Shows a cute cat video :3"""
        random_video = random.choice(self.cat_vid_names)
        await ctx.send(file=discord.File(random_video.resolve()))
    
    @commands.command()
    async def pi(self, ctx: commands.Context, digits: int):
        """Pi digits."""
        headers = {
            "accept": "application/json"
        }
        url = f"https://api.math.tools/numbers/pi?to={digits}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                json_data = await response.json()
        
        console.print(json_data)
        try:
            if json_data['error']:
                await ctx.send("error :(")
                return
        except KeyError: # no error
            pass

        pi = json_data['cotents']['result'] # Cotents???
        splits = []
        if digits > 1980:
            current_split = ""
            for char in pi:
                current_split += char
                if len(current_split) == 1980:
                    splits.append(current_split)
                    current_split = ""
            
        if splits:
            for split in splits:
                await ctx.send(split)
                await asyncio.sleep(0.2)
            return
        
        await ctx.send(pi)

    @commands.command(name="tr")
    async def hypertranslate(self, ctx: commands.Context):
        """Hypertranslate a text."""
        # Get the reply
        reply = ctx.message.reference
        if reply is None:
            await ctx.send("You didn't reply to a message.")
            return
        
        reply = await ctx.channel.fetch_message(reply.message_id)
        text = reply.content

        # Hypertranslate
        translator = Translator()
        languages = [
            "ha", "so", "zu", "st", "xh", "mg", "mi", "sm", "haw", "uz", "ku", 
            "eu", "mt", "is", "cy", "gl", "et", "lv", "lt", "ht", "su", "jw"
        ]

        current_translation = text
        async with ctx.typing():
            translations = random.sample(languages, 15)
            for language in translations:
                response = await translator.translate(current_translation, language)
                current_translation = response.text
            
            # Back to english
            response = await translator.translate(current_translation, "en")
            current_translation = response.text

        await ctx.message.reply(current_translation, allowed_mentions=discord.AllowedMentions.none())


    @commands.command()
    async def ship(self, ctx: commands.Context, user1: str | discord.User, user2: str | discord.User):
        """Ship two users."""

        user1 = user1.mention if isinstance(user1, discord.User) else user1
        user2 = user2.mention if isinstance(user2, discord.User) else user2

        # Hardcoded ships
        hardcoded_ships = {
            (980436567531335700, 976276627346559017): 100, # eddgow and roob
            (1245098829116866560, 1220973198875693156): 100, # winter and epik
        }

        if (user1, user2) in hardcoded_ships:
            ship_percentage = hardcoded_ships[(user1, user2)]
        elif (user2, user1) in hardcoded_ships:
            ship_percentage = hardcoded_ships[(user2, user1)]
        else:
            ship_percentage = random.randint(0, 100)

        emoji = "💘" if ship_percentage >= 80 else "❤️" if ship_percentage >= 33 else "💔"

        await ctx.send(f"{user1} X {user2}: {ship_percentage}% {emoji}", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command(aliases=("wbr",))
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def whatbeatsrock(self, ctx: commands.Context): # TODO: maybe add a leaderboard
        """like the game on the website"""
        # Uses AI to answer
        schema = {
            "type": "object",
            "properties": {
                "decision": {"type": "boolean", "description": "True if the suggested item beats the previous one, false otherwise."},
                "reason": {"type": "string", "description": "A brief explanation of why the suggested item does or does not beat the previous one."}
            },
            "required": ["decision", "reason"]
        }

        answers = ["rock"] # User answers
        what_beats = "rock"

        # Game loop
        while True:
            # Bottom line is the answers so far
            bottom_line = " → ".join(list(reversed(answers))) if answers != ["rock"] else "Start"
            await ctx.send(f"What beats **{what_beats}**? Type '-stop' to end the game. \n-# {bottom_line}")

            def check(m: discord.Message):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=90)
            except asyncio.TimeoutError:
                await ctx.send("Game timed out.")
                return
            
            if msg.content.lower() == "-stop":
                await ctx.send("Game ended.")
                return
            
            answers.append(msg.content)
            old_item = what_beats
            what_beats = msg.content

            # No repeats
            if what_beats in answers[:-1]:
                await ctx.send(f"❌: You already said '{what_beats}'!\n**Game over!** \n-# Final sequence: {what_beats} ✗ {bottom_line if bottom_line != 'Start' else 'rock'}")
                return

            # AI decision
            async with ctx.typing():
                client = AsyncOpenAI(api_key=self.openai_api_key)
                response = await client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are playing a game where the user suggests items that beat the previous item. You must decide if the user's suggestion is valid or not."
                        },
                        {
                            "role": "user",
                            "content": (
                                f"The current item is '{old_item}'. "
                                f"The user suggests '{what_beats}' as the next item. "
                                "Does this item logically beat the previous one?"
                            )
                        }
                    ],

                    functions=[
                        {
                            "name": "what_beats_rock_response",
                            "description": "Determines if the suggested item beats the previous item.",
                            "parameters": schema
                        }
                    ]
                )

                raw_args = response.choices[0].message.function_call.arguments
                data = WhatBeatsRockResponse.model_validate_json(raw_args)

            if data.decision:
                await ctx.send(f"✅: {data.reason}")
            else:
                await ctx.send(f"❌: {data.reason}\n**Game over!** \n-# Final sequence: {what_beats} ✗ {bottom_line if bottom_line != 'Start' else 'rock'}")
                return


