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
            await ctx.send(f"{ctx.author.mention} kisses themselves... that's a bit sad.")
            return
        if user.id == self.bot.user.id:
            reaction = random.choice(["૮ ˶ᵔ ᵕ ᵔ˶ ა", ">/////<", "m- me? ._."])
            await ctx.send(reaction)
            return
        if user.bot:
            await ctx.send("ok what :broken_heart:")
            return
        
        await ctx.send(f"{ctx.author.mention} kisses {user.mention} ❤️")

async def setup(bot: commands.Bot):
    await bot.add_cog(Reactions(bot))
    console.print("Reactions cog loaded.")