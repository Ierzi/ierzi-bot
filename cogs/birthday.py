import discord
from discord.ext import commands
from rich.console import Console
from typing import Optional, Union
from datetime import datetime
from .utils.database import db
from .utils.functions import to_timestamp
from .utils.pronouns import get_pronoun, PronounEnum
from .utils.types import Birthday 
from discord import Embed

MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]

class BirthdayCog(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        # Doing this differently 
        self.avaliable_commands = [
            "set",
            "get",
            "until",
            "since",
            "compare",
            "today",
            "month"
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
    async def set(self, ctx: commands.Context, day: int, month: Union[int, str], year: Optional[int] = None):
        """Set your birthday. (Day Month and optionally Year)"""
        if year is not None and year < 0:
            await ctx.send("you're so old cro")
            return
        
        if isinstance(month, str):
            month = MONTHS.index(month.capitalize()) + 1
        
        if day < 1 or day > 31:
            await ctx.send("Day must be between 1 and 31")
            return
        
        if month < 1 or month > 12:
            await ctx.send("Month must be between 1 and 12")
            return
        
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
    
    @birthday.command()
    async def until(self, ctx: commands.Context, user: Optional[discord.User] = None, month: Optional[Union[int, str]] = None):
        """Get the time until someone's birthday."""
        user_id = user.id if user else ctx.author.id

        birthday = await self._get_birthday(user_id)
        if birthday is None:
            await ctx.send(f"{user.mention} doesn't have a birthday set." if user else "You don't have a birthday set.", allowed_mentions=discord.AllowedMentions.none())
            return

        if isinstance(month, str):
            month = MONTHS.index(month.capitalize()) + 1

        today = datetime.now()
        birthday_date = datetime(today.year, birthday.month, birthday.day)
        
        user = user if user else ctx.author

        if birthday_date < today:
            # Birthday already passed this year, show next year's birthday
            timestamp = to_timestamp(birthday_date, "R", next_year=True)
        else:
            # Birthday hasn't passed this year yet
            timestamp = to_timestamp(birthday_date, "R")
        
        await ctx.send(f"{user.mention}'s birthday is {timestamp}.", allowed_mentions=discord.AllowedMentions.none())

    @birthday.command()
    async def since(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Get the time since someone's birthday."""
        user_id = user.id if user else ctx.author.id

        birthday = await self._get_birthday(user_id)
        if birthday is None:
            await ctx.send(f"{user.mention} doesn't have a birthday set." if user else "You don't have a birthday set.", allowed_mentions=discord.AllowedMentions.none())
            return
        
        user = user if user else ctx.author

        today = datetime.now()
        birthday_date = datetime(today.year, birthday.month, birthday.day)

        if birthday_date > today:
            # Birthday hasn't happened this year yet, show last year's birthday
            timestamp = to_timestamp(birthday_date, "R", previous_year=True)
        else:
            # Birthday already happened this year
            timestamp = to_timestamp(birthday_date, "R")

        await ctx.send(f"{user.mention}'s birthday was {timestamp}.", allowed_mentions=discord.AllowedMentions.none())

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

    @birthday.command()
    async def today(self, ctx: commands.Context):
        """Anyone's birthday today?"""
        today = datetime.now()
        birthdays = await db.fetch("SELECT user_id, day, month FROM birthdays WHERE month = $1 AND day = $2", today.month, today.day)
        if not birthdays:
            await ctx.send("No one's birthday today.")
            return
        
        birthday_users = []
        for birthday in birthdays:
            birthday_users.append(await self.bot.fetch_user(birthday["user_id"]))

        await ctx.send(f"{len(birthday_users)} person(s) have a birthday today: {', '.join([user.mention for user in birthday_users])}", allowed_mentions=discord.AllowedMentions.none())
    
    @birthday.command()
    async def month(self, ctx: commands.Context, month: Union[int, str]):
        """Lists all birthdays in a given month."""
        if month < 1 or month > 12:
            await ctx.send("Month must be between 1 and 12")
            return
        
        if isinstance(month, str):
            month = MONTHS.index(month.capitalize()) + 1
        
        birthdays = await db.fetch("SELECT user_id, day, month FROM birthdays WHERE month = $1", month)
        if not birthdays:
            await ctx.send("No one's birthday in this month.")
            return
        
        birthday_users = []
        for birthday in birthdays:
            birthday_users.append(await self.bot.fetch_user(birthday["user_id"]))
        
        await ctx.send(f"{len(birthday_users)} person(s) have a birthday in this month: {', '.join([user.mention for user in birthday_users])}", allowed_mentions=discord.AllowedMentions.none())

    @birthday.command()
    async def list(self, ctx: commands.Context, page_number: int = 1):
        """Lists all birthdays."""

        birthdays = await db.fetch("SELECT user_id, day, month FROM birthdays ORDER BY month, day ASC LIMIT 10 OFFSET $1", (page_number - 1) * 10)
        if not birthdays:
            await ctx.send("No one has a birthday.")
            return
        
        birthday_users = []
        for birthday in birthdays:
            user = await self.bot.fetch_user(birthday["user_id"])
            birthday_users.append((user, birthday["day"], birthday["month"]))
        
        bday_embed = Embed(
            title="Birthdays",
            description="",
            color=discord.Colour.gold()
        )
        for user, day, month in birthday_users:
            bday_embed.description += f"{user.mention} - {day}/{month}\n"
        
        await ctx.send(embed=bday_embed)

    @birthday.command(aliases=("fsb",))
    async def force_set_birthday(self, ctx: commands.Context, user: discord.User, day: int, month: Union[int, str], year: Optional[int] = None):
        """Force set a user's birthday. Can only be used by Ierzi."""
        if ctx.author.id != 966351518020300841:
            await ctx.send("no.")
            return
        
        if isinstance(month, str):
            month = MONTHS.index(month.capitalize()) + 1
        
        birthday = Birthday(day, month, year)
        await self._set_birthday(user.id, birthday)
        await ctx.send(f"{user.mention}'s birthday has been set to {birthday}.", allowed_mentions=discord.AllowedMentions.none())
    