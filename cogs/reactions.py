import discord
from discord.ext import commands
from rich.console import Console
import random
import asyncio

class Reactions(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console

    @commands.command()
    async def kiss(self, ctx: commands.Context, user: discord.Member):
        if user == ctx.author:
            await ctx.send(f"{ctx.author.mention} kisses themselves... that's a bit sad.", allowed_mentions=discord.AllowedMentions.none())
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
        if user == ctx.author:
            await ctx.send(f"{ctx.author.mention} hugs themselves :sob: \n-# I'd argue that hugging a pillow is better.", allowed_mentions=discord.AllowedMentions.none())
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
        if user == ctx.author:
            await ctx.send(f"this dumbass {ctx.author.mention} is slapping himself smh my head", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            await ctx.send("fuck you")
            return
        if user.bot:
            await ctx.send(f"{ctx.author.mention} **SLAPS** {user.mention}! \n-# deserved icl cause im better", allowed_mentions=discord.AllowedMentions.none())
            return
        
        await ctx.send(f"{ctx.author.mention} **SLAPS** {user.mention}!", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def kill(self, ctx: commands.Context, user: discord.Member):
        if user == ctx.author:
            if ctx.author.id == 1153301933231181824: #apex 
                await ctx.send(f"hi pexie also no")
                return
            await ctx.send(f"NOOOOOOOO DONT KILL YOURSELF {ctx.author.mention}", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            await ctx.send("what did i do to you :pensive:")
            return
        if user.bot:
            await ctx.send("why do you wanna kill a bot :sob: wait kill.. bot? gd reference?? \n-# i only made this command for this message lmao")
            return
        if user.id == 1153301933231181824:
            if ctx.author.id == 966351518020300841: #me
                # im the only one who can kill her
                await ctx.send(f"{ctx.author.mention} **KILLS** {user.mention}!! \n-# that's not nice", allowed_mentions=discord.AllowedMentions.none())
                return
            
            await ctx.send("no.")
            return
        
        await ctx.send(f"{ctx.author.mention} **KILLS** {user.mention}!! \n-# that's not nice", allowed_mentions=discord.AllowedMentions.none())


