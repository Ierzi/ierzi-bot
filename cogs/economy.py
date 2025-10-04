# Imports
import discord
from discord.ext import commands
from rich.console import Console
from decimal import Decimal, getcontext
from typing import Literal, Optional
from datetime import timedelta, datetime, timezone

# Utils
from .utils.database import db

getcontext().prec = 2  # Set decimal precision to 2 for currency

COOLDOWN_TYPES = Literal["last_worked", "last_daily", "last_robbed_bank", "last_robbed_user"]
_hours = Optional[int]
_minutes = Optional[int]
_seconds = Optional[int]
_output_data = tuple[bool, _hours, _minutes, _seconds]

class Economy:
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.coin_emoji = '<:coins:1416429599084118239>'
    
    # Helper functions
    async def _get_balance(self, user_id: int) -> float:
        """Get the balance of a user."""
        row = await db.fetchrow("SELECT balance FROM economy WHERE user_id = $1", user_id)
        self.console.print(row)
        if row:
            return float(row["balance"])
        else:
            return 0.0
    
    async def _get_money_lost(self, user_id: int) -> float:
        """Get the total money lost by a user."""
        row = await db.fetchrow("SELECT money_lost FROM economy WHERE user_id = $1", user_id)
        if row:
            return float(row["money_lost"])
        else:
            return 0.0

    async def _add_money(self, user_id: int, amount: float):
        """Add money to a user."""
        current_balance = await self._get_balance(user_id)
        new_balance = Decimal(current_balance) + Decimal(amount)
        await db.execute("""
            INSERT INTO economy (user_id, balance) 
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET balance = $2
        """, user_id, new_balance)
        self.console.print(f"Added {amount} to user {user_id}. New balance: {new_balance}")
    
    async def _remove_money(self, user_id: int, amount: float):
        """Remove money from a user. This also updates the money_lost column."""
        current_balance = await self._get_balance(user_id)
        new_balance = Decimal(current_balance) - Decimal(amount)
        await db.execute("""
            INSERT INTO economy (user_id, balance, money_lost) 
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET balance = $2, money_lost = money_lost + $3
        """, user_id, new_balance, amount)
        self.console.print(f"Removed {amount} to user {user_id}. New balance: {new_balance}")
    
    async def _cooldown(
            user_id: int, 
            cooldown_type: COOLDOWN_TYPES,
            cooldown: timedelta
    ) -> _output_data:
        row = db.fetchrow(f"SELECT {cooldown_type} FROM economy WHERE user_id = $1", user_id)
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

    async def _update_cooldown(user_id: int, cooldown_type: COOLDOWN_TYPES) -> None:
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
            title=f"{member.mention}'s Economy Profile",
            color=discord.Color.gold()
        )
        embed.add_field(name="Balance", value=f"{self.coin_emoji} {balance:,.2f}", inline=False)
        embed.add_field(name="Total Money Lost", value=f"{self.coin_emoji} {money_lost:,.2f}", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

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
