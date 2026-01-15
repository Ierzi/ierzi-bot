import discord
from discord import Message, SelectOption, Embed
from discord.ext import commands
from discord.ui import View, Select

from .utils.database import db
from .utils.functions import to_timestamp
from .utils.pronouns import get_pronoun, PronounEnum
from .utils.types import Currency
from .utils.variables import VIEW_TIMEOUT

import asyncio
from datetime import timedelta, datetime, timezone
from typing import Literal, Optional
import random
from rich.console import Console

from cogs.utils import pronouns


_hours = Optional[int]
_minutes = Optional[int]
_seconds = Optional[int]
_output_data = tuple[bool, _hours, _minutes, _seconds]

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.coin_emoji = '<:coins:1416429599084118239>'

        self.jobs = [ # Job name, min pay, max pay
            ("Retail Worker", 50.00, 130.00),
            ("Barista", 65.00, 155.00),
            ("Teacher", 90.00, 235.00),
            ("SFW Artist", 90.00, 260.00),
            ("Content Creator", 105.00, 275.00),
            ("Writer", 105.00, 315.00),
            ("Musician", 115.00, 350.00),
            ("Graphic Designer", 130.00, 325.00),
            ("Doctor", 195.00, 390.00),
            ("Software Developer", 195.00, 390.00),
            ("Lawyer", 235.00, 455.00),
            ("CEO", 325.00, 650.00)
        ]
        
        self.rare_jobs = [ #Job Name, Rarity, Minimum pay, maximum pay 
            ("NSFW Artist", 0.025, 325.00, 550.00),
            ("onlyfans", 0.00125, 1500.00, 3000.00)
        ]

        self.latest_transactions = [] # (user_id, amount, timestamp)
    
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

    async def _get_rebirths(self, user_id: int) -> int:
        """Get the number of rebirths of a user."""
        row = await db.fetchrow("SELECT rebirths FROM economy WHERE user_id = $1", user_id)
        if row:
            return row["rebirths"]
        else:
            return 0

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

    async def _add_new_transaction(self, user_id: int, amount: float) -> None:
        """Add a new transaction to the latest transactions list."""
        now = datetime.now(tz=timezone.utc)
        timestamp = to_timestamp(now, 'R')
        self.latest_transactions.append((user_id, amount, timestamp))

        # Keep only the last 500 transactions
        if len(self.latest_transactions) > 500:
            self.latest_transactions.pop(0)

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
        await self._add_new_transaction(user_id, amount)
    
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
        await self._add_new_transaction(user_id, -amount)

    async def _add_rebirths(self, user_id: int, rebirths: int = 1):
        """Add rebirths to a user."""
        await self._ensure_user_exists(user_id)
        await db.execute("""
            UPDATE economy 
            SET rebirths = rebirths + $2
            WHERE user_id = $1
        """, user_id, rebirths)
        self.console.print(f"Added {rebirths} rebirths to user {user_id}.")

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

    async def _set_rebirths(self, user_id: int, rebirths: int):
        """Set the number of rebirths of a user."""
        await self._ensure_user_exists(user_id)
        await db.execute("""
            UPDATE economy 
            SET rebirths = $2
            WHERE user_id = $1
        """, user_id, rebirths)
        self.console.print(f"Set rebirths of user {user_id} to {rebirths}.")

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

    async def _calculate_rebirth_cost(
            self,
            user_id: int
        ) -> float:
        """Calculate the rebirth cost for a user."""
        rebirths = await self._get_rebirths(user_id)
        base_cost = 1_000_000.00
        cost_multiplier = 2.0 ** rebirths
        cost = base_cost * cost_multiplier
        return cost
    

    async def _calculate_rebirth_bonus(
            self,
            user_id: int,
            bonus_per_rebirth: float = 0.1
        ) -> float:
        """Calculate the rebirth bonus multiplier for a user."""
        rebirths = await self._get_rebirths(user_id)
        bonus_multiplier = 1 + (rebirths * bonus_per_rebirth) # 10% bonus per rebirth by default
        return bonus_multiplier
    

    # Commands
    @commands.command(name="ecoprofile", aliases=("balance", "bal"))
    async def eco_profile(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """See your or someone else's economy profile."""
        if member is None:
            member = ctx.author
        
        balance = await self._get_balance(member.id)
        money_lost = await self._get_money_lost(member.id)
        rebirths = await self._get_rebirths(member.id)

        embed = Embed(
            title=f"{member.display_name}'s Economy Profile",
            color=discord.Colour.gold()
        )
        embed.add_field(name="Balance", value=f"{self.coin_emoji} {balance:,.2f}", inline=False)
        embed.add_field(name="Total Money Lost", value=f"{self.coin_emoji} {money_lost:,.2f}", inline=False)
        embed.add_field(name="Rebirths", value=f"💠 {rebirths:,} rebirths", inline=False)

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
        
        # Handle rare jobs
        for job, rarity, max_pay, min_pay in self.rare_jobs:
            if random.random() < rarity:
                pay = random.uniform(min_pay, max_pay)
                # Say rare job message
                if job == "onlyfans":
                    await ctx.send(f"{ctx.author.mention} **sold pictures on OnlyFans** and gained {pay:,.2f} coins 🔥👅 {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
                else: 
                    await ctx.send(f"{ctx.author.mention} worked as a **{job}** and earned {pay:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
                await self._add_money(user_id, pay)
                await self._update_cooldown(user_id, "last_worked")
                return
        
        job = random.choice(self.jobs)
        job_name, min_pay, max_pay = job

        rebirth_bonus = await self._calculate_rebirth_bonus(user_id)
        usual_pay = random.uniform(min_pay, max_pay) * rebirth_bonus
        rich_pay = 0.005 * (await self._get_balance(user_id)).to_float() * rebirth_bonus
        pay = max(usual_pay, rich_pay)

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

        balance = (await self._get_balance(user_id)).to_float()
        usual_daily_amount = 3500 * await self._calculate_rebirth_bonus(user_id)
        rich_daily = 0.002 * balance * await self._calculate_rebirth_bonus(user_id)
        daily_amount = max(usual_daily_amount, rich_daily)
        await self._add_money(user_id, daily_amount)
        await self._update_cooldown(user_id, "last_daily")
        await ctx.send(f"{ctx.author.mention} claimed {p_pronoun} daily! {daily_amount:,.2f} coins {self.coin_emoji}!", allowed_mentions=discord.AllowedMentions.none())

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
        
        success_chance = 0.25 * await self._calculate_rebirth_bonus(user_id, bonus_per_rebirth=0.05)
        self.console.print(f"Success chance: {success_chance}")
        user_balance = (await self._get_balance(user_id)).to_float()
        await self._update_cooldown(user_id, "last_robbed_bank")
        if random.random() < success_chance:
            usual_amount_stolen = random.uniform(500, 1000) 
            rich_amount_stolen = random.uniform(0.025 * user_balance, 0.05 * user_balance)
            amount_stolen = max(usual_amount_stolen, rich_amount_stolen)
            await self._add_money(user_id, amount_stolen)
            await ctx.send(f"{ctx.author.mention} robbed a bank and got away with {amount_stolen:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            usual_fine = random.uniform(200, 800)
            rich_fine = random.uniform(0.02 * user_balance, 0.0375 * user_balance) # to fine-tune
            fine = max(usual_fine, rich_fine)
            await self._remove_money(user_id, fine)
            await ctx.send(f"{ctx.author.mention} got caught and had to pay a fine of {fine:,.2f} coins...", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
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
        target_member_rebirths_bonus = await self._calculate_rebirth_bonus(member.id, bonus_per_rebirth=0.05)
        if target_balance.to_float() < 100 and not target_balance.to_float() < 0:
            await ctx.send(f"{member.mention} doesn't have enough money to be robbed.", allowed_mentions=discord.AllowedMentions.none())
            return

        success_chance = min(0.25 * target_member_rebirths_bonus, 0.5)
        await self._update_cooldown(user_id, "last_robbed_user")
        if random.random() < success_chance:
            amount_stolen = random.uniform(0.01 * target_balance.to_float(), 0.1 * target_balance.to_float()) 
            await self._remove_money(member.id, amount_stolen)
            await self._add_money(user_id, amount_stolen)
            await ctx.send(f"{ctx.author.mention} successfully robbed {member.mention} and stole {amount_stolen:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            fine = random.uniform(200, 600) 
            await self._remove_money(user_id, fine)
            await self._add_money(member.id, fine)
            robbed_pronouns = await pronouns.get_pronoun(member.id)
            await ctx.send(f"{ctx.author.mention} got caught trying to rob {member.mention} and gave {robbed_pronouns[1]} {fine:,.2f} coins...", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name="ecolb", aliases=("lb", "leaderboard", "baltop"))
    async def eco_leaderboard(self, ctx: commands.Context, arg_a: Optional[str] = None, arg_b: Optional[str] = None):
        """See the economy leaderboard."""
        await ctx.typing()
        # CASES
        # 1. !lb 2 -- page
        # 2. !lb lost -- category
        # 3. !lb lost 2 -- category and page
        # 4. !lb -- nothing

        per_page = 10
        page = 1
        offset = (page - 1) * 10
        category: str = "balance" # by default
        _case = 0 # Debug variable

        if arg_a is None and arg_b is None:
            # Both are none, case 4
            _case = 4
            # category is still balance
            # page is still 1
        else:
            try:
                # If arg_a can be converted to int, its a page number
                page = int(arg_a)
                offset = (page - 1) * 10 # Recalculate offset
                # Unkwown category, balance by default
                _case = 1
            except Exception:
                # Maybe argument 2? --> case 3
                try: 
                    page = int(arg_b)
                    offset = (page - 1) * 10 # Recalculate offset
                    # Since its argument 2, set category to arg_a
                    category = arg_a
                    _case = 3
                except Exception:
                    # Forcefully case 2
                    category = arg_a
                    _case = 2

        # Just a debug statement
        self.console.print(f"ARGUMENTS {arg_a}, {arg_b}")
        self.console.print(f"Case {_case}")
        self.console.print(f"Page {page}, offset {offset}, category {category}.")

        async def get_balance_leaderboard() -> Optional[Embed]:
            nonlocal offset
            rows = await db.fetch("""
                SELECT user_id, balance FROM economy 
                ORDER BY balance DESC 
                LIMIT $1 OFFSET $2
            """, per_page, offset)

            if not rows:
                return
            
            embed = Embed(
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

        async def get_money_lost_leaderboard() -> Optional[Embed]:
            nonlocal offset
            rows = await db.fetch("""
                SELECT user_id, money_lost FROM economy 
                ORDER BY money_lost DESC 
                LIMIT $1 OFFSET $2
            """, per_page, offset)

            if not rows:
                return
            
            embed = Embed(
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

        async def get_rebirths_leaderboard() -> Optional[Embed]:
            nonlocal offset
            rows = await db.fetch("""
                SELECT user_id, rebirths FROM economy 
                ORDER BY rebirths DESC 
                LIMIT $1 OFFSET $2
            """, per_page, offset)

            if not rows:
                return
            
            embed = Embed(
                title=f"Economy Rebirths Leaderboard - Page {page}",
                color=discord.Colour.gold()
            )
            description = ""
            rank = offset + 1
            for row in rows:
                user = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(row["user_id"])
                user_name = user.mention
                rebirths = row["rebirths"]
                description += f"**{rank}. {user_name}** - {rebirths:,} rebirths 💠\n"
                rank += 1
            
            embed.description = description

            return embed

        # View to change categories 
        view = View(timeout=VIEW_TIMEOUT)
        select_item = Select(
            placeholder="Select Category",
            options=[
                SelectOption(label="Balance", value="balance", description="See the balance leaderboard"),
                SelectOption(label="Money Lost", value="money_lost", description="See the money lost leaderboard"),
                SelectOption(label="Rebirths", value="rebirths", description="See the rebirths leaderboard")
            ]
        )

        async def select_callback(interaction: discord.Interaction):
            nonlocal category, embed, page, offset
            select_category = select_item.values[0]
            if select_category == "balance":
                embed = await get_balance_leaderboard()
                category = "balance"
            elif select_category == "money_lost":
                embed = await get_money_lost_leaderboard()
                category = "money_lost"
            else:
                embed = await get_rebirths_leaderboard()
                category = "rebirths"
            
            if not embed: 
                await interaction.response.send_message("try again idk my bot is weird", ephemeral=True)
                return

            await interaction.response.edit_message(embed=embed, view=view)
        
        match category:
            # Everything related to balance
            case "balance" | "bal":
                embed = await get_balance_leaderboard()
            case "lost" | "money_lost" | "ml":
                embed = await get_money_lost_leaderboard()
            case "rebirths" | "rebirth" | "rb":
                embed = await get_rebirths_leaderboard()
            case _:
                embed = await get_balance_leaderboard() # Defaults to balance
            
        if not embed:
            await ctx.send("No users found on this page.")
            return

        select_item.callback = select_callback
        view.add_item(select_item)

        # Next, back and refresh buttons
        async def back_callback(interaction: discord.Interaction):
            nonlocal page, offset
            if page == 1:
                await interaction.response.send_message("you are already on the first page dumbass", ephemeral=True)
                return
            page -= 1
            offset = (page - 1) * per_page
            match category:
                case "balance" | "bal":
                    new_embed = await get_balance_leaderboard()
                case "lost" | "money_lost" | "ml":
                    new_embed = await get_money_lost_leaderboard()
                case "rebirths" | "rebirth" | "rb":
                    new_embed = await get_rebirths_leaderboard()
                case _:
                    new_embed = await get_balance_leaderboard() # Defaults to balance
            if not new_embed:
                page += 1 # revert page change
                await interaction.response.send_message("No users found on this page.", ephemeral=True)
                return
            embed.title = new_embed.title
            embed.description = new_embed.description
            await interaction.response.edit_message(embed=embed, view=view)
        
        back_button = discord.ui.Button(label="⬅️", style=discord.ButtonStyle.grey)
        back_button.callback = back_callback
        view.add_item(back_button)

        async def next_callback(interaction: discord.Interaction):
            nonlocal page, offset
            page += 1
            offset = (page - 1) * per_page
            match category:
                case "balance" | "bal":
                    new_embed = await get_balance_leaderboard()
                case "lost" | "money_lost" | "ml":
                    new_embed = await get_money_lost_leaderboard()
                case "rebirths" | "rebirth" | "rb":
                    new_embed = await get_rebirths_leaderboard()
                case _:
                    new_embed = await get_balance_leaderboard() # Defaults to balance
            if not new_embed:
                page -= 1 # revert page change
                await interaction.response.send_message("No more users found on the next page.", ephemeral=True)
                return
            embed.title = new_embed.title
            embed.description = new_embed.description
            await interaction.response.edit_message(embed=embed, view=view)
        
        next_button = discord.ui.Button(label="➡️", style=discord.ButtonStyle.grey)
        next_button.callback = next_callback
        view.add_item(next_button)

        async def refresh_callback(interaction: discord.Interaction):
            nonlocal page, offset
            offset = (page - 1) * per_page
            match category:
                case "balance" | "bal":
                    new_embed = await get_balance_leaderboard()
                case "lost" | "money_lost" | "ml":
                    new_embed = await get_money_lost_leaderboard()
                case "rebirths" | "rebirth" | "rb":
                    new_embed = await get_rebirths_leaderboard()
                case _:
                    new_embed = await get_balance_leaderboard() # Defaults to balance
            if not new_embed:
                await interaction.response.send_message("No users found on this page.", ephemeral=True)
                return
            embed.title = new_embed.title
            embed.description = new_embed.description
            await interaction.response.edit_message(embed=embed, view=view)

        refresh_button = discord.ui.Button(label="🔄", style=discord.ButtonStyle.primary)
        refresh_button.callback = refresh_callback
        view.add_item(refresh_button)

        # Theres a lot of repeated code here, but its fine for now
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
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def beg(self, ctx: commands.Context):
        """Beg for a few coins."""
        user_id = ctx.author.id

        balance = await self._get_balance(user_id)
        if balance > Currency(5_000): # That's like 2 daily claims
            await ctx.send("aint you rich enough")

            def check(m: Message):
                return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
            
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=15.0)
            except asyncio.TimeoutError:
                return

            if msg.content.strip().lower() != "no":
                return
            
            await self._add_money(user_id, 0.01)
            await ctx.send(f"{ctx.author.mention} begged and received 0.01 coins. {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            return


        amount = random.uniform(5, 20)
        await self._add_money(user_id, amount)
        await ctx.send(f"{ctx.author.mention} begged and received {amount:,.2f} coins. {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def compare(self, ctx: commands.Context, member1: discord.Member, member2: discord.Member):
        """Compare the balances of two users."""
        if member1.id == member2.id:
            await ctx.send("im tired ion wanna do this")
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

    @commands.command()
    async def transactions(self, ctx: commands.Context, page: Optional[int] = 1):
        """See the latest economy transactions."""

        def get_transactions(page: int):
            offset = (page - 1) * 10
            transactions = self.latest_transactions[offset:offset + 10] # (if offset was 0, gets 0-9, if 1 gets 10-19, etc)
            transactions = transactions[::-1]
            return transactions
        
        async def format_description(transactions: list[tuple[int, float, str]]):
            description = ""
            for user_id, amount, timestamp in transactions:
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                if amount >= 0:
                    description += f"**{user.mention}** received {amount:,.2f} coins {timestamp} {self.coin_emoji}\n"
                else:
                    description += f"**{user.mention}** lost {-amount:,.2f} coins {timestamp} {self.coin_emoji}\n"
            return description

        transactions = get_transactions(page)

        if not transactions:
            await ctx.send("No transactions found on this page." if page > 1 else "No transactions found.")
            return
        
        async with ctx.typing():
            embed = Embed(
                title=f"Latest Economy Transactions - Page {page}",
                color=discord.Colour.gold()
            )

            description = await format_description(transactions)
            embed.description = description
        
        # Refresh and Next buttons
        view = View(timeout=VIEW_TIMEOUT)

        async def back_callback(interaction: discord.Interaction):
            nonlocal page
            page -= 1
            transactions = get_transactions(page)
            description = await format_description(transactions)
            embed.description = description
            embed.title = f"Latest Economy Transactions - Page {page}"
            await interaction.response.edit_message(embed=embed, view=view)
        
        back_button = discord.ui.Button(label="⬅️", style=discord.ButtonStyle.grey)
        back_button.callback = back_callback
        view.add_item(back_button)

        async def next_callback(interaction: discord.Interaction):
            nonlocal page
            page += 1
            transactions = get_transactions(page)
            if not transactions:
                page -= 1 # revert page change
                await interaction.response.send_message("No more transactions found on the next page.", ephemeral=True)
                return
            description = await format_description(transactions)
            embed.description = description
            embed.title = f"Latest Economy Transactions - Page {page}"
            await interaction.response.edit_message(embed=embed, view=view)
        
        next_button = discord.ui.Button(label="➡️", style=discord.ButtonStyle.grey)
        next_button.callback = next_callback
        view.add_item(next_button)

        async def refresh_callback(interaction: discord.Interaction):
            transactions = get_transactions(page)
            description = await format_description(transactions)
            embed.description = description
            await interaction.response.edit_message(embed=embed, view=view)
        
        refresh_button = discord.ui.Button(label="🔄", style=discord.ButtonStyle.primary)
        refresh_button.callback = refresh_callback
        view.add_item(refresh_button)
        
        await ctx.send(embed=embed, view=view)
            

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

    @commands.command(aliases=("total_r", "totalr"))
    async def total_rebirths(self, ctx: commands.Context):
        """See the total number of rebirths by all users."""
        row = await db.fetchrow("SELECT SUM(rebirths) AS total_rebirths FROM economy")
        total_rebirths = row["total_rebirths"] if row and row["total_rebirths"] is not None else 0
        await ctx.send(f"The total number of rebirths by all users is {total_rebirths:,}.", allowed_mentions=discord.AllowedMentions.none())

    # GAMBLING COMMANDS!!!
    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
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
    @commands.cooldown(1, 1, commands.BucketType.user)
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
    @commands.cooldown(1, 1, commands.BucketType.user)
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
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def wheel(self, ctx: commands.Context, amount: float):
        """Spin the wheel and win or lose money."""
        user_id = ctx.author.id
        if amount <= 0:
            await ctx.send("im feeling evil today, you just lost 100 coins.")
            await self._remove_money(user_id, 100)
            return
        
        bet = Currency(amount)
        balance = await self._get_balance(user_id)
        if bet > balance:
            await ctx.send(f"you only have {balance.to_float():,.2f} coins.")
            return
        
        wheel_multipliers = [0, 0.5, 1, 1.5, 2]
        end_multiplier = random.choice(wheel_multipliers)
        animation_frames = random.randint(15, 20)
        
        message = await ctx.send("Spinning the wheel...", allowed_mentions=discord.AllowedMentions.none())
        await asyncio.sleep(1.5)

        # Trying something new (making the animation slower and slower)
        animation_speed = 0.02
        for _ in range(animation_frames):
            current_frame = random.choice(wheel_multipliers)
            await message.edit(content=f"**{current_frame}x**")
            await asyncio.sleep(animation_speed)
            animation_speed += 0.02

        await message.edit(content=f"**{end_multiplier}x**")
        await asyncio.sleep(2)

        winnings = float(bet * end_multiplier)
        bet_amount = bet.to_float()

        if winnings < bet_amount:
            # Player receives only a fraction of the bet back: remove the net loss (bet - winnings)
            loss = bet_amount - winnings
            await self._remove_money(user_id, loss)
            await ctx.send(f"**{end_multiplier}x**: {ctx.author.mention} lost {loss:,.2f} coins... {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            return

        # Player made a net gain (winnings >= bet)
        net_gain = winnings - bet_amount
        if net_gain > 0:
            await self._add_money(user_id, net_gain)
            await ctx.send(f"**{end_multiplier}x**: {ctx.author.mention} won {net_gain:,.2f} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
        else:
            # Exactly even (e.g. 1x): no money changes
            await ctx.send(f"**{end_multiplier}x**: {ctx.author.mention} didn't win anything. {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

        #thank you gpt-5-mini
    
    # guess what im bringing back
    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def lottery(self, ctx: commands.Context):
        """Participate in the lottery! Costs 500 coins to enter btw."""
        user_id = ctx.author.id
        lottery_cost = Currency(500)
        balance = await self._get_balance(user_id)
        if lottery_cost > balance:
            await ctx.send("you broke bro")
            return
        
        winning_money = random.randint(10_000_000, 50_000_000)
        message = await ctx.send("The lottery is starting...", allowed_mentions=discord.AllowedMentions.none())
        await asyncio.sleep(2)

        numbers_pool = [str(i) for i in range(1, 51)]
        user_numbers = random.sample(numbers_pool, 6)
        winning_numbers = random.sample(numbers_pool, 6)
        #  Sort in ascending order
        user_numbers.sort(key=lambda x: int(x))
        winning_numbers.sort(key=lambda x: int(x))

        jackpot_message = f"The jackpot is {winning_money:,} coins! {self.coin_emoji}"
        await message.edit(content=jackpot_message)
        await asyncio.sleep(2)

        your_numbers = f"Your numbers: {', '.join(user_numbers)}"
        await message.edit(content=f"{jackpot_message}\n{your_numbers}")
        await asyncio.sleep(2)

        for i in range(6):
            await message.edit(content=f"{jackpot_message}\n{your_numbers}\nWinning numbers: {', '.join(winning_numbers[:i+1])}")
            await asyncio.sleep(1)
        
        matches = set(user_numbers) & set(winning_numbers)
        num_matches = len(matches)

        if num_matches == 6:
            await ctx.send(f"**{ctx.author.mention} won the lottery jackpot of {winning_money:,.2f} coins!!!** {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            await self._add_money(user_id, winning_money)
        else:
            await self._remove_money(user_id, float(lottery_cost))
            await ctx.send(f"{ctx.author.mention} didn't win the lottery and lost {lottery_cost:,.2f} coins... {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.user)
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
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def roulette(self, ctx: commands.Context, _type: str, choice: str, amount: float):
        """roulette! Usage: !roulette number 17 150 or !roulette color black 100"""
        # basic checks
        user_id = ctx.author.id
        if amount <= 0:
            await ctx.send("ok vro")
            return

        bet = Currency(amount)
        balance = await self._get_balance(user_id)

        if bet > balance:
            await ctx.send("make some money first")
            return
        
        _type = _type.strip().lower()
        choice = choice.strip().lower()

        if _type not in ["color", "number"]:
            await ctx.send("invalid type")
            return

        if _type == "color":
            if choice not in ["red", "black", "green"]:
                await ctx.send("invalid color")
                return
        
        # Not including ranges nor odds/evens for now

        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        
        # Funny animation
        winning_number = random.randint(0, 36)
        animation_frames = random.randint(6, 9) # nice

        message = await ctx.send("Spinning the roulette...", allowed_mentions=discord.AllowedMentions.none())
        await asyncio.sleep(2)

        for _ in range(animation_frames):
            number = random.randint(0, 36)
            formatted_message = f"Spinning the roulette... 🟢 {number}" if number == 0 else f"Spinning the roulette... 🔴 {number}" if number in red_numbers else f"Spinning the roulette... ⚫ {number}"
            await message.edit(content=formatted_message)
            await asyncio.sleep(1)
        
        winning_message = f"Spinning the roulette... 🟢 {winning_number}" if winning_number == 0 else f"Spinning the roulette... 🔴 {winning_number}" if winning_number in red_numbers else f"Spinning the roulette... ⚫ {winning_number}"
        await message.edit(content=winning_message)

        if _type == "color":
            if choice == "red" and winning_number in red_numbers:
                winnings = float(bet * 2)
                await self._add_money(user_id, winnings)
                await ctx.send(f"{ctx.author.mention} won {winnings} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
                return
            elif choice == "black" and winning_number not in red_numbers:
                winnings = float(bet * 2)
                await self._add_money(user_id, winnings)
                await ctx.send(f"{ctx.author.mention} won {winnings} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
                return
            elif choice == "green" and winning_number == 0:
                winnings = float(bet * 36)
                await self._add_money(user_id, winnings - bet.to_float())
                await ctx.send(f"{ctx.author.mention} won {winnings} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
                return

        elif _type == "number":
            if choice == str(winning_number):
                winnings = float(bet * 36)
                await self._add_money(user_id, winnings - bet.to_float())
                await ctx.send(f"{ctx.author.mention} won {winnings} coins! {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
                return

        await self._remove_money(user_id, bet.to_float())
        await ctx.send(f"{ctx.author.mention} lost {bet:,.2f} coins... {self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    # Rebirth commands
    @commands.group()
    async def rebirth(self, ctx: commands.Context):
        """Rebirth commands."""
        if ctx.invoked_subcommand is None:
           return
        
    @rebirth.command()
    async def see(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """See your or someone else's rebirths."""
        if member is None:
            member = ctx.author
        
        rebirths = await self._get_rebirths(member.id)

        await ctx.send(f"{member.mention} has rebirthed {rebirths} times. 💠", allowed_mentions=discord.AllowedMentions.none())
    
    @rebirth.command()
    async def buy(self, ctx: commands.Context):
        """Buy a rebirth."""
        user_id = ctx.author.id
        balance = await self._get_balance(user_id)
        rebirth_cost = await self._calculate_rebirth_cost(user_id)

        if balance < Currency(rebirth_cost):
            await ctx.send(f"You need {rebirth_cost:,.2f} coins to rebirth, but you only have {balance:,.2f} coins.", allowed_mentions=discord.AllowedMentions.none())
            return
        
        # Reset economy data except rebirths
        await db.execute("""
            UPDATE economy
            SET balance = 0.00,
                money_lost = 0.00,
                last_daily = NULL,
                last_worked = NULL,
                last_robbed_bank = NULL,
                last_robbed_user = NULL
            WHERE user_id = $1
        """, user_id)


        await self._add_rebirths(user_id)
        bonus_multiplier = await self._calculate_rebirth_bonus(user_id)
        await ctx.send(f"{ctx.author.mention} has successfully rebirthed! {self.coin_emoji} Your earnings are now multiplied by {bonus_multiplier:.2f}x! 💠", allowed_mentions=discord.AllowedMentions.none())

    @rebirth.command(aliases=("next",))
    async def price(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """See how much your next or someone else's rebirth will cost."""

        if member is not None:
            rebirth_cost = await self._calculate_rebirth_cost(member.id)
            await ctx.send(f"{member.mention}'s next rebirth will cost {rebirth_cost:,.2f} coins. 💠{self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())
            return
        
        rebirth_cost = await self._calculate_rebirth_cost(ctx.author.id)
        await ctx.send(f"Your next rebirth will cost {rebirth_cost:,.2f} coins. 💠{self.coin_emoji}", allowed_mentions=discord.AllowedMentions.none())

    # Admin commands
    @commands.command()
    @commands.is_owner()
    async def give_money(self, ctx: commands.Context, user: discord.User, amount: float):
        """Spawns money out of thin air and gives it to someone. Can only be used by bot owners."""

        await self._add_money(user.id, amount)
        await ctx.send(f"Successfully gave {amount:,.2f} coins to user {user}.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(aliases=("gr",))
    @commands.is_owner()
    async def give_rebirth(self, ctx: commands.Context, user: discord.User, amount: Optional[int] = 1):
        """Give someone rebirths. Can only be used by bot owners."""
        
        await self._add_rebirths(user.id, amount)
        await ctx.send(f"Successfully gave {amount} rebirth(s) to user {user}.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.is_owner()
    async def set_balance(self, ctx: commands.Context, user: discord.User, amount: float):
        """Set someone's balance. Can only be used by bot owners."""

        await self._set_balance(user.id, amount)
        await ctx.send(f"Set the balance of {user.mention} to {amount:,.2f} coins.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(aliases=("sml",))
    @commands.is_owner()
    async def set_money_lost(self, ctx: commands.Context, user: discord.User, amount: float):
        """Set the money_lost of a user. Can only be used by bot owners."""
        
        await self._set_money_lost(user.id, amount)
        await ctx.send(f"Set the money_lost of {user.mention} to {amount:,.2f} coins.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.is_owner()
    async def set_rebirths(self, ctx: commands.Context, user: discord.User, amount: int):
        """Set the rebirths of a user. Can only be used by bot owners."""
        
        await self._set_rebirths(user.id, amount)
        await ctx.send(f"Set the rebirths of {user.mention} to {amount}.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command(aliases=("mm",))
    @commands.is_owner()
    async def max_money(self, ctx: commands.Context, user: discord.User):
        """Give someone the maximum balance possible. Can only be used by bot owners."""
        
        max_balance = 999_999_999_999.99
        await self._set_balance(user.id, max_balance)
        await ctx.send(f"Set the balance of {user.mention} to the maximum balance of {max_balance:,.2f} coins.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.is_owner()
    async def ecoreset(self, ctx: commands.Context, user: discord.User):
        """Reset the economy data of a user. Can only be used by bot owners."""
        
        await db.execute("DELETE FROM economy WHERE user_id = $1", user.id)
        await ctx.send(f"Reset the economy data of {user.mention}.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.is_owner()
    async def ecotransfer(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """Transfer all economy data from one user to another. Can only be used by bot owners."""
        
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
                rebirths = $8
            WHERE user_id = $1
        """, user2_id, row["balance"], row["money_lost"], row["last_daily"], row["last_worked"], row["last_robbed_bank"], row["last_robbed_user"], row["rebirths"])

        await db.execute("DELETE FROM economy WHERE user_id = $1", user1_id)

        await ctx.send(f"Transferred all economy data from {user1.mention} to {user2.mention}.", allowed_mentions=discord.AllowedMentions.none())

async def update_tables(reset: bool = False) -> None:
    # Just remaking the database schema lmao
    # max balance is 999,999,999,999.99
    # New max money lost is 999,999,999,999,999.99

    if reset:
        await db.execute("DROP TABLE IF EXISTS economy")

    await db.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                balance numeric(15, 2) NOT NULL DEFAULT 0.00,
                money_lost numeric(18, 2) NOT NULL DEFAULT 0.00,
                last_daily TIMESTAMPTZ,
                last_worked TIMESTAMPTZ,
                last_robbed_bank TIMESTAMPTZ,
                last_robbed_user TIMESTAMPTZ,
                rebirths INT NOT NULL DEFAULT 0
                );
    """)

