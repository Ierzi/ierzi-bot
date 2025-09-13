import discord
from discord.ext import commands
from rich.console import Console
import random
import asyncio
from pathlib import Path
from utils import pronouns

class Reactions(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.assets_folder = Path(__file__).resolve().parent.parent / "assets"

    @commands.command()
    async def kiss(self, ctx: commands.Context, user: discord.Member):
        """Kiss someone."""
        all_pronouns = pronouns.get_pronoun(ctx.author.id)
        if user == ctx.author:
            await ctx.send(f"{ctx.author.mention} kisses {all_pronouns[4]}... that's a bit sad.", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            reaction = random.choice(["૮ ˶ᵔ ᵕ ᵔ˶ ა", ">/////<", "m- me? ._."])
            await ctx.send(reaction)
            return
        if user.bot:
            await ctx.send("ok what :broken_heart:")
            return
        
        await ctx.send(f"{ctx.author.mention} kisses {user.mention} ❤️", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def hug(self, ctx: commands.Context, user: discord.Member):
        """Hug someone."""
        all_pronouns = pronouns.get_pronoun(ctx.author.id)
        if user == ctx.author:
            await ctx.send(f"{ctx.author.mention} hugs {all_pronouns[4]} :sob: \n-# I'd argue that hugging a pillow is better.", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            await ctx.send("Hey I needed that hug... thank you <333")
            return
        if user.bot:
            await ctx.send("not only are you hugging a bot, but it's not even me? :pensive:")
            return
        await ctx.send(f"{ctx.author.mention} hugs {user.mention} 🤗", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def cuddle(self, ctx: commands.Context, user: discord.Member):
        """Cuddle someone."""
        if user == ctx.author:
            await ctx.send(f"{ctx.author.mention} ain't got anyone to cuddle (lonely ass)", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            if ctx.author.id == 966351518020300841:
                await ctx.send("awww... <333 \n-# why tf am i cuddling my bot")
                return
            await ctx.send("hell no, I don't cuddle with anyone but my owner <33")
            return
        if user.bot:
            await ctx.send("cuddling a bot? really? :broken_heart:")
            return
        
        await ctx.send(f"{ctx.author.mention} cuddles {user.mention} 🥰 \n-# so cutesy", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def slap(self, ctx: commands.Context, user: discord.Member):
        """Slap someone."""
        all_pronouns = pronouns.get_pronoun(ctx.author.id)
        if user == ctx.author:
            if ctx.author.id == 1153301933231181824:
                # im not even gonna send a message this is gonna piss her off
                return
            await ctx.send(f"this dumbass {ctx.author.mention} is slapping {all_pronouns[4]} smh my head", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            await ctx.send("fuck you")
            return
        if user.bot:
            await ctx.send(f"{ctx.author.mention} **SLAPS** {user.mention}! \n-# deserved icl cause im better", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == 1153301933231181824: # apex
            await ctx.send("no.")
            return
        
        await ctx.send(f"{ctx.author.mention} **SLAPS** {user.mention}!", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def kill(self, ctx: commands.Context, user: discord.Member):
        """Kill someone."""
        if user == ctx.author:
            if ctx.author.id == 1153301933231181824: #apex 
                await ctx.send(f"beat my time first")
                return
            await ctx.send(f"NOOOOOOOO DONT KILL YOURSELF {ctx.author.mention}", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            await ctx.send("why?? :(")
            return
        if user.bot:
            await ctx.send('why do you wanna kill a bot :sob: wait kill.. bot? gd reference?? \n-# i only made this command for this "joke" lmao')
            return
        if user.id == 1153301933231181824: # apex
            if ctx.author.id == 966351518020300841: #me
                # im the only one who can kill her
                await ctx.send(f"{ctx.author.mention} **KILLS** {user.mention}!! \n-# that's not nice", allowed_mentions=discord.AllowedMentions.none())
                return
            
            await ctx.send("no.")
            return
        
        await ctx.send(f"{ctx.author.mention} **KILLS** {user.mention}!! \n-# that's not nice", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def pat(self, ctx: commands.Context, user: discord.Member):
        """Pat someone's head."""
        if user == ctx.author:
            await ctx.send("why tf do you wanna pat yourself..")
            return
        if user.bot:
            await ctx.send("can you pick a real person??:sob:")
            return
        
        await ctx.send(f"{ctx.author.mention} pats {user.mention} 👏", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def flirt(self, ctx: commands.Context, user: discord.Member):
        """Flirt with someone."""
        if user == ctx.author:
            await ctx.send("how does that even work")
            return
        if user.id == self.bot.user.id:
            await ctx.message.add_reaction("❌")
            await asyncio.sleep(0.5)
            await ctx.message.reply("no.")
            return
        if user.bot:
            await ctx.send("vros NOT gonna flirt back :broken_heart:")
            return

        await ctx.send(f"{ctx.author.mention} flirts with {user.mention} 😘", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def punch(self, ctx: commands.Context, user: discord.Member):
        """Punch someone."""
        if user == ctx.author:
            if ctx.author.id == 1153301933231181824:
                await ctx.send("btw you're the only one not allowed to punch yourself")
                return
            
            all_pronouns = pronouns.get_pronoun(ctx.author.id)
            await ctx.send(f"{ctx.author.mention} PUNCHES {all_pronouns[4]}!", allowed_mentions=discord.AllowedMentions.none())
            return

        if user.id == self.bot.user.id:
            what_file = self.assets_folder / "what.jpg"
            await ctx.send(file=discord.File(what_file.resolve()))
            return
        if user.bot:
            await ctx.send(f"{ctx.author.mention} PUNCHES {user.mention}! \n-# deserved icl cause im the best bot here")
            return
        if user.id == 1153301933231181824: # apex
            await ctx.message.add_reaction("❌")
            return
        
        await ctx.send(f"{ctx.author.mention} PUNCHES {user.mention}!! \n-# that's not nice", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def feed(self, ctx: commands.Context, user: discord.Member):
        """Feed someone."""
        food_emoji = random.choice(["🥫", "🍲", "🍛", "🍅", "🍜", "🍔", "🥗", "🫔", "🥑", "🥪", "🥖 (baguette)", "🥩", "🌯", "🍟", "🍕", "🌭", "🥙", "🍗"]) #why is there so many food emojis
        all_pronouns = pronouns.get_pronoun(ctx.author.id)
        if user == ctx.author:
            await ctx.send(f"{ctx.author.mention} feeds {all_pronouns[4]} 😋{food_emoji}", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            await ctx.send("no thanks.")
            return
        if user.bot:
            await ctx.send(f"{ctx.author.mention} feeds.. the bot? or something? idfk", allowed_mentions=discord.AllowedMentions.none())
            return
        
        await ctx.send(f"{ctx.author.mention} feeds {user.mention} 😋{food_emoji}", allowed_mentions=discord.AllowedMentions.none())