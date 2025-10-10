import discord
from discord.ext import commands
from rich.console import Console
from typing import Optional
from datetime import datetime
from .utils.database import db
from .utils.functions import to_timestamp

# Updating the database
async def update_tables():
    await db.execute(
        """CREATE TABLE IF NOT EXISTS birthdays (
            user_id BIGINT PRIMARY KEY,
            day INT NOT NULL,
            month INT NOT NULL,
            year INT DEFAULT NULL
        )"""
    )

BirthdayData = tuple[int, int, Optional[int]] # day, month, year 

class Birthday(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        # Doing this differently 
        self.avaliable_commands = [
            "set_dm",
            "set_md",
            "get",
            "time_until"
        ]
    
    # groups!!!
    @commands.group(name="birthday", aliases=("bday", "bd"))
    async def birthday(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Valid commands: {', '.join(self.avaliable_commands)}")
            return
    
    # Helper functions
    async def _set_birthday(self, user_id: int, day: int, month: int, year: Optional[int] = None):
        """Set the birthday of a user."""
        await db.execute(
            "INSERT INTO birthdays (user_id, day, month, year) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id) DO UPDATE SET day = $2, month = $3, year = $4",
            user_id, day, month, year
        )
    
    async def _get_birthday(self, user_id: int) -> BirthdayData:
        """Get the birthday of a user."""
        row = await db.fetchrow("SELECT day, month, year FROM birthdays WHERE user_id = $1", user_id)
        if row is None:
            return None
        
        if row["year"] is None:
            return row["day"], row["month"], None
        
        return row["day"], row["month"], row["year"]

    # Commands
    @birthday.command(aliases=("set_dm", "dm"))
    async def set_day_month(self, ctx: commands.Context, day: int, month: int):
        """Set your birthday (Day Month)."""
        user_id = ctx.author.id
        await self._set_birthday(user_id, day, month)
    
    @birthday.command(aliases=("set_md", "md"))
    async def set_month_day(self, ctx: commands.Context, month: int, day: int):
        """Set your birthday (Month Day)."""
        user_id = ctx.author.id
        await self._set_birthday(user_id, day, month)

    @birthday.command()
    async def get(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Get someone's birthday."""
        user_id = user.id if user else ctx.author.id

        birthday = await self._get_birthday(user_id)
        if birthday is None:
            await ctx.send(f"{user.mention} doesn't have a birthday set.", allowed_mentions=discord.AllowedMentions.none())
            return

        await ctx.send(f"{user.mention}'s birthday is {birthday[0]}/{birthday[1]}.", allowed_mentions=discord.AllowedMentions.none())
    
    @birthday.command(aliases=("tu", "until"))
    async def time_until(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Get the time until someone's birthday."""
        user_id = user.id if user else ctx.author.id

        birthday = await self._get_birthday(user_id)
        if birthday is None:
            await ctx.send(f"{user.mention} doesn't have a birthday set." if user else "You don't have a birthday set.", allowed_mentions=discord.AllowedMentions.none())
            return

        today = datetime.now()
        birthday_date = datetime(today.year, int(birthday[1]), int(birthday[0]))
        
        timestamp = to_timestamp(birthday_date, "D")
        await ctx.send(f"{user.mention}'s birthday is {timestamp}.", allowed_mentions=discord.AllowedMentions.none())


