import discord
from discord.ext import commands
from rich.console import Console
import psycopg2
import os
import random
from datetime import datetime, timedelta, timezone

console = Console()

conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)

cur = conn.cursor()

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.conn = conn
        self.cur = cur
        self.console = console

        # All the jobs and how much they pay
        self.jobs: list[tuple[str, int]] = [("McDonalds Employee", 100), ("Teacher", 300), ("Video Editor", 300), ("Chef", 500), ("Music Producer", 500), ("Software Developer", 750), ("Nanotechnology Engineer", 900)]
    
    async def get_balance(self, user_id: int) -> int:
        self.cur.execute("SELECT balance FROM economy WHERE user_id = %s", (user_id,))
        row = self.cur.fetchone()
        if row:
            return row[0]
        else:
            self.cur.execute("INSERT INTO economy (user_id, balance) VALUES (%s, %s)", (user_id, 0))
            self.conn.commit()
            return 0
    
    async def add_money(self, user_id: int, amount: int):
        cur.execute("""
            INSERT INTO economy (user_id, balance)
            VALUES (%s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET balance = economy.balance + EXCLUDED.balance;
        """, (user_id, amount)
        )
        conn.commit() #lowk had no idea how to make this so i asked chatgpt
        console.print(f"Successfully added {amount} coins to {user_id}")


    @commands.command()
    async def balance(self, ctx: commands.Context, user: discord.Member = None):
        if not user:
            user = ctx.author

        balance = await self.get_balance(user.id)
        await ctx.send(f"{user.mention} has {balance} coins.", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def work(self, ctx: commands.Context): 
        # Gets the last time the user worked
        user_id = ctx.author.id
        cur.execute("SELECT last_worked FROM economy WHERE user_id = %s", (user_id,))
        last_worked = timedelta(cur.fetchone()[0])

        cooldown = timedelta(hours=6)
        now = datetime.now(timezone.utc)

        if now - last_worked < cooldown:
            remaining: timedelta = cooldown - (now - last_worked)
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.send(f"You already worked! \nYou can work in {hours} hours, {minutes} minutes and {seconds} seconds")
            return 
        
        job, raw_payement = random.choice(self.jobs)
        payement = random.randint(raw_payement - 50, raw_payement + 50)
        cur.execute("""
                    INSERT INTO economy (user_id, balance, last_daily) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET balance = economy.balance + EXLCUDED.balance, last_daily = EXCLUDED.last_daily;
        """, (user_id, payement, now))
        conn.commit()

        await ctx.send(f"{ctx.author.mention} worked as a {job} and gained {payement} coins!", allowed_mentions=discord.AllowedMentions.none())

    # @commands.command(name="ecolb")
    # async def eco_leaderboard():

    @commands.command()
    async def daily(self, ctx: commands.Context): ...

    @commands.command()
    async def give_money(self, ctx: commands.Context, user: discord.Member, amount: int):
        if ctx.author.id != 966351518020300841:
            await ctx.send("no.")
            return
        if not user:
            await ctx.send("who?")
            return
        if not amount:
            await ctx.send("how much?")
            return
        
        await self.add_money(user.id, amount)
        await ctx.send(f"Successfully added {amount} coins to {user.mention}'s account", allowed_mentions=discord.AllowedMentions.none())

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
    console.print("Economy cog loaded.")
