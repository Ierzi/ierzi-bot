# Imports
import discord
from discord.ext import commands
from rich.console import Console
from typing import Literal, Optional
from datetime import timedelta, datetime, timezone
import random

# Utils
from .utils.database import db
from .utils.types import Currency

_hours = Optional[int]
_minutes = Optional[int]
_seconds = Optional[int]
_output_data = tuple[bool, _hours, _minutes, _seconds]

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.coin_emoji = '<:coins:1416429599084118239>'

        self.jobs = [
            ("Retail Worker", 40.00, 100.00),
            ("Barista", 50.00, 120.00),
            ("Teacher", 70.00, 180.00),
            ("Artist", 70.00, 200.00),
            ("Content Creator", 80.00, 210.00),
            ("Writer", 80.00, 240.00),
            ("Musician", 90.00, 270.00),
            ("Graphic Designer", 100.00, 250.00),
            ("Doctor", 150.00, 300.00),
            ("Software Developer", 150.00, 300.00),
            ("Lawyer", 180.00, 350.00),
            ("CEO", 250.00, 500.00)
        ]
    
    # Helper functions
    async def _get_balance(self, user_id: int) -> Currency:
        """Get the balance of a user."""
        row = await db.fetchrow("SELECT balance FROM economy WHERE user_id = $1", user_id)
        if row:
            return Currency(row["balance"])
        else:
            return 0.0
    
    async def _get_money_lost(self, user_id: int) -> Currency:
        """Get the total money lost by a user."""
        row = await db.fetchrow("SELECT money_lost FROM economy WHERE user_id = $1", user_id)
        if row:
            return Currency(row["money_lost"])
        else:
            return 0.0

    async def _get_items(self, user_id: int) -> list:
        """Get the items of a user."""
        row = await db.fetchrow("SELECT items FROM economy WHERE user_id = $1", user_id)
        if row:
            return row["items"]
        else:
            return []

    async def _add_money(self, user_id: int, amount: float):
        """Add money to a user."""
        current_balance = await self._get_balance(user_id)
        new_balance = Currency(current_balance) + Currency(amount)
        await db.execute("""
            INSERT INTO economy (user_id, balance) 
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET balance = $2
        """, user_id, new_balance)
        self.console.print(f"Added {amount} to user {user_id}. New balance: {new_balance}")
    
    async def _remove_money(self, user_id: int, amount: float):
        """Remove money from a user. This also updates the money_lost column."""
        current_balance = await self._get_balance(user_id)
        new_balance = Currency(current_balance) - Currency(amount)
        await db.execute("""
            INSERT INTO economy (user_id, balance, money_lost) 
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET balance = $2, money_lost = money_lost + $3
        """, user_id, new_balance, amount)
        self.console.print(f"Removed {amount} to user {user_id}. New balance: {new_balance}")

    async def _set_balance(self, user_id: int, amount: float):
        """Set the balance of a user."""
        float_amount = float(f"{amount:.2f}")
        await db.execute("""
            INSERT INTO economy (user_id, balance) 
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET balance = $2
        """, user_id, float_amount)
        self.console.print(f"Set balance of user {user_id} to {amount}.")

    async def _set_money_lost(self, user_id: int, amount: float):
        """Set the money_lost of a user."""
        float_amount = float(f"{amount:.2f}")
        await db.execute("""
            INSERT INTO economy (user_id, money_lost) 
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET money_lost = $2
        """, user_id, float_amount)
        self.console.print(f"Set money_lost of user {user_id} to {amount}.")

    async def _cooldown(
            self,
            user_id: int, 
            cooldown_type: Literal["last_worked", "last_daily", "last_robbed_bank", "last_robbed_user"],
            cooldown: timedelta
        ) -> _output_data:
        """Check if a user is on cooldown for a specific action."""
        row = await db.fetchrow(f"SELECT {cooldown_type} FROM economy WHERE user_id = $1", user_id)
        if row is None or row[cooldown_type] is None:
            return (True, None, None, None)

        last_used: datetime = row[cooldown_type]
        now = datetime.now(tz=timezone.utc)

        if now - last_used >= cooldown:
            return (True, None, None, None)
        
        remaining = (last_used + cooldown) - now
        hours, remainder = divmod(remaining.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return (False, int(hours), int(minutes), int(seconds))

    async def _update_cooldown(
            self,
            user_id: int, 
            cooldown_type: Literal["last_worked", "last_daily", "last_robbed_bank", "last_robbed_user"]
        ) -> None:
        """Update the cooldown for a specific action."""
        now = datetime.now(tz=timezone.utc)
        await db.execute(f"""
            INSERT INTO economy (user_id, {cooldown_type}) 
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET {cooldown_type} = $2
        """, user_id, now)

    # Commands
    @commands.command(name="ecoprofile", aliases=("balance", "bal"))
    async def eco_profile(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """See your or someone else's economy profile."""
        if member is None:
            member = ctx.author
        
        balance = await self._get_balance(member.id)
        money_lost = await self._get_money_lost(member.id)

        embed = discord.Embed(
            title=f"{member.display_name}'s Economy Profile",
            color=discord.Color.gold()
        )
        embed.add_field(name="Balance", value=f"{self.coin_emoji} {balance:,.2f}", inline=False)
        embed.add_field(name="Total Money Lost", value=f"{self.coin_emoji} {money_lost:,.2f}", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    async def work(self, ctx: commands.Context):
        """Work and gain some coins."""
        user_id = ctx.author.id
        cooldown = timedelta(hours=6)

        output = await self._cooldown(user_id, "last_worked", cooldown)
        if not output[0]:
            hours, minutes, seconds = output[1], output[2], output[3]
            await ctx.send(f"You already worked! Try again in {hours}h {minutes}m {seconds}s.")
            return

        job = random.choice(self.jobs)
        job_name, min_pay, max_pay = job
        pay = random.uniform(min_pay, max_pay)

        await self._add_money(user_id, pay)
        await self._update_cooldown(user_id, "last_worked")
        await ctx.send(f"You worked as a **{job_name}** and earned {pay:,.2f} coins! {self.coin_emoji}")


async def _update_tables():
    # Just remaking the database schema lmao
    # Max balance is 999,999,999,999.99

    # jst delete the table and remake it
    await db.execute("DROP TABLE IF EXISTS economy")

    await db.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                balance numeric(15, 2) NOT NULL DEFAULT 0.00,
                money_lost numeric(15, 2) NOT NULL DEFAULT 0.00,

                last_daily TIMESTAMPTZ,
                last_worked TIMESTAMPTZ,
                last_robbed_bank TIMESTAMPTZ,
                last_robbed_user TIMESTAMPTZ,

                items JSONB NOT NULL DEFAULT '[]'::JSONB
                );
    """)
    # Remove old columns (see schema.sql)
    await db.execute("""ALTER TABLE users DROP COLUMN IF EXISTS balance""")
    await db.execute("""ALTER TABLE users DROP COLUMN IF EXISTS last_daily""")
    await db.execute("""ALTER TABLE users DROP COLUMN IF EXISTS last_worked""")
    await db.execute("""ALTER TABLE users DROP COLUMN IF EXISTS last_robbed_bank""")
    await db.execute("""ALTER TABLE users DROP COLUMN IF EXISTS last_robbed_user""")

    # Also since this is an old bot, add the new collumns
    await db.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS pronouns TEXT""")
