import discord
from discord import Embed, Colour
from discord.ext import commands
from rich.console import Console
from cogs.utils.database import db
import os
import random
from datetime import datetime, timedelta, timezone
import asyncio
from typing import TypedDict, Literal, Optional
from .utils import pronouns

# -- Types

# Cooldown function
_output = bool
_hours = Optional[int]
_minutes = Optional[int]
_seconds = Optional[int]
output_data = tuple[_output, _hours, _minutes, _seconds]

# -- Variables

class ShopItem(TypedDict):
    name: str
    price: int
    description: str

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.db = db
        self.console = console
        self.coin_emoji = '<:coins:1416429599084118239>'

        # All the jobs and how much they pay
        self.jobs: list[tuple[str, int]] = [("McDonalds Employee", 250), ("Teacher", 500), ("Video Editor", 750), ("Chef", 1000), ("Music Producer", 1500), ("Software Developer", 2000), ("Nanotechnology Engineer", 3000)]

        # Shop
        #TODO
        self.shop_items: list[ShopItem] = [
            {'name': 'Banana', 'price': 100, 'description': 'useless item'}
        ]
        self.shop_item_names: list[str] = ['banana']

    # Helper functions
    async def get_balance(self, user_id: int) -> int:
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        if balance is not None:
            return int(balance)
        await db.execute("INSERT INTO users (user_id, balance) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING", user_id, 0)
        return 0
    
    async def cooldown(self, 
                       user_id: int, 
                       cooldown_type: Literal["last_worked", "last_daily", "last_robbed_bank", "last_robbed_user"],
                       cooldown_time: timedelta,
                       now: datetime
                       ) -> output_data:
        # All cooldowns are in the users table
        last_action = await db.fetchval(f"SELECT {cooldown_type} FROM users WHERE user_id = $1", user_id)
        if last_action is not None:
            # Normalize to naive UTC for subtraction compatibility
            if isinstance(last_action, str):
                last_action = datetime.fromisoformat(last_action)
            if getattr(last_action, "tzinfo", None) is not None:
                last_action = last_action.astimezone(timezone.utc).replace(tzinfo=None)
            
            if (now - last_action) < cooldown_time:
                time_remaining = cooldown_time - (now - last_action)

                hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)

                return False, hours, minutes, seconds
        
        return True, None, None, None


    async def add_money(self, user_id: int, amount: int):
        await db.execute(
            """
            INSERT INTO users (user_id, balance)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET balance = users.balance + EXCLUDED.balance;
            """,
            user_id,
            amount,
        )
        self.console.print(f"Successfully added {amount} coins to {user_id}")


    @commands.command(aliases=("bal",))
    async def balance(self, ctx: commands.Context, user: discord.Member = None):
        """Check your balance."""
        if not user:
            user = ctx.author

        balance = await self.get_balance(user.id)
        await ctx.send(f"{user.mention} has {balance} coins.", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def work(self, ctx: commands.Context):
        """Work to gain some coins."""
        user_id = ctx.author.id
        cooldown = timedelta(hours=6)
        now = datetime.utcnow()

        output = await self.cooldown(ctx.author.id, 'last_worked', cooldown, now)
        if not output[0]: # Cooldown
            hours, minutes, seconds = output[1:4]
            await ctx.send(f"You already worked! \nYou can work again in {hours} hours, {minutes} minutes and {seconds} seconds.")
            return

        # If the user can work, give them a random job and pay them
        job, raw_payment = random.choice(self.jobs)
        payment = random.randint(raw_payment - 50, raw_payment + 50) # randomize the payement
        await db.execute("""
            INSERT INTO users (user_id, balance, last_worked)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET balance = users.balance + EXCLUDED.balance, last_worked = EXCLUDED.last_worked;
        """, user_id, payment, now)
        await ctx.send(f"{ctx.author.mention} worked as a {job} and gained {payment} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name="ecolb", aliases=("lb", "leaderboard")) # since there's no other leaderboards
    @commands.cooldown(1, 5, commands.BucketType.user) # cause its a heavy command that freezes(?) the bot for a few seconds
    async def eco_leaderboard(self, ctx: commands.Context, page: int = 1):
        """View the economy leaderboard."""
        if page < 1:
            await ctx.send("Page must be 1 or higher.")
            return
        
        async with ctx.typing():
            offset = (page - 1) * 10
            rows = await db.fetch(
                """
                SELECT user_id, balance FROM users 
                ORDER BY balance DESC
                OFFSET $1
                LIMIT 10  
                """,
                offset,
            )
            if not rows:
                await ctx.send("No users found on this page.")
                return
            
            ecolb_embed = Embed(
                title=f"**Economy Leaderboard - Page {page:,}**",
                description=""
            )
            for i, rec in enumerate(rows):
                user_id = rec["user_id"] if hasattr(rec, "keys") else rec[0]
                balance = rec["balance"] if hasattr(rec, "keys") else rec[1]
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                ecolb_embed.description += f"**{i + 1 + (page * 10) - 10}. {user.mention}** - {self.coin_emoji} {balance:,} coins \n" 

        await ctx.send(embed=ecolb_embed, allowed_mentions=discord.AllowedMentions.none()) 

    @commands.command()
    async def daily(self, ctx: commands.Context): 
        """Get a daily reward."""
        user_id = ctx.author.id

        cooldown = timedelta(hours=24)
        now = datetime.utcnow()

        output = await self.cooldown(ctx.author.id, 'last_daily', cooldown, now)
        if not output[0]: # Cooldown
            hours, minutes, seconds = output[1:4]
            await ctx.send(f"You already claimed your daily! \nYou can claim it again in {hours} hours, {minutes} minutes and {seconds} seconds.")
            return

        payment = 12_500
        await db.execute("""
            INSERT INTO users (user_id, balance, last_daily)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET balance = users.balance + EXCLUDED.balance, last_daily = EXCLUDED.last_daily;
        """, user_id, payment, now)

        # Use pronouns

        all_pronouns = await pronouns.get_pronoun(user_id)

        await ctx.send(f"{ctx.author.mention} claimed {all_pronouns[2]} daily! +{payment:,} coins {self.coin_emoji}.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def pay(self, ctx: commands.Context, user: discord.Member, amount: int):
        """Pay someone."""
        balance = await self.get_balance(user.id)
        if amount < 0:
            await ctx.send("have you tried using coins that have a positive amount of atoms?")
            return
        if amount == 0:
            await ctx.send("wow so generous")
            return
        if user.id == ctx.author.id:
            await ctx.send("cro what")
            return
        if balance < amount:
            await ctx.send("pug is fixed")
            return
        
        author = ctx.author
        await self.add_money(user.id, amount)
        await self.add_money(author.id, -amount)
        await ctx.send(f"{author.mention} paid {user.mention} {amount} coins!", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.cooldown(1, 2, commands.BucketType.user)
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
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def dicebet(self, ctx: commands.Context, amount: int):
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

        # I dont wanna write my whole code again so guess is a fixed value
        guess = 2
        correct_side = random.randint(1, 6)
        prize = amount * 6
        if correct_side == guess:
            await ctx.send(f"You guessed the corect side! +{prize} coins.")
            await self.add_money(user_id, prize)
            return
        else:
            await ctx.send(f"You guessed the wrong side. -{amount} coins.")
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
            description=f"The prize money is {prize_money:,} coins {self.coin_emoji}. \nEach ticket costs {ticket_price} coins {self.coin_emoji}. \n\nWinning chance: {chance * 100}% \n\n**Reply with the amount of tickets you would like to buy (max 10).**",
            color=Colour.green()
        )
        await ctx.send(embed=lottery_embed)

        def check(m: discord.Message):
            return m.author.id == user_id and m.channel == ctx.channel and m.content.lower() in [str(i) for i in range(10)]
        
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
    
    # TODO: add cooldown fucntionality (2 hours for both)
    @commands.command(name="robbank")
    async def rob_bank(self, ctx: commands.Context):
        """Rob a bank (no way)."""
        rob_money = random.randint(1000, 2000)
        success = False
        user_id = ctx.author.id
        cooldown = timedelta(hours=2)
        now = datetime.utcnow()

        # Pronouns
        all_pronouns = await pronouns.get_pronoun(user_id)

        output = await self.cooldown(user_id, 'last_robbed_bank', cooldown, now)
        if not output[0]: # Cooldown
            hours, minutes, seconds = output[1:4]
            await ctx.reply(f"Try again in {hours} hours, {minutes} minutes and {seconds} seconds.")
            return

        # You have a 50% chance of robbing a bank.
        if random.random() < 0.5:
            await ctx.send(f"{ctx.author.mention} robbed the bank and won {rob_money} coins!", allowed_mentions=discord.AllowedMentions.none())
            await self.add_money(user_id, rob_money)
            success = True
        else:
            lose_money = rob_money // 2
            await ctx.send(f"🚨 The police caught {ctx.author.mention} and {all_pronouns[0]} lost {lose_money} coins...", allowed_mentions=discord.AllowedMentions.none())
            await self.add_money(user_id, -lose_money)
        
        await db.execute("""
            INSERT INTO users (user_id, balance, last_robbed_bank)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET balance = users.balance + EXCLUDED.balance, last_robbed_bank = EXCLUDED.last_robbed_bank;
        """, user_id, rob_money if success else 0, now)
    
    @commands.command(name="robuser")
    async def rob_user(self, ctx: commands.Context, user: discord.Member):
        """Rob someone 1000 coins. If you fail you give them 500 coins."""
        if not user:
            await ctx.send("who?")
            return
        if user.bot:
            await ctx.send('rob a real person vro')
            return
        
        balance = await self.get_balance(user.id)
        if balance < 1000:
            await ctx.send("pick someone else, cros too poor :broken_heart:")
            return
        
        user_id = ctx.author.id
        cooldown = timedelta(hours=2)
        now = datetime.now(timezone.utc)
        robbed_pronouns = await pronouns.get_pronoun(user.id)
        
        output = await self.cooldown(user_id, 'last_robbed_user', cooldown, now)
        if not output[0]: # Cooldown
            hours, minutes, seconds = output[1:4]
            await ctx.reply(f"Try again in {hours} hours, {minutes} minutes and {seconds} seconds.")
            return
        
        # You have a 33% chance of robbing someone
        # cause its not nice lmao (and you're also stealing a lot of money)
        if random.random() < 0.33:
            await ctx.send(f"{ctx.author.mention} robbed 1,000 coins from {user.mention}! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            await self.add_money(ctx.author.id, 1000)
            await self.add_money(user.id, -1000)
        else:
            await ctx.send(f"{ctx.author.mention} tried to rob {user.mention}, failed, and gave {robbed_pronouns[1]} 500 coins :broken_heart:", allowed_mentions=discord.AllowedMentions.none())
            await self.add_money(ctx.author.id, -500)
            await self.add_money(user.id, 500)
        
        # record last_robbed_user timestamp without changing balance further
        await db.execute("""
            INSERT INTO users (user_id, last_robbed_user)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET last_robbed_user = EXCLUDED.last_robbed_user;
        """, user_id, now)


    # @commands.command()
    # async def shop(self, ctx: commands.Context):
    #     """Shows all the items in the shop."""
    #     # I have no idea what to add so maybe a shop will help.
    #     # Do !buy to buy an item
    #     # This only shows the shop
    #     shop_embed = Embed(
    #         title="Shop",
    #         description="working on a shop rn, this is still a wip\n\n",
    #         color=Colour.green()
    #     )
    #     for shop_item in self.shop_items:
    #         shop_embed.description += f'{shop_item["name"]} - {shop_item["description"]} - {shop_item["price"]:,} coins.\n'
        
    #     await ctx.send(embed=shop_embed)
    
    # @commands.command()
    # async def buy(self, ctx: commands.Context, item: str):
    #     """Buy an item in the shop."""
    #     item_name = item.strip().lower()
    #     if item_name not in [name.lower() for name in self.shop_item_names]:
    #         await ctx.send("Item not in shop.")
    #         return
        
    #     # Get the item price
    #     shop_item = None
    #     for s_item in self.shop_items:
    #         if s_item["name"].lower() == item_name:
    #             shop_item = s_item
    #             break
        
    #     if shop_item is None:
    #         await ctx.send("error???")
    #         return

    #     price = shop_item["price"]
    #     user_id = ctx.author.id
    #     balance = await self.get_balance(user_id)
    #     if balance < price:
    #         await ctx.send("check ur balance cro :broken_heart:")
    #         return

    #     await self.add_money(user_id, -price)
    #     await self.update_items(user_id, shop_item["name"], 1)
    #     await ctx.send(f"You bought 1 {shop_item['name']} for {price} coins!")

    # async def fetch_inv(self, user_id: int):
    #     self.cur.execute("SELECT item, amount FROM items WHERE user_id = %s", (user_id,))
    #     rows = self.cur.fetchall()
    #     return rows

    # @commands.command(aliases=("inv",))
    # async def inventory(self, ctx: commands.Context):
    #     """See the items in your inventory."""
    #     inventory_embed = Embed(
    #         title=ctx.author.display_name,
    #         description="",
    #         color=Colour.blue()
    #     )
    #     inv = await self.fetch_inv(ctx.author.id)
    #     for item in inv:
    #         inventory_embed.description += f"{item[0]} - {item[1]}\n"
        
    #     await ctx.send(embed=inventory_embed)

    @commands.command()
    async def give_money(self, ctx: commands.Context, user: discord.Member | int, amount: int):
        """Spawns money out of thin air and gives it to someone. Can only be used by Ierzi, obviously."""
        # user or user id 
        if ctx.author.id != 966351518020300841:
            await ctx.send("To use this command you need 1e308 cash. You do not have this much money and so cannot use this command.")
            return
        if not user:
            await ctx.send("who?")
            return
        if not amount:
            await ctx.send("how much?")
            return
        
        if isinstance(user, discord.Member):
            await self.add_money(user.id, amount)
            await ctx.send(f"Successfully added {amount} coins to {user.mention}'s account. {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            return
        
        if isinstance(user, int):
            # user id
            await self.add_money(user, amount)
            profile = self.bot.get_user(user) or await self.bot.fetch_user(user)
            await ctx.send(f"Successfully added {amount} coins to {profile.mention}'s account. {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            return
