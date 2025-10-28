import discord
from discord.ext import commands
from discord.ui import Button, View

from .utils import pronouns
from .utils.database import db
from .utils.pronouns import PronounEnum
from .utils.variables import *

from rich.console import Console
from typing import Optional

class Marriages(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console

    async def add_marriage_list(self, marriage_pair: tuple[int]):
        # Ensure both users exist in the users table first
        for user_id in marriage_pair:
            await db.execute(
                "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
                user_id,
            )
        await db.execute(
            "INSERT INTO marriages (user1_id, user2_id) VALUES ($1, $2)", 
            marriage_pair[0], marriage_pair[1]
        )
        await db.execute(
            "INSERT INTO marriages (user1_id, user2_id) VALUES ($1, $2)", 
            marriage_pair[1], marriage_pair[0]
        )

    async def remove_marriage_list(self, marriage_pair: tuple[int]):
        await db.execute(
            "DELETE FROM marriages WHERE user1_id = $1 AND user2_id = $2",
            marriage_pair[0], marriage_pair[1]
        )
        await db.execute(
            "DELETE FROM marriages WHERE user1_id = $1 AND user2_id = $2",
            marriage_pair[1], marriage_pair[0]
        )


    async def get_marriages(self):
        marriages = await db.fetch("SELECT id, user1_id, user2_id FROM marriages")
        ids = []
        for marriage in marriages:
            _, id1, id2 = marriage
            ids.append((id1, id2))
        
        return ids

    @commands.command()
    async def marry(self, ctx: commands.Context, partner: discord.Member):
        """Marry someone."""
        proposer = ctx.author
        marriages = await self.get_marriages()

        if proposer.id == partner.id:
            await ctx.send("...")
            return
        if (proposer.id, partner.id) in marriages or (partner.id, proposer.id) in marriages:
            await ctx.send("does he know?")
            return
        if partner.id == self.bot.user.id:
            if proposer.id == 966351518020300841: # me :3
                await ctx.send("<333")
                await ctx.send(f"Congratulations {proposer.mention} and {self.bot.user.mention}, you are now happily married!", allowed_mentions=discord.AllowedMentions.none()) 
                await self.add_marriage_list((proposer.id, self.bot.user.id))
                return
            if ctx.guild.id in NO_SLURS_SERVERS: 
                await ctx.send("no.")
                await ctx.send(f"{self.bot.user.mention} has declined the marriage proposal.", allowed_mentions=discord.AllowedMentions.none())
                return
                
            await ctx.send("faggot")
            await ctx.send(f"{self.bot.user.mention} has declined the marriage proposal.", allowed_mentions=discord.AllowedMentions.none())
            return
        if partner.bot:
            await ctx.send("dumbass")
            return
        
        message = f"{partner.mention}, do you want to marry {proposer.mention}? \nYou have 2 hours to respond."
        view = View(timeout=VIEW_TIMEOUT)
        yes_button = Button(label="Yes", style=discord.ButtonStyle.green)
        no_button = Button(label="No", style=discord.ButtonStyle.red)

        async def yes_button_callback(interaction: discord.Interaction):
            if not interaction.user.id == partner.id:
                await interaction.response.send_message("no.", ephemeral=True)
                return
            
            await interaction.response.send_message(f"Congratulations {proposer.mention} and {partner.mention}, you are now happily married!", allowed_mentions=discord.AllowedMentions.none())
            await interaction.message.edit(view=None)
            await self.add_marriage_list((proposer.id, partner.id))
            self.console.print(f"Marriage between {proposer.name} and {partner.name} has been recorded.")
        
        async def no_button_callback(interaction: discord.Interaction):
            if not interaction.user.id == partner.id:
                await interaction.response.send_message("why do you wanna ruin someone's marriage? :sob:", ephemeral=True)
                return

            await interaction.response.send_message(f"{partner.mention} has declined the marriage proposal.", allowed_mentions=discord.AllowedMentions.none())
            await interaction.message.edit(view=None)

        yes_button.callback = yes_button_callback
        no_button.callback = no_button_callback
        view.add_item(yes_button)
        view.add_item(no_button)

        await ctx.send(message, allowed_mentions=discord.AllowedMentions.none(), view=view)

    @commands.command()
    async def divorce(self, ctx: commands.Context, partner: discord.Member):
        """Divorce someone."""
        proposer = ctx.author
        marriages = await self.get_marriages()

        if (proposer.id, partner.id) not in marriages and (partner.id, proposer.id) not in marriages:
            await ctx.send("You are not married to this person!")
            return
        
        # fact cant divorce guest
        if proposer.id == 1206615811792576614 and partner.id == 747918143745294356: 
            await ctx.send("Not now big guy~")
            return

        message = f"Are you sure you want to divorce {partner.mention}? \nYou have 2 hours to respond."

        view = View(timeout=VIEW_TIMEOUT)
        yes_button = Button(label="Yes", style=discord.ButtonStyle.green)
        no_button = Button(label="No", style=discord.ButtonStyle.red)

        partner_pronouns_object = await pronouns.get_pronoun(partner.id, PronounEnum.OBJECT)

        async def yes_button_callback(interaction: discord.Interaction):
            if not interaction.user.id == proposer.id:
                await interaction.response.send_message("wow you found the very secret message", ephemeral=True)
                return
            
            await interaction.response.send_message(f"{proposer.mention} and {partner.mention} have been divorced. \n-# its over...")
            await interaction.message.edit(view=None)
        
        async def no_button_callback(interaction: discord.Interaction):
            if not interaction.user.id == proposer.id:
                await interaction.response.send_message("a", ephemeral=True)
                return

            await interaction.response.send_message(f"{proposer.mention} doesnt want to divorce {partner_pronouns_object} :D")
            await interaction.message.edit(view=None)

        yes_button.callback = yes_button_callback
        no_button.callback = no_button_callback
        view.add_item(yes_button)
        view.add_item(no_button)

        await ctx.send(message, allowed_mentions=discord.AllowedMentions.none(), view=view)

    @commands.command()
    async def aremarried(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        """Says if two people are married to each other."""
        marriages = await self.get_marriages()
        if (user1, user2) in marriages:
            await ctx.message.reply("Yes, they are married.")
            return
        
        await ctx.message.reply("No, they aren't married.")


    @commands.command()
    async def countmarriages(self, ctx: commands.Context, user: discord.Member = None):
        """Count the number of marriages a member has."""
        if user == None:
            user = ctx.author
        
        marriages = await self.get_marriages()
        user_marriages = [pair for pair in marriages if user.id in pair]

        if not user_marriages:
            await ctx.send(f"{user.mention} is not married.", allowed_mentions=discord.AllowedMentions.none())
            return
        
        number_marriages = len(user_marriages) // 2
        await ctx.send(f"{user.mention} has {number_marriages} marriages.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def totalmarriages(self, ctx: commands.Context):
        """Amount of marriages globally."""
        marriages = await self.get_marriages()
        number_marriages = len(marriages) // 2
        await ctx.send(f"There are {number_marriages} marriages." if number_marriages != 1 else f"There is 1 marriage.")

    @commands.command()
    async def marriagestatus(self, ctx: commands.Context, user: discord.Member = None):
        """Check all the marriages of an user."""
        if user == None:
            user = ctx.author

        marriages = await self.get_marriages()
        user_marriages = [pair for pair in marriages if user.id in pair]
        
        if not user_marriages:
            await ctx.send(f"{user.mention} is not married.", allowed_mentions=discord.AllowedMentions.none())
            return

        marriage_status = ""
        count = 0
        async with ctx.typing():
            for pair in user_marriages:
                partner_id = pair[0] if pair[1] == user.id else pair[1]
                partner = self.bot.get_user(partner_id) or await self.bot.fetch_user(partner_id)
                message = f"{user.mention} is married to {partner.mention}, " if count == 0 else f"{partner.mention}, "
                marriage_status += message if message not in marriage_status else ""
                count += 1

        if marriage_status.endswith(", "):
            marriage_status = marriage_status[:-2]

        marriage_status += f"\n\nTotal marriages: {count // 2}"
        await ctx.send(marriage_status, allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    @commands.is_owner()
    async def forcemarry(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        """Can only be used by bot owners. Force marry 2 people."""
        marriages = await self.get_marriages()
        if (user1.id, user2.id) in marriages or (user2.id, user1.id) in marriages:
            await ctx.send("does he know?")
            return
        if user1.id == user2.id:
            await ctx.send("dumbass")
            return
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            await ctx.send("HELL NO :sob::sob:")
            return
        
        await self.add_marriage_list((user1.id, user2.id))
        await ctx.send(f"{user1.mention} and {user2.mention} are now married!", allowed_mentions=discord.AllowedMentions.none())
        self.console.print(f"Forced marriage between {user1.name} and {user2.name} has been recorded.")

    @commands.command()
    @commands.is_owner()
    async def forcedivorce(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        """Can only be used by bot owners. Force divorce 2 people."""
        marriages = await self.get_marriages()
        if (user1.id, user2.id) not in marriages and (user2.id, user1.id) not in marriages:
            await ctx.send("they are not married lmao")
            return
        if ctx.author.id != 966351518020300841:
            await ctx.send("no.")
            return
        
        await self.remove_marriage_list((user1.id, user2.id))
        await ctx.send(f"{user1.mention} and {user2.mention} have been divorced.", allowed_mentions=discord.AllowedMentions.none())
        self.console.print(f"Forced divorce between {user1.name} and {user2.name} has been recorded.")

