import discord
from discord.ext import commands
from rich.console import Console
import random

console = Console()

class Reactions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.console = Console()

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
            ctx.send(f"{ctx.author.mention} hugs themselves :sob: \n-#I'd argue that hugging a pillow is better.", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            await ctx.send("Hey I needed that hug... thank you <333")
            return
        if user.bot:
            await ctx.send("not only are you hugging a bot, but it's not even me? :pensive:")
            return
        await ctx.send(f"{ctx.author.mention} hugs {user.mention} 🤗", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def slap(self, ctx: commands.Context, user: discord.Member):
        if user == ctx.author:
            await ctx.send(f"this dumbass {ctx.author.mention} is slapping himself smh my head", allowed_mentions=discord.AllowedMentions.none())
            return
        if user.id == self.bot.user.id:
            await ctx.send("fuck you")
            return
        if user.bot:
            await ctx.send(f"{ctx.author.mention} **SLAPS** {user.mention}! \n-#deserved icl cause im better", allowed_mentions=discord.AllowedMentions.none())
            return
        
        await ctx.send(f"{ctx.author.mention} **SLAPS** {user.mention}!", allowed_mentions=discord.AllowedMentions.none())


async def setup(bot: commands.Bot):
    await bot.add_cog(Reactions(bot))
    console.print("Reactions cog loaded.")