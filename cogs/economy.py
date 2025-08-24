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
    
    #TODO: fix this

    @commands.command()
    async def work(self, ctx: commands.Context):
        user_id = ctx.author.id
        self.cur.execute("SELECT last_worked FROM economy WHERE user_id = %s", (user_id,))
        row = self.cur.fetchone()
        console.print(row)

        cooldown = timedelta(hours=6)
        now = datetime.now(timezone.utc)

        # * now is a datetime object, row[0] is a datetime object or None, and cooldown is a timedelta object

        # If the user has worked before, send a message saying how long until they can work again
        if row and row[0] is not None:
            # if row is none, user has never worked before, so they can work now
            # so if row is not none, user has worked before, so check if they can work again
            last_worked = datetime(row[0])
            # Ensure last_worked is timezone-aware
            if last_worked.tzinfo is None:
                last_worked = last_worked.replace(tzinfo=timezone.utc) # I have no fucking clue why !work doesnt work so i asked chatgpt IM SORRY IM SORRYYYY 

            if now - last_worked < cooldown: 
                # if now - last_worked is less than the cooldown, (for example, user worked 2 hours ago and 2 < 6)
                # they can't work yet
                # calculate the remaining time
                # (i really gotta put this many comments cause im so lost :sob:)
                time_remaining = cooldown - (now - last_worked) # example: 6 hours - (17:00  - 15:00) = 4 hours remaining
                # now just put the time into readable shit
                hours, remainder = divmod(int(round(time_remaining.total_seconds())), 3600)
                minutes, seconds = divmod(remainder, 60)
                await ctx.send(f"You already worked! \nYou can work in {hours} hours, {minutes} minutes and {seconds} seconds.")
                return

        # If the user can work, give them a random job and pay them
        job, raw_payment = random.choice(self.jobs)
        payment = random.randint(raw_payment - 50, raw_payment + 50) # randomize the payement
        self.cur.execute("""
            INSERT INTO economy (user_id, balance, last_worked)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET balance = economy.balance + EXCLUDED.balance, last_worked = EXCLUDED.last_worked;
        """, (user_id, payment, now)
        )
        conn.commit()
        await ctx.send(f"{ctx.author.mention} worked as a {job} and gained {payment} coins!", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name="ecolb")
    async def eco_leaderboard(self, ctx: commands.Context, page: int = 1):
        if page < 1:
            await ctx.send("Page must be 1 or higher.")
            return
        
        offset = (page - 1) * 10
        self.cur.execute("""
            SELECT user_id, balance FROM economy 
            ORDER BY balance DESC
            OFFSET %s
            LIMIT 10  
        """, (offset,)
        )
        rows = self.cur.fetchall()
        if not rows:
            await ctx.send("No users found on this page.")
            return
        
        message = f"**Economy Leaderboard - Page {page}** \n"
        for i, (user_id, balance) in enumerate(rows):
            user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
            message += f"**{i + 1}. {user.mention}** - {balance} coins \n" 

        await ctx.send(message, allowed_mentions=discord.AllowedMentions.none()) 

    @commands.command()
    async def daily(self, ctx: commands.Context): 
        user_id = ctx.author.id
        self.cur.execute("SELECT last_daily FROM economy WHERE user_id = %s", (user_id,))
        row = self.cur.fetchone()
        console.print(row)

        cooldown = timedelta(hours=6)
        now = datetime.now(timezone.utc)

        # * now is a datetime object, row[0] is a datetime object or None, and cooldown is a timedelta object

        # If the user has claimed his daily before, send a message saying how long until they can claim it again
        if row and row[0] is not None:
            # if row is none, user has never claimed his daily before, so they can claim it now
            # so if row is not none, user has claimed it before, so check if they can claim it again
            last_daily = datetime(row[0])

            if last_daily.tzinfo is None:
                last_daily = last_daily.replace(tzinfo=timezone.utc)

            if now - last_daily < cooldown: 
                # if now - last_daily is less than the cooldown, (for example, user claimed 2 hours ago and 2 < 6)
                # they can't work yet
                # calculate the remaining time
                time_remaining = cooldown - (now - last_daily) 
                # now just put the time into readable shit
                hours, remainder = divmod(int(round(time_remaining.total_seconds(), 0)), 3600)
                minutes, seconds = divmod(remainder, 60)
                await ctx.send(f"You already claimed your daily! \nYou can work in {hours} hours, {minutes} minutes and {seconds} seconds.")
                return

        # If the user can work, give them a random job and pay them
        payment = 1250
        self.cur.execute("""
            INSERT INTO economy (user_id, balance, last_daily)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET balance = economy.balance + EXCLUDED.balance, last_daily = EXCLUDED.last_daily;
        """, (user_id, payment, now)
        )
        conn.commit()
        await ctx.send(f"{ctx.author.mention} claimed his daily! +{payment} coins.", allowed_mentions=discord.AllowedMentions.none())


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
