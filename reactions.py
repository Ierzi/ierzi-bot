import discord
from discord.ext import commands
from rich.console import Console

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
        
        await ctx.send(f"{ctx.author.mention} kisses {user.mention} ❤️")

async def setup(bot: commands.Bot):
    await bot.add_cog(Reactions(bot))
    console.print("Reactions cog loaded.")