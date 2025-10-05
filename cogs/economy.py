# Imports
import discord
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput
from discord import SelectOption
from rich.console import Console
from typing import Literal, Optional
from datetime import timedelta, datetime, timezone
import random
import asyncio

# Utils
from .utils.database import db
from .utils.types import Currency
from .utils.pronouns import get_pronoun, PronounEnum

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
            return Currency.none()
    
    async def _get_money_lost(self, user_id: int) -> Currency:
        """Get the total money lost by a user."""
        row = await db.fetchrow("SELECT money_lost FROM economy WHERE user_id = $1", user_id)
        if row:
            return Currency(row["money_lost"])
        else:
            return Currency.none()

    async def _get_items(self, user_id: int) -> list:
        """Get the items of a user."""
        row = await db.fetchrow("SELECT items FROM economy WHERE user_id = $1", user_id)
        if row:
            return row["items"]
        else:
            return []

    async def _set_items(self, user_id: int, items: list) -> None:
        """Set the items of a user."""
        await self._ensure_user_exists(user_id)
        await db.execute("""
            UPDATE economy 
            SET items = $2
            WHERE user_id = $1
        """, user_id, items)

    async def _ensure_user_exists(self, user_id: int) -> None:
        """Ensure the user exists in the database."""
        # First ensure user exists in users table (which economy references)
        await db.execute("""
            INSERT INTO users (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id)
        
        # Then ensure user exists in economy table
        await db.execute("""
            INSERT INTO economy (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id)

    async def _add_money(self, user_id: int, amount: float):
        """Add money to a user."""
        await self._ensure_user_exists(user_id)
        current_balance = await self._get_balance(user_id)
        new_balance = Currency(current_balance) + Currency(amount)
        float_balance = float(new_balance)
        await db.execute("""
            UPDATE economy 
            SET balance = $2
            WHERE user_id = $1
        """, user_id, float_balance)
        self.console.print(f"Added {amount} to user {user_id}. New balance: {new_balance}")
    
    async def _remove_money(self, user_id: int, amount: float):
        """Remove money from a user. This also updates the money_lost column."""
        await self._ensure_user_exists(user_id)
        current_balance = await self._get_balance(user_id)
        new_balance = Currency(current_balance) - Currency(amount)
        float_balance = float(new_balance)
        await db.execute("""
            UPDATE economy 
            SET balance = $2,
                money_lost = money_lost + $3
            WHERE user_id = $1
        """, user_id, float_balance, amount)
        self.console.print(f"Removed {amount} from user {user_id}. New balance: {new_balance}")

    async def _set_balance(self, user_id: int, amount: float):
        """Set the balance of a user."""
        await self._ensure_user_exists(user_id)
        float_amount = float(Currency(amount))
        await db.execute("""
            UPDATE economy 
            SET balance = $2
            WHERE user_id = $1
        """, user_id, float_amount)
        self.console.print(f"Set balance of user {user_id} to {amount}.")

    async def _set_money_lost(self, user_id: int, amount: float):
        """Set the money_lost of a user."""
        await self._ensure_user_exists(user_id)
        float_amount = float(Currency(amount))
        await db.execute("""
            UPDATE economy 
            SET money_lost = $2
            WHERE user_id = $1
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
        await self._ensure_user_exists(user_id)
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
            color=discord.Colour.gold()
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
        await ctx.send(f"{ctx.author.mention} worked as a **{job_name}** and earned {pay:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def daily(self, ctx: commands.Context):
        """Claim your daily coins."""
        user_id = ctx.author.id
        cooldown = timedelta(hours=24)
        p_pronoun = await get_pronoun(ctx.author.id, data_returned=PronounEnum.POSSESSIVE)

        output = await self._cooldown(user_id, "last_daily", cooldown)
        if not output[0]:
            hours, minutes, seconds = output[1], output[2], output[3]
            await ctx.send(f"You already claimed your daily! Try again in {hours}h {minutes}m {seconds}s.")
            return

        daily_amount = 2500
        await self._add_money(user_id, daily_amount)
        await self._update_cooldown(user_id, "last_daily")
        await ctx.send(f"{ctx.author.mention} claimed {p_pronoun} daily! {daily_amount:,} coins {self.coin_emoji}!", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def robbank(self, ctx: commands.Context):
        """Attempt to rob a bank."""
        user_id = ctx.author.id

        cooldown = timedelta(hours=2)

        output = await self._cooldown(user_id, "last_robbed_bank", cooldown)
        if not output[0]:
            hours, minutes, seconds = output[1], output[2], output[3]
            await ctx.send(f"You already tried to rob a bank! Try again in {hours}h {minutes}m {seconds}s.")
            return
        
        success_chance = 0.3  # 30% chance of success
        await self._update_cooldown(user_id, "last_robbed_bank")
        if random.random() < success_chance:
            amount_stolen = random.uniform(500, 1500)
            await self._add_money(user_id, amount_stolen)
            await ctx.send(f"{ctx.author.mention} robbed a bank and got away with {amount_stolen:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            fine = random.uniform(100, 1000)
            await self._remove_money(user_id, fine)
            await ctx.send(f"{ctx.author.mention} got caught and had to pay a fine of {fine:,.2f} coins...", allowed_mentions=discord.AllowedMentions.none())

    async def robuser(self, ctx: commands.Context, member: discord.Member):
        """Rob someone."""
        user_id = ctx.author.id
        if user_id == member.id:
            await ctx.send("cro what")
            return
        
        if member.bot:
            await ctx.send("imagine being that desperate for money")
            return

        cooldown = timedelta(hours=2)

        output = await self._cooldown(user_id, "last_robbed_user", cooldown)
        if not output[0]:
            hours, minutes, seconds = output[1], output[2], output[3]
            await ctx.send(f"You already tried to rob someone! Try again in {hours}h {minutes}m {seconds}s.")
            return
        
        target_balance = await self._get_balance(member.id)
        if target_balance.to_float() < 100:
            await ctx.send(f"{member.mention} doesn't have enough money to be robbed.", allowed_mentions=discord.AllowedMentions.none())
            return

        success_chance = 0.3  # 30% chance of success
        await self._update_cooldown(user_id, "last_robbed_user")
        if random.random() < success_chance:
            amount_stolen = random.uniform(0.1 * target_balance.to_float(), 0.3 * target_balance.to_float())
            await self._remove_money(member.id, amount_stolen)
            await self._add_money(user_id, amount_stolen)
            await ctx.send(f"{ctx.author.mention} successfully robbed {member.mention} and stole {amount_stolen:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            fine = random.uniform(100, 500)
            await self._remove_money(user_id, fine)
            await ctx.send(f"{ctx.author.mention} got caught trying to rob {member.mention} and had to pay a fine of {fine:,.2f} coins...", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name="ecolb", aliases=("lb", "leaderboard", "baltop"))
    async def eco_leaderboard(self, ctx: commands.Context, page: int = 1):
        """See the economy leaderboard."""
        if page < 1:
            await ctx.send("whar?")
            return
        
        per_page = 10
        offset = (page - 1) * per_page

        async def get_balance_leaderboard() -> Optional[discord.Embed]:
            rows = await db.fetch("""
                SELECT user_id, balance FROM economy 
                ORDER BY balance DESC 
                LIMIT $1 OFFSET $2
            """, per_page, offset)

            if not rows:
                await ctx.send("There's a whopping 0 users on this page.")
                return
            
            embed = discord.Embed(
                title=f"Economy Balance Leaderboard - Page {page}",
                color=discord.Colour.gold()
            )
            description = ""
            rank = offset + 1
            for row in rows:
                user = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(row["user_id"])
                user_name = user.mention
                balance = Currency(row["balance"])
                description += f"**{rank}. {user_name}** - {self.coin_emoji} {balance:,.2f}\n"
                rank += 1
            
            embed.description = description

            return embed

        async def get_money_lost_leaderboard():
            rows = await db.fetch("""
                SELECT user_id, money_lost FROM economy 
                ORDER BY money_lost DESC 
                LIMIT $1 OFFSET $2
            """, per_page, offset)

            if not rows:
                await ctx.send("There's a whopping 0 users on this page.")
                return
            
            embed = discord.Embed(
                title=f"Economy Money Lost Leaderboard - Page {page}",
                color=discord.Colour.gold()
            )
            description = ""
            rank = offset + 1
            for row in rows:
                user = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(row["user_id"])
                user_name = user.mention
                money_lost = Currency(row["money_lost"])
                description += f"**{rank}. {user_name}** - {self.coin_emoji} -{money_lost:,.2f}\n"
                rank += 1
            
            embed.description = description

            return embed

        # View to change categories (balance and money lost)
        view = View()
        select_item = Select(
            placeholder="Select Category",
            options=[
                SelectOption(label="Balance", value="balance", description="See the balance leadeerboard"),
                SelectOption(label="Money Lost", value="money_lost", description="See the money lost leaderboard")
            ]
        )
        async def select_callback(interaction: discord.Interaction):
            select_category = select_item.values[0]
            if select_category == "balance":
                embed = await get_balance_leaderboard()
            else:
                embed = await get_money_lost_leaderboard()
            
            if not embed:
                return
            await interaction.response.edit_message(embed=embed, view=view)
        
        embed = await get_balance_leaderboard()
        select_item.callback = select_callback
        view.add_item(select_item)

        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: float):
        """Send money to someone else."""
        
        if amount <= 0:
            await ctx.send("have you tried using coins that have a positive amount of atoms?")
            return

        user_id = ctx.author.id
        if user_id == member.id:
            await ctx.send("cro what")
            return

        balance = await self._get_balance(user_id)
        # pug fix
        if Currency(amount) > balance:
            await ctx.send("pug is still fixed")
            return
        
        await self._add_money(user_id, -amount) # doesnt really count as losing money
        await self._add_money(member.id, amount)
        await ctx.send(f"{ctx.author.mention} sent {amount:,.2f} coins to {member.mention}! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def beg(self, ctx: commands.Context):
        """Beg for a few coins."""
        user_id = ctx.author.id

        balance = await self._get_balance(user_id)
        if balance > Currency(5_000): # That's like 2 daily claims
            await ctx.send("aint you rich enough")
            return

        amount = random.uniform(5, 20)
        await self._add_money(user_id, amount)
        await ctx.send(f"{ctx.author.mention} begged and received {amount:,.2f} coins. {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def compare(self, ctx: commands.Context, member1: discord.Member, member2: discord.Member):
        """Compare the balances of two users."""
        if member1.id == member2.id:
            await ctx.send("im tired ion wanna do this ")
            return
        
        balance1 = await self._get_balance(member1.id)
        balance2 = await self._get_balance(member2.id)

        if balance1 > balance2:
            diff = balance1 - balance2
            await ctx.send(f"{member1.mention} has {diff:,.2f} more coins than {member2.mention}.", allowed_mentions=discord.AllowedMentions.none())
        elif balance2 > balance1:
            diff = balance2 - balance1
            await ctx.send(f"{member2.mention} has {diff:,.2f} more coins than {member1.mention}.", allowed_mentions=discord.AllowedMentions.none())
        else:
            await ctx.send(f"{member1.mention} and {member2.mention} have the same amount of coins!", allowed_mentions=discord.AllowedMentions.none())

    # just other commands idk where to put
    @commands.command(aliases=("totalbal", "totbal", "tbal"))
    async def total_balance(self, ctx: commands.Context):
        """See the total balance of all users."""
        row = await db.fetchrow("SELECT SUM(balance) AS total_balance FROM economy")
        total_balance = Currency(row["total_balance"]) if row and row["total_balance"] is not None else Currency.none()
        await ctx.send(f"The total balance of all users is {total_balance:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(aliases=("totlost", "tlost"))
    async def total_money_lost(self, ctx: commands.Context):
        """See the total money lost by all users."""
        row = await db.fetchrow("SELECT SUM(money_lost) AS total_money_lost FROM economy")
        total_money_lost = Currency(row["total_money_lost"]) if row and row["total_money_lost"] is not None else Currency.none()
        await ctx.send(f"The total money lost by all users is {total_money_lost:,.2f} coins.", allowed_mentions=discord.AllowedMentions.none())

    # GAMBLING COMMANDS!!!
    @commands.command()
    async def double(self, ctx: commands.Context, amount: float):
        """Gamble your coins with a chance to double them."""
        user_id = ctx.author.id
        if amount <= 0:
            await ctx.send("gambling your debt?")
            return
        
        bet = Currency(amount)
        balance = await self._get_balance(user_id)
        possessive_pronoun = await get_pronoun(ctx.author.id, data_returned=PronounEnum.POSSESSIVE)
        if bet > balance:
            await ctx.send("check your balance cro :broken_heart:")
            return

        if random.random() < 0.5:
            double_amount = float(bet * 2)
            await self._add_money(user_id, bet)
            await ctx.send(f"{ctx.author.mention} doubled {possessive_pronoun} money and won {double_amount:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            await ctx.send(f"{ctx.author.mention} lost {bet:,.2f} coins... {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            await self._remove_money(user_id, float(bet)) # I didnt remove the money above cause it would append to money_lost too if they won
    
    @commands.command(name="doubleall")
    async def double_all(self, ctx: commands.Context):
        """Gamble all your coins!!!"""
        user_id = ctx.author.id
        balance = await self._get_balance(user_id)
        possessive_pronoun = await get_pronoun(ctx.author.id, data_returned=PronounEnum.POSSESSIVE)
        if balance <= Currency.none():
            await ctx.send("check your balance cro :broken_heart:")
            return

        bet = balance

        if random.random() < 0.5:
            double_amount = float(bet * 2)
            await self._add_money(user_id, bet)
            await ctx.send(f"{ctx.author.mention} doubled {possessive_pronoun} money and won {double_amount:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            await ctx.send(f"{ctx.author.mention} lost {bet:,.2f} coins... {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            await self._remove_money(user_id, float(bet)) 

    @commands.command()
    async def dicebet(self, ctx: commands.Context, amount: Optional[float] = None):
        """Roll a 6 sided dice, guess the correct side to win 6x your bet."""
        if not amount:
            await ctx.send("If you just wanna roll a dice, use !roll :broken_heart:")
            return
        
        if amount < 0:
            await ctx.send("what is a negative number im stupid")
            return
        
        if amount == 0:
            await ctx.send("You rolled a 0 and lost 0 coins!")
            return
        
        user_id = ctx.author.id
        bet = Currency(amount)
        balance = await self._get_balance(user_id)
        if bet > balance:
            await ctx.send("oh btw do !bal")
            return
        
        # Hard-coded guess
        guess = 2
        roll = random.randint(1, 6)
        if roll == guess:
            winnings = float(bet * 6)
            await self._add_money(user_id, float(bet * 5)) # Convert to float before database operation
            await ctx.send(f"{ctx.author.mention} guessed correctly and won {winnings:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            await self._remove_money(user_id, float(bet)) # Convert to float before database operation
            await ctx.send(f"{ctx.author.mention} guessed incorrectly and lost {bet:,.2f} coins... {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def slots(self, ctx: commands.Context, amount: float):
        """slot machine idk"""
        user_id = ctx.author.id
        animation_frames_number = random.randint(5, 8)
        bet = Currency(amount)
        balance = await self._get_balance(user_id)
        if bet <= Currency.none():
            await ctx.send("you tryna gamble negative money?")
            return
        
        if bet > balance:
            await ctx.send("check your balance cro :broken_heart:")
            return
        
        slot_emojis = ['🍒', '🍋', '🍊', '🍉', '⭐', '🔔', '💎']

        message = await ctx.send("Spinning the slots...", allowed_mentions=discord.AllowedMentions.none())
        await asyncio.sleep(2)

        for _ in range(animation_frames_number):
            current_frame = [random.choice(slot_emojis) for _ in range(3)]
            await message.edit(content="| " + " | ".join(current_frame) + " |")
            await asyncio.sleep(1)

        final_frame = [random.choice(slot_emojis) for _ in range(3)]
        await message.edit(content="| " + " | ".join(final_frame) + " |")

        if final_frame[0] == final_frame[1] == final_frame[2]:
            # Jackpot
            winnings = float(bet * 10)
            await self._add_money(user_id, float(bet * 9)) 
            await ctx.send(f"{ctx.author.mention} hit the jackpot and won {winnings:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        elif final_frame[0] == final_frame[1] or final_frame[1] == final_frame[2] or final_frame[0] == final_frame[2]:
            # Two in a row
            winnings = float(bet * 3)
            await self._add_money(user_id, float(bet * 2)) 
            await ctx.send(f"{ctx.author.mention} got two in a row and won {winnings:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            # No match
            await self._remove_money(user_id, float(bet)) 
            await ctx.send(f"{ctx.author.mention} didn't win anything and lost {bet:,.2f} coins... {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def crash(self, ctx: commands.Context, amount: float):
        """"Gamble your coins in a game of crash."""
        user_id = ctx.author.id
        if amount <= 0:
            await ctx.send("wtf are you trying to do")
            return
        
        bet = Currency(amount)
        balance = await self._get_balance(user_id)

        if bet > balance:
            await ctx.send("you're broke :broken_heart:")
            return
        
        crash_point = random.uniform(1.00, 2.50)
        crash_embed = discord.Embed(
            title="Crash Game",
            description="The game is starting! The multiplier is increasing... Type cash to cash out!"
        )
        crash_embed.add_field(name="Your Bet", value=f"{bet:,.2f} coins", inline=False)
        crash_embed.add_field(name="Multiplier", value="1.00x", inline=False)

        message = await ctx.send(embed=crash_embed, allowed_mentions=discord.AllowedMentions.none())

        def check(m: discord.Message):
            return m.author.id == user_id and m.channel.id == ctx.channel.id and m.content.strip().lower() != "cash"

        multiplier = 1.00
        try:
            while multiplier < crash_point:
                await asyncio.sleep(0.3)
                multiplier += random.uniform(0.10, 0.50)
                if multiplier > crash_point:
                    multiplier = crash_point
                crash_embed.set_field_at(1, name="Multiplier", value=f"{multiplier:.2f}x", inline=False)
                await message.edit(embed=crash_embed)
                msg = await self.bot.wait_for("message", check=check, timeout=0.3)
                if msg:
                    winnings = float(bet * multiplier)
                    await self._add_money(user_id, winnings - float(bet)) # Add profit only
                    crash_embed.description = f"You cashed out at {multiplier:.2f}x and won {winnings:,.2f} coins! {self.coin_emoji}"
                    await message.edit(embed=crash_embed)
                    return
        except asyncio.TimeoutError:
            pass

    # Admin commands
    @commands.command()
    async def give_money(self, ctx: commands.Context, member: discord.User, amount: float):
        """Spawns money out of thin air and gives it to someone. Can only be used by Ierzi."""
        if ctx.author.id != 966351518020300841:
            await ctx.send("To use this command you need 1e308 cash. You do not have this much money and so cannot use this command.")
            return
        
        await self._add_money(member.id, amount)
        await ctx.send(f"Successfully gave {amount:,.2f} coins to user ID {member}.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def set_balance(self, ctx: commands.Context, member: discord.User, amount: float):
        """Set someone's balance. Can only be used by Ierzi, obviously."""
        if ctx.author.id != 966351518020300841:
            await ctx.send("no.")
            return
        
        await self._set_balance(member.id, amount)
        await ctx.send(f"Set the balance of {member.mention} to {amount:,.2f} coins.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(aliases=("sml",))
    async def set_money_lost(self, ctx: commands.Context, member: discord.User, amount: float):
        """Set the money_lost of a user. Can only be used by Ierzi."""
        if ctx.author.id != 966351518020300841:
            await ctx.send("no.")
            return
        
        await self._set_money_lost(member.id, amount)
        await ctx.send(f"Set the money_lost of {member.mention} to {amount:,.2f} coins.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def ecoreset(self, ctx: commands.Context, member: discord.User):
        """Reset the economy data of a user. Can only be used by Ierzi."""
        if ctx.author.id != 966351518020300841:
            await ctx.send("no.")
            return
        
        await db.execute("DELETE FROM economy WHERE user_id = $1", member.id)
        await ctx.send(f"Reset the economy data of {member.mention}.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def ecotransfer(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """Transfer all economy data from one user to another. Can only be used by Ierzi."""
        if ctx.author.id != 966351518020300841:
            await ctx.send("no.")
            return
        
        user1_id = user1.id 
        user2_id = user2.id 

        if user1_id == user2_id:
            await ctx.send("smart")
            return

        row = await db.fetchrow("SELECT * FROM economy WHERE user_id = $1", user1_id)
        if not row:
            await ctx.send("the first user has no economy data.")
            return
        
        # Ensure the second user exists
        await self._ensure_user_exists(user2_id)

        await db.execute("""
            UPDATE economy 
            SET balance = $2,
                money_lost = $3,
                last_daily = $4,
                last_worked = $5,
                last_robbed_bank = $6,
                last_robbed_user = $7,
                items = $8
            WHERE user_id = $1
        """, user2_id, row["balance"], row["money_lost"], row["last_daily"], row["last_worked"], row["last_robbed_bank"], row["last_robbed_user"], row["items"])

        await db.execute("DELETE FROM economy WHERE user_id = $1", user1_id)

        await ctx.send(f"Transferred all economy data from <@{user1_id}> to <@{user2_id}>.", allowed_mentions=discord.AllowedMentions.none())

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
