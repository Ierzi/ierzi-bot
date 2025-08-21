import discord
from discord.ext import commands
from rich.console import Console
import psycopg2
import os

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
    
    async def get_balance(self, user_id: int) -> int:
        self.cur.execute("SELECT balance FROM economy WHERE user_id = %s", (user_id,))
        row = self.cur.fetchone()
        print(row)
        if row:
            return row[0]
        else:
            self.cur.execute("INSERT INTO economy (user_id, balance) VALUES (%s, %s)", (user_id, 0))
            self.conn.commit()
            return 0
    
    @commands.command
    async def balance(self, ctx: commands.Context, user: discord.Member = None):
        if not user:
            user = ctx.author

        console.print(user)
        
        balance = await self.get_balance(user.id)
        ctx.send(f"{user.mention} has {balance} coins.", allowed_mentions=discord.AllowedMentions.none())

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
    console.print("Economy cog loaded.")
