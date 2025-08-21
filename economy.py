import discord
from discord.ext import commands
from rich.console import Console
import psycopg2
import os
import random

console = Console()

conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)

cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS economy (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE NOT NULL,
        balance BIGINT DEFAULT 0
    );
""")

conn.commit()
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
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx: commands.Context): 
        job = random.choice(self.jobs)
        await ctx.send(f"You worked as a {job[0]} and gained {job[1]} coins!")
        await self.add_money(ctx.author.id, job[1])

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
