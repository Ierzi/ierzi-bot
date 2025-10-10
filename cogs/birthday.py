import discord
from discord.ext import commands
from rich.console import Console
from typing import Optional
from datetime import datetime
from .utils.database import db
from .utils.functions import to_timestamp
from .utils.pronouns import get_pronoun, PronounEnum
from .utils.types import Birthday 

class BirthdayCog(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        # Doing this differently 
        self.avaliable_commands = [
            "set_dm",
            "set_md",
            "get",
            "time_until",
            "compare"
        ]
    
    # groups!!!
    @commands.group(name="birthday", aliases=("bday", "bd"))
    async def birthday(self, ctx: commands.Context):
        """Birthday commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Valid commands: {', '.join(self.avaliable_commands)}")
            return
    
    # Helper functions
    async def _set_birthday(self, user_id: int, birthday: Birthday):
        """Set the birthday of a user."""
        await db.execute(
            "INSERT INTO birthdays (user_id, day, month, year) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id) DO UPDATE SET day = $2, month = $3, year = $4",
            user_id, birthday.day, birthday.month, birthday.year
        )
    
    async def _get_birthday(self, user_id: int) -> Optional[Birthday]:
        """Get the birthday of a user."""
        row = await db.fetchrow("SELECT day, month, year FROM birthdays WHERE user_id = $1", user_id)
        if row is None:
            return None
        
        return Birthday(row["day"], row["month"], row["year"])

    # Commands
    @birthday.command()
    async def set(self, ctx: commands.Context, day: int, month: int, year: Optional[int] = None):
        """Set your birthday. (Day Month Year)"""
        user_id = ctx.author.id
        birthday = Birthday(day, month, year)
        await self._set_birthday(user_id, birthday)

        await ctx.send(f"Your birthday has been set to {birthday}.", allowed_mentions=discord.AllowedMentions.none())
    
    @birthday.command()
    async def get(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Get someone's birthday."""
        user_id = user.id if user else ctx.author.id
        p1 = await get_pronoun(user_id, PronounEnum.SUBJECT)

        birthday = await self._get_birthday(user_id)
        if birthday is None:
            await ctx.send(f"{user.mention} doesn't have a birthday set.", allowed_mentions=discord.AllowedMentions.none())
            return

        user = user if user else ctx.author

        await ctx.send(f"{user.mention}'s birthday is {birthday}.", allowed_mentions=discord.AllowedMentions.none())

        if birthday.year is not None:
            await ctx.send(f"{p1.capitalize()} was born in {birthday.year}.", allowed_mentions=discord.AllowedMentions.none())
    
    @birthday.command(aliases=("tu", "until"))
    async def time_until(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Get the time until someone's birthday."""
        user_id = user.id if user else ctx.author.id

        birthday = await self._get_birthday(user_id)
        if birthday is None:
            await ctx.send(f"{user.mention} doesn't have a birthday set." if user else "You don't have a birthday set.", allowed_mentions=discord.AllowedMentions.none())
            return

        today = datetime.now()
        birthday_date = datetime(today.year, birthday.month, birthday.day)
        
        user = user if user else ctx.author

        timestamp = to_timestamp(birthday_date, "R", next_year=True)
        await ctx.send(f"{user.mention}'s birthday is {timestamp}.", allowed_mentions=discord.AllowedMentions.none())


    @birthday.command()
    async def compare(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """Compare two users' birthdays."""
        birthday1 = await self._get_birthday(user1.id)
        birthday2 = await self._get_birthday(user2.id)

        if birthday1 is None:
            await ctx.send(f"{user1.mention} doesn't have a birthday set.", allowed_mentions=discord.AllowedMentions.none())
            return

        if birthday2 is None:
            await ctx.send(f"{user2.mention} doesn't have a birthday set.", allowed_mentions=discord.AllowedMentions.none())
            return
        
        if birthday1.day == birthday2.day and birthday1.month == birthday2.month:
            await ctx.send(f"{user1.mention} and {user2.mention} have the same birthday!", allowed_mentions=discord.AllowedMentions.none())
            return

        # Create datetime objects for this year to compare
        today = datetime.now()
        date1 = datetime(today.year, birthday1.month, birthday1.day)
        date2 = datetime(today.year, birthday2.month, birthday2.day)
        
        # Calculate days between birthdays
        if date1 < date2:
            days_diff = (date2 - date1).days
            await ctx.send(f"{user1.mention}'s birthday is {days_diff} days before {user2.mention}'s birthday.", allowed_mentions=discord.AllowedMentions.none())
        else:
            days_diff = (date1 - date2).days
            await ctx.send(f"{user2.mention}'s birthday is {days_diff} days before {user1.mention}'s birthday.", allowed_mentions=discord.AllowedMentions.none())
