import discord
from discord import Embed, Colour
from discord.ext import commands
from rich.console import Console
import psycopg2
import os
import random
from datetime import datetime, timedelta, timezone
import asyncio

conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)

cur = conn.cursor()


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
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
        self.console.print(f"Successfully added {amount} coins to {user_id}")


    @commands.command()
    async def balance(self, ctx: commands.Context, user: discord.Member = None):
        """Check your balance."""
        if not user:
            user = ctx.author

        balance = await self.get_balance(user.id)
        await ctx.send(f"{user.mention} has {balance} coins.", allowed_mentions=discord.AllowedMentions.none())
    
    #TODO: fix this
    @commands.command()
    async def work(self, ctx: commands.Context):
        """Work to gain some coins."""
        user_id = ctx.author.id
        self.cur.execute("SELECT last_worked FROM economy WHERE user_id = %s", (user_id,))
        row = self.cur.fetchone()
        self.console.print(row)

        cooldown = timedelta(hours=6)
        now = datetime.now(timezone.utc)

        # * now is a datetime object, row[0] is a datetime object or None, and cooldown is a timedelta object

        # If the user has worked before, send a message saying how long until they can work again
        if row and row[0] is not None:
            # if row is none, user has never worked before, so they can work now
            # so if row is not none, user has worked before, so check if they can work again
            last_worked: datetime = row[0]
            # Ensure last_worked is timezone-aware
            if last_worked.tzinfo is None:
                last_worked = last_worked.replace(tzinfo=timezone.utc) # I have no fucking clue why !work doesnt work so i asked chatgpt IM SORRY IM SORRYYYY 

            if (now - last_worked) < cooldown: 
                # if now - last_worked is less than the cooldown, (for example, user worked 2 hours ago and 2 < 6)
                # they can't work yet
                # calculate the remaining time
                # (i really gotta put this many comments cause im so lost :sob:)
                time_remaining = cooldown - (now - last_worked) # example: 6 hours - (17:00  - 15:00) = 4 hours remaining
                # now just put the time into readable shit
                hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
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
        """View the economy leaderboard."""
        if page < 1:
            await ctx.send("Page must be 1 or higher.")
            return
        
        async with ctx.typing():
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
            
            ecolb_embed = Embed(
                title=f"**Economy Leaderboard - Page {page:,}**",
                description=""
            )
            for i, (user_id, balance) in enumerate(rows):
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                ecolb_embed.description += f"**{i + 1}. {user.mention}** - {balance:,} coins \n" 

        await ctx.send(embed=ecolb_embed, allowed_mentions=discord.AllowedMentions.none()) 

    @commands.command()
    async def daily(self, ctx: commands.Context): 
        """Get a daily reward."""
        user_id = ctx.author.id
        self.cur.execute("SELECT last_daily FROM economy WHERE user_id = %s", (user_id,))
        row = self.cur.fetchone()
        self.console.print(row)

        cooldown = timedelta(hours=24)
        now = datetime.now(timezone.utc)

        # * now is a datetime object, row[0] is a datetime object or None, and cooldown is a timedelta object

        # If the user has claimed his daily before, send a message saying how long until they can claim it again
        if row and row[0] is not None:
            # if row is none, user has never claimed his daily before, so they can claim it now
            # so if row is not none, user has claimed it before, so check if they can claim it again
            last_daily: datetime = row[0]

            if last_daily.tzinfo is None:
                last_daily = last_daily.replace(tzinfo=timezone.utc)

            self.console.print(now - last_daily)
            self.console.print((now - last_daily) < cooldown)
            if (now - last_daily) < cooldown: 
                # if now - last_daily is less than the cooldown, (for example, user claimed 2 hours ago and 2 < 6)
                # they can't work yet
                # calculate the remaining time
                time_remaining = cooldown - (now - last_daily) 
                self.console.print(time_remaining)
                # now just put the time into readable shit
                hours, remainder = divmod(int(round(time_remaining.total_seconds())), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.console.print(f"time shit {hours, minutes, seconds}")
                await ctx.send(f"You already claimed your daily! \nYou can claim it in {hours} hours, {minutes} minutes and {seconds} seconds.")
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
    async def pay(self, ctx: commands.Context, user: discord.Member, amount: int):
        """Pay someone."""
        if amount < 0:
            await ctx.send("have you tried using coins that have a positive amount of atoms?")
            return
        if amount == 0:
            await ctx.send("wow so generous")
            return
        if user.id == ctx.author.id:
            await ctx.send("cro what")
            return
        
        author = ctx.author
        await self.add_money(user.id, amount)
        await self.add_money(author.id, -amount)
        await ctx.send(f"{author.mention} paid {user.mention} {amount} coins!", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def double(self, ctx: commands.Context, amount: int):
        """Gamble your coins with a chance to double them."""
        user_id = ctx.author.id
        balance = await self.get_balance(user_id)

        if amount < 0:
            await ctx.send("You doubled your money! +-Infinity coins.")
            return
        if amount > balance:
            await ctx.send("You're too poor cro :broken_heart:")
            return
        if amount == 0:
            await ctx.send("You lost your money! -Infinity coins. \n-# skill issue icl")
            return
        
        if random.choice([False, True]):
            await self.add_money(user_id, amount)
            await ctx.send(f"You doubled your money! +{amount} coins.")
            return
        else:
            await self.add_money(user_id, -amount)
            await ctx.send(f"You lost your money! -{amount} coins. \n-# skill issue icl")
            return
    
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dicebet(self, ctx: commands.Context, amount: int, guess: int):
        """Roll a 6 sided dice, guess the correct side to win."""
        user_id = ctx.author.id
        balance = await self.get_balance(user_id)
        if amount < 0:
            ctx.send("gambling your debts?")
            return
        if amount > balance:
            await ctx.send("check your balance again")
            return
        if amount == 0:
            await ctx.send("if you just wanna roll a dice use !roll :broken_heart:")
            return

        correct_side = random.randint(1, 6)
        prize = amount * 6
        if correct_side == guess:
            await ctx.send(f"You guessed the corect side! +{prize} coins.")
            await self.add_money(user_id, prize)
            return
        else:
            await ctx.send(f"-{amount} coins. The correct side was {correct_side}")
            await self.add_money(user_id, -amount)
            return

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def lottery(self, ctx: commands.Context):
        """Participate in the lottery."""
        prize_money = round(random.randint(1000000, 9999999), -3)
        ticket_price = 125 if prize_money > 4999999 else 100
        chance = 0.001275 # 0.1275% chance
        user_id = ctx.author.id
        user_balance = await self.get_balance(user_id)

        lottery_embed = Embed(
            title="Lottery",
            description=f"The prize money is {prize_money:,} coins. \nEach ticket costs {ticket_price} coins. \n\nWinning chance: {chance * 100}% \n\n**Reply with the amount of tickets you would like to buy (max 10).**",
            color=Colour.green()
        )
        await ctx.send(embed=lottery_embed)

        def check(m: discord.Message):
            return m.author.id == user_id and m.channel == ctx.channel and m.content.lower() in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        
        try:
            message = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Timed out.")
            return
        
        n_tickets = int(message.content)
        cost = n_tickets * ticket_price
        
        if cost > user_balance:
            await ctx.send("you're too poor cro :broken_heart:")
            return
        
        await self.add_money(user_id, -cost)

        if n_tickets == 1:
            if random.random() < chance:
                await ctx.send(f"**You won {prize_money:,} coins!!!**")
                await self.add_money(user_id, prize_money)
                return
            else:
                await ctx.send(f"You didn't win {prize_money:,} coins.")
                return

        # multiple tickets
        win = False
        for _ in range(1, n_tickets):
            if random.random() < chance:
                win = True
        
        if win:
            await ctx.send(f"**You won {prize_money:,} coins!!!**")
            await self.add_money(user_id, prize_money)
            return
        else:
            await ctx.send(f"You bought {cost:,} worth of tickets and didn't win {prize_money:,} coins.")
            return
    # @commands.command()
    # async def test_randomness(self, ctx: commands.Context):
    #     """a debug command to test random.choice randomness"""
    #     opt_1 = 0
    #     opt_2 = 0
    #     for _ in range(100):
    #         choice = random.choice([True, False])
    #         if choice:
    #             opt_1 += 1
    #         else:
    #             opt_2 += 1
        
    #     await ctx.send(f"Test 1 results: {opt_1} option 1, {opt_2} option 2.")
        
    #     opt_1 = 0
    #     opt_2 = 0
    #     for _ in range(100):
    #         choice = random.choice([False, True])
    #         if choice:
    #             opt_1 += 1
    #         else:
    #             opt_2 += 1
        
    #     await ctx.send(f"Test 2 results: {opt_1} option 1, {opt_2} option 2.")

    @commands.command()
    async def give_money(self, ctx: commands.Context, user: discord.Member, amount: int):
        """Spawns money out of thin air and gives it to someone. Can only be used by Ierzi, obviously."""
        if ctx.author.id != 966351518020300841:
            await ctx.send("To use this command you need 1e308 cash. You do not have this much money and so cannot use this command.")
            return
        if not user:
            await ctx.send("who?")
            return
        if not amount:
            await ctx.send("how much?")
            return
        
        await self.add_money(user.id, amount)
        await ctx.send(f"Successfully added {amount} coins to {user.mention}'s account.", allowed_mentions=discord.AllowedMentions.none())
