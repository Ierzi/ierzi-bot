import discord
from discord import Embed, Message
from discord.ext import commands
from discord.ui import View, Button

from cogs.utils.variables import VIEW_TIMEOUT

from .utils.database import db
from .utils.functions import to_ordinal, to_timestamp, parse_offset, tz_to_str
from .utils.types import Birthday

import aiohttp
import asyncio
import certifi
from datetime import datetime, timedelta
import random
from rich.console import Console
from typing import Optional, Union
import ssl
from zoneinfo import ZoneInfo

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

class WorldDateTime(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
    
    # groups!!!

    # Birthday
    @commands.group(name="birthday", aliases=("bday", "bd"))
    async def birthday(self, ctx: commands.Context):
        """Birthday commands."""
        if ctx.invoked_subcommand is None:
            return
        
    # Timezone
    @commands.group(name='timezone', aliases=("tz",))
    async def timezone(self, ctx: commands.Context):
        """Timezone commands."""
        if ctx.invoked_subcommand is None:
            return
    
    # Helper functions
    async def _set_birthday(self, user_id: int, birthday: Birthday):
        """Set the birthday of a user."""
        await db.execute(
            "INSERT INTO users (user_id, day, month, year) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id) DO UPDATE SET day = $2, month = $3, year = $4",
            user_id, birthday.day, birthday.month, birthday.year
        )
    
    async def _get_birthday(self, user_id: int) -> Optional[Birthday]:
        """Get the birthday of a user."""
        row = await db.fetchrow("SELECT day, month, year FROM users WHERE user_id = $1", user_id)
        if row is None:
            return None
        
        return Birthday(row["day"], row["month"], row["year"])

    async def _total_birthdays(self) -> int:
        """Return total number of birthdays stored in the database."""
        count = await db.fetchval("SELECT COUNT(*) FROM users WHERE day IS NOT NULL;")
        return int(count or 0)


    async def _get_pp_events(self, dt: datetime) -> list:
        """Gets events from pronouns.page."""
        # Convert datetime to yyyy-mm-dd
        date_str = dt.strftime("%Y-%m-%d")
        url = f"https://en.pronouns.page/api/calendar/{date_str}"
        self.console.print(url)

        timeout = aiohttp.ClientTimeout(total=10)
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=ssl_context)) as client:
            async with client.get(url, headers={"User-Agent": "ierzi-bot/1.0"}) as request:
                request.raise_for_status()
                response: dict = await request.json()
                self.console.print(response)

        return response.get("events", [])
    
    async def _get_otd_events(self, dt: datetime, many: int, random_events: bool = False) -> list:
        """Gets events from On This Day API."""
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        timeout = aiohttp.ClientTimeout(total=10)
        url = f"https://api.ontoday.info/api/v1/events/{dt.month}/{dt.day}"
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                    async with session.get(url, headers={"User-Agent": "ierzi-bot/1.0"}) as request:
                        request.raise_for_status()
                        response: dict = await request.json()
                        self.console.print(response)
                        break
            except Exception as e:
                self.console.print(f"OTD fetch attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    self.console.print("OTD fetch failed after retries.")
                    return []

        events: list[dict] = response.get("data", {}).get("Events", [])
        event_names = [event.get("text") for event in events]
        if random_events:
            return [random.choice(event_names)] if event_names else []
        return event_names[:many]
    
    async def _get_events(self, dt: datetime) -> list:
        """Gets events from different sources."""
        return await self._get_pp_events(dt) + await self._get_otd_events(dt, 5, random_events=True)

    async def _set_timezone(self, user_id: int, timezone: str):
        """Set the timezone of a user."""
        await db.execute(
            "INSERT INTO users (user_id, timezone) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET timezone = EXCLUDED.timezone",
            user_id, timezone
        )
    
    async def _get_timezone(self, user_id: int) -> Optional[str]:
        """Get the timezone of a user."""
        row = await db.fetchrow("SELECT timezone FROM users WHERE user_id = $1", user_id)
        if row is None:
            return None
        
        return row["timezone"]

        
    # Commands!
    @commands.command(name="et", aliases=("events-today", "events", "event"))
    async def events_today(self, ctx: commands.Context):
        """Gets events today."""
        now = datetime.now()
        try:
            events = await self._get_events(now)
        except Exception as e:
            await ctx.send("error :(")
            self.console.print(f"Error fetching events: {e}")
            return

        today_embed = Embed(
            colour=6016762, # transgender blue
            title=f"Today - {now.day}/{now.month}/{now.year}",
            description="**Events today:**\n\n"
        )

        if not events:
            today_embed.description += "No events today."
            await ctx.send(embed=today_embed)
            return
        
        for event in events:
            today_embed.description += f"- {event}\n"
        
        await ctx.send(embed=today_embed)

    # Birthday Commands
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
        birthdays = await db.fetch("SELECT user_id, day, month FROM users WHERE month = $1 AND day = $2", today.month, today.day)
        if not birthdays:
            await ctx.send("No one's birthday today.")
            return
        
        birthday_users: list[discord.User] = []
        for birthday in birthdays:
            birthday_users.append(await self.bot.fetch_user(birthday["user_id"]))

        await ctx.send(f"{len(birthday_users)} person(s) have a birthday today: {', '.join([user.mention for user in birthday_users])}", allowed_mentions=discord.AllowedMentions.none())
    
    @birthday.command()
    async def month(self, ctx: commands.Context, month: Union[int, str]):
        """Lists all birthdays in a given month."""
        if isinstance(month, int) and (month < 1 or month > 12):
            await ctx.send("Month must be between 1 and 12")
            return
        
        if isinstance(month, str):
            try:
                month = MONTHS.index(month.capitalize()) + 1
            except Exception:
                await ctx.send("invalid month")
        
        birthdays = await db.fetch("SELECT user_id, day, month FROM users WHERE month = $1", month)
        if not birthdays:
            await ctx.send("No one's birthday in this month.")
            return
        
        birthday_users: list[discord.User] = []
        for birthday in birthdays:
            birthday_users.append(await self.bot.fetch_user(birthday["user_id"]))
        
        await ctx.send(f"{len(birthday_users)} person(s) have a birthday in this month: {', '.join([user.mention for user in birthday_users])}", allowed_mentions=discord.AllowedMentions.none())

    @birthday.command()
    async def thismonth(self, ctx: commands.Context):
        """Lists all birthdays coming this month."""
        current_month_index = datetime.now().month
        birthdays = await db.fetch("SELECT user_id, day, month FROM users WHERE month = $1", current_month_index)
        if not birthdays:
            await ctx.send("No one's birthday in this month.")
            return
        
        birthday_users: list[discord.User] = []
        for birthday in birthdays:
            birthday_users.append(await self.bot.fetch_user(birthday["user_id"]))
        
        await ctx.send(f"{len(birthday_users)} person(s) have a birthday in this month: {', '.join([user.mention for user in birthday_users])}", allowed_mentions=discord.AllowedMentions.none())

    @birthday.command()
    async def list(self, ctx: commands.Context, page_number: int = 1):
        """Lists all birthdays."""
        async with ctx.typing():
            birthdays = await db.fetch("SELECT user_id, day, month FROM users ORDER BY month, day ASC LIMIT 10 OFFSET $1", (page_number - 1) * 10)
            if not birthdays:
                await ctx.send("There's a whopping 0 users on this page.")
                return
            
            birthday_users: list[tuple[discord.User, int, int]] = []
            for birthday in birthdays:
                user = await self.bot.fetch_user(birthday["user_id"])
                birthday_users.append((user, birthday["day"], birthday["month"]))
            
            bday_embed = Embed(
                title=f"Birthdays - Page {page_number}",
                description="",
                color=discord.Colour.gold()
            )
            for user, day, month in birthday_users:
                bday_embed.description += f"{user.mention} - {MONTHS[month - 1]} {to_ordinal(day)}\n"
        
        await ctx.send(embed=bday_embed)

    @birthday.command()
    async def total(self, ctx: commands.Context):
        """Gives the number of birthdays stored in the database."""
        n = await self._total_birthdays()
        await ctx.send(f"There is a total of {n} birthdays registered in the database.")

    @birthday.command(aliases=("fsb",))
    @commands.is_owner()
    async def force_set_birthday(self, ctx: commands.Context, user: discord.User, day: int, month: Union[int, str], year: Optional[int] = None):
        """Force set a user's birthday. Can only be used by bot owners."""
        if isinstance(month, str):
            month = MONTHS.index(month.capitalize()) + 1
        
        birthday = Birthday(day, month, year)
        await self._set_birthday(user.id, birthday)
        await ctx.send(f"{user.mention}'s birthday has been set to {birthday}.", allowed_mentions=discord.AllowedMentions.none())
    
    # Timezone commands
    @timezone.command(name="set")
    async def set_timezone(self, ctx: commands.Context):
        """Set your timezone."""
        # Pre-load buttons
        buttons_view = View(timeout=VIEW_TIMEOUT)
        yes_button = Button(label="Yes", style=discord.ButtonStyle.green)
        no_button = Button(label="No", style=discord.ButtonStyle.red)

        async def yes_callback(interaction: discord.Interaction):
            await interaction.response.send_message(f"Your timezone has been set to {stored_tz}")
            await self._set_timezone(ctx.author.id, stored_tz)

        async def no_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Your timezone has not been changed.")

        yes_button.callback = yes_callback
        no_button.callback = no_callback
        buttons_view.add_item(yes_button)
        buttons_view.add_item(no_button)

        def check(m: Message):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            await ctx.send("Enter the name of your timezone or your UTC offset.")
            offset = await self.bot.wait_for("message", check=check, timeout=180)
            if offset.content.isnumeric() or offset.content.startswith("UTC"):
                offset = parse_offset(offset.content)
            else:
                offset = ZoneInfo(offset.content)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond.")
            return

        tz_str = tz_to_str(offset)

        if isinstance(offset, ZoneInfo):
            stored_tz = offset.key
        else:
            utcoffset = offset.utcoffset(datetime.now()) or timedelta(0)
            hours = int(utcoffset.total_seconds() // 3600)
            stored_tz = f"UTC{hours:+d}"

        dt = datetime.now(offset)
        await ctx.send(f"Is it currently {dt.hour}:{dt.minute} in {tz_str}?", view=buttons_view)
        # Everything else is handled by the buttons
    
    @timezone.command(name="get")
    async def get_timezone(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Get a user's timezone."""
        if not user:
            user = ctx.author
        
        tz = await self._get_timezone(user.id)
        if not tz:
            await ctx.send(
                f"{user.mention} doesn't have a timezone set. Use `!timezone set` to set one." if user != ctx.author else "You don't have a timezone set. Use `!timezone set` to set one.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        try:
            tzinfo = parse_offset(tz)
        except Exception as e:
            await ctx.send("error :(")
            self.console.print(f"Error parsing timezone {tz}: {e}")
            return

        dt = datetime.now(tzinfo)
        await ctx.send(
            f"{user.mention}'s timezone is {tz}. It is currently {dt.hour}:{dt.minute} there.",
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def update_wdt_tables():
    # Drop old table
    await db.execute("DROP TABLE IF EXISTS birthdays;")

    await db.execute("""
        ALTER TABLE users
        ADD COLUMN day SMALLINT NULL,
        ADD COLUMN month SMALLINT NULL,
        ADD COLUMN year SMALLINT NULL,
        ADD COLUMN timezone VARCHAR(50) NULL;
    """)
