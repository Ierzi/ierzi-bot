import discord
from discord.ext import commands
import asyncio
import psycopg2
from rich.console import Console
import os

conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)

cur = conn.cursor()

console = Console()

class Marriages(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cur = cur
        self.conn = conn
        self.console = console

    async def add_marriage_list(self, marriage_pair: tuple[int]):
        self.cur.execute(
            "INSERT INTO marriages (user1_id, user2_id) VALUES (%s, %s)", 
            (marriage_pair[0], marriage_pair[1])
            )
        self.cur.execute(
            "INSERT INTO marriages (user1_id, user2_id) VALUES (%s, %s)", 
            (marriage_pair[1], marriage_pair[0])
            )
        self.conn.commit()

    async def remove_marriage_list(self, marriage_pair: tuple[int]):
        self.cur.execute(
            "DELETE FROM marriages WHERE user1_id = %s AND user2_id = %s",
            (marriage_pair[0], marriage_pair[1])
        )
        self.cur.execute(
            "DELETE FROM marriages WHERE user1_id = %s AND user2_id = %s",
            (marriage_pair[1], marriage_pair[0])
        )
        self.conn.commit()


    async def get_marriages(self):
        self.cur.execute("SELECT * FROM marriages")
        marriages = self.cur.fetchall()
        ids = []
        for marriage in marriages:
            _, id1, id2 = marriage
            ids.append((id1, id2))
        
        return ids

    @commands.command()
    async def marry(self, ctx: commands.Context, partner: discord.Member):
        proposer = ctx.author
        marriages = await self.get_marriages()

        if proposer.id == partner.id:
            await ctx.send("...")
            return
        if (proposer.id, partner.id) in marriages or (partner.id, proposer.id) in marriages:
            await ctx.send("does he know?")
            return
        if partner.id == self.bot.user.id:
            if proposer.id == 966351518020300841:
                await ctx.send("<333")
                await ctx.send(f"Congratulations {proposer.mention} and {self.bot.user.mention}, you are now happily married!", allowed_mentions=discord.AllowedMentions.none()) 
                await self.add_marriage_list((proposer.id, self.bot.user.id))
                return
            
            await ctx.send("faggot")
            await ctx.send(f"{self.bot.user.mention} has declined the marriage proposal.", allowed_mentions=discord.AllowedMentions.none())
            return
        if partner.bot:
            await ctx.send("dumbass")
            return
        
        await ctx.send(f"{partner.mention}, do you want to marry {proposer.mention}? \nReply with yes if you accept, or no if you decline.", allowed_mentions=discord.AllowedMentions.none())

        def check(m: discord.Message):
            return m.author.id == partner.id and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send(f"Marriage proposal for {partner.mention} timed out.", allowed_mentions=discord.AllowedMentions.none())
            return
        
        if msg.content.lower() == "yes":
            await ctx.send(f"Congratulations {proposer.mention} and {partner.mention}, you are now happily married!", allowed_mentions=discord.AllowedMentions.none())
            self.console.print(f"Marriage between {proposer.name} and {partner.name} has been recorded.")
            await self.add_marriage_list((proposer.id, partner.id))
        else:
            await ctx.send(f"{partner.mention} has declined the marriage proposal.", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def divorce(self, ctx: commands.Context, partner: discord.Member):
        proposer = ctx.author
        marriages = await self.get_marriages()

        if (proposer.id, partner.id) not in marriages and (partner.id, proposer.id) not in marriages:
            await ctx.send("You are not married to this person!")
            return
        
        await ctx.send(f"Are you sure you want to divorce {partner.mention}? \nReply with yes if you confirm, or no if you changed your mind. ", allowed_mentions=discord.AllowedMentions.none())
        
        def check(m: discord.Message):
            return m.author.id == proposer.id and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send(f"Divorce request by {ctx.author.mention} timed out.", allowed_mentions=discord.AllowedMentions.none())
            return
        
        if msg.content.lower() == "yes":
            # Remove the marriage from the list
            await self.remove_marriage_list((proposer.id, partner.id))
            await ctx.send(f"{proposer.mention} and {partner.mention} have been divorced. \n-# its over...", allowed_mentions=discord.AllowedMentions.none())
            self.console.print(f"Divorce between {proposer.name} and {partner.name} has been recorded.")
        else:
            await ctx.send(f"{proposer.mention} has canceled the divorce proposal.", allowed_mentions=discord.AllowedMentions.none())
            
    # TODO: fix this
    # @commands.command()
    # async def listmarriages(self, ctx: commands.Context, page_number: int = 1):
    #     marriages = await self.get_marriages()
            
    #     if not marriages:
    #         await ctx.send("Nobody is married yet!")
    #         return
    #     else:
    #         n_marriages = len(marriages) 
    #         n_pages = round(n_marriages // 10 + 1)
            
    #         if page_number > n_pages or page_number < 1:
    #             await ctx.send(f"Invalid page number. There are {n_pages} pages.")
    #             return
            
    #         # Send some sort of message to indicate that the bot is processing the request
    #         think = await ctx.send("Thinking...")

    #         all_messages = ""
    #         start_index = (page_number - 1) * 10
    #         count = 0
    #         mess_count = 0
    #         marriages_ = []
    #         for i, pair in enumerate(marriages):
    #             if pair[::-1] in marriages_:
    #                 continue

    #             count += 1
    #             if count <= start_index:
    #                 continue

    #             if mess_count == 10:
    #                 # Reach the end of the page
    #                 break

    #             if i % 10 == 0:
    #                 all_messages += f"**Page {page_number}/{n_pages}**\n"
                
    #             if i >= start_index:
    #                 user_1 = self.bot.get_user(pair[0]) or await self.bot.fetch_user(pair[0])
    #                 user_2 = self.bot.get_user(pair[1]) or await self.bot.fetch_user(pair[1])
    #                 all_messages += f"{user_1.mention} and {user_2.mention}\n"
    #                 marriages_.append(pair)
    #                 mess_count += 1
            
    #         await think.delete()
    #         await ctx.send(all_messages, allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def countmarriages(self, ctx: commands.Context, user: discord.Member = None):
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
        marriages = await self.get_marriages()
        number_marriages = len(marriages) // 2
        await ctx.send(f"There are {number_marriages} marriages." if number_marriages != 1 else f"There is 1 marriage.")

    @commands.command()
    async def marriagestatus(self, ctx: commands.Context, user: discord.Member = None):
        if user == None:
            user = ctx.author

        marriages = await self.get_marriages()
        user_marriages = [pair for pair in marriages if user.id in pair]
        
        if not user_marriages:
            await ctx.send(f"{user.mention} is not married.", allowed_mentions=discord.AllowedMentions.none())
            return
        
        marriage_status = ""
        count = 0
        for pair in user_marriages:
            partner_id = pair[0] if pair[1] == user.id else pair[1]
            partner = self.bot.get_user(partner_id) or await self.bot.fetch_user(partner_id)
            message = f"{user.mention} is married to {partner.mention}.\n"
            marriage_status += message if message not in marriage_status else ""
            count += 1
        
        marriage_status += f"\nTotal marriages: {count // 2}"
        await ctx.send(marriage_status, allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def forcemarry(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        marriages = await self.get_marriages()
        if (user1.id, user2.id) in marriages or (user2.id, user1.id) in marriages:
            await ctx.send("does he know?")
            return
        if user1.id == user2.id:
            await ctx.send("dumbass")
            return
        if ctx.author.id != 966351518020300841:
            await ctx.send("no.")
            return
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            await ctx.send("HELL NO :sob::sob:")
            return
        
        await self.add_marriage_list((user1.id, user2.id))
        await ctx.send(f"{user1.mention} and {user2.mention} are now married!", allowed_mentions=discord.AllowedMentions.none())
        self.console.print(f"Forced marriage between {user1.name} and {user2.name} has been recorded.")

    @commands.command()
    async def forcedivorce(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
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

