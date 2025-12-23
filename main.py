import discord
import os
import time
from discord import app_commands
from discord.ext import commands
import json

# --- CONFIGURATION ---
SESSION_CHANNEL_ID = 1443909455866626240 
WELCOME_CHANNEL_ID = 1443909455866626240
STAFF_LOG_CHANNEL_ID = 1443909455866626240
SERVER_JOIN_CODE = "HillsideRP"
STAFF_ROLE_ID = 1452721845139673168 
PING_ROLE_ID = 1452721845139673168   

AOP_IMAGES = {
    "Northwind Falls": "https://media.discordapp.net/attachments/1322319257131946034/1446923555265581201/hillside_nf_aop_map.png",
    "Hillside City": "https://media.discordapp.net/attachments/1322319257131946034/1446923553894170801/hillside_hillside_city_aop_map.png"
}
# ---------------------

DATA_FILE = "session_data.json"

def save_data(msg_id, aop_votes=None):
    with open(DATA_FILE, "w") as f:
        json.dump({"last_msg_id": msg_id, "aop_votes": aop_votes or {}}, f)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"last_msg_id": None, "aop_votes": {}}

class SessionVoteView(discord.ui.View):
    def __init__(self, duration_mins, target, staff_member):
        super().__init__(timeout=None)
        self.voters = set()
        self.nf_votes = set()
        self.hc_votes = set()
        self.duration_mins = duration_mins
        self.target = target
        self.staff_member = staff_member
        self.goal_reached = False
        self.end_timestamp = int(time.time() + (duration_mins * 60))

    def create_embed(self):
        count = len(self.voters)
        embed = discord.Embed(
            color=16533327,
            title="Server Start Up Poll",
            description=(
                f"{self.staff_member.mention} has started an ssu poll.\n"
                f"**{self.target}** votes are required. Poll lasts **{self.duration_mins}** minutes.\n\n"
                f"Poll ends: <t:{self.end_timestamp}:R>"
            )
        )
        embed.add_field(name="AOP Voting", value=f"🏔️ NF: **{len(self.nf_votes)}**\n🏙️ HC: **{len(self.hc_votes)}**", inline=True)
        
        progress = min(count / self.target, 1.0)
        bar = "🟩" * int(progress * 10) + "⬜" * (10 - int(progress * 10))
        embed.add_field(name="Progress", value=f"{bar} ({count}/{self.target})", inline=False)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1322319257131946034/1441759845081546843/0a931781c210724549c829d241b0dc28_1.png")
        embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452718197714325565/image.png")
        return embed

    @discord.ui.button(label="0 Vote", style=discord.ButtonStyle.blurple, emoji="✅", row=0)
    async def vote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.voters: self.voters.remove(interaction.user.id)
        else: self.voters.add(interaction.user.id)
        button.label = f"{len(self.voters)} Vote"
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Northwind Falls", style=discord.ButtonStyle.gray, emoji="🏔️", row=1)
    async def nf_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.hc_votes: self.hc_votes.remove(interaction.user.id)
        if interaction.user.id in self.nf_votes: self.nf_votes.remove(interaction.user.id)
        else: self.nf_votes.add(interaction.user.id)
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Hillside City", style=discord.ButtonStyle.gray, emoji="🏙️", row=1)
    async def hc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.nf_votes: self.nf_votes.remove(interaction.user.id)
        if interaction.user.id in self.hc_votes: self.hc_votes.remove(interaction.user.id)
        else: self.hc_votes.add(interaction.user.id)
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🗑️", row=2)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        has_role = discord.utils.get(interaction.user.roles, id=STAFF_ROLE_ID)
        if has_role or interaction.user.guild_permissions.administrator:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("Missing Staff Role.", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.tree.command(name="ssupoll", description="Start SSU & AOP Poll")
async def ssupoll(interaction: discord.Interaction, minutes: int, votes_needed: int):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    view = SessionVoteView(minutes, votes_needed, interaction.user)
    poll_msg = await channel.send(content=f"<@&{PING_ROLE_ID}>", embed=view.create_embed(), view=view)
    save_data(poll_msg.id) # Temporarily save poll ID to delete it later
    await interaction.response.send_message("Poll posted!", ephemeral=True)

@bot.tree.command(name="ssustart", description="Post SSU and determine AOP winner")
async def ssustart(interaction: discord.Interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    data = load_data()
    
    # 1. Try to find and delete the poll
    winning_aop = "Northwind Falls" # Default
    if data["last_msg_id"]:
        try:
            poll_msg = await channel.fetch_message(data["last_msg_id"])
            # Count votes from the embed fields
            embed = poll_msg.embeds[0]
            nf_count = int(embed.fields[0].value.split("**")[1])
            hc_count = int(embed.fields[0].value.split("**")[3])
            if hc_count > nf_count: winning_aop = "Hillside City"
            await poll_msg.delete()
        except: pass

    # 2. Post Start Embed
    current_ts = int(time.time())
    start_embed = discord.Embed(
        color=16533327, title="Server Start Up",
        description=f"Server is now **OPEN**.\n**AOP**: `{winning_aop}`\n**Join Code**: `{SERVER_JOIN_CODE}`\n\nStarted: <t:{current_ts}:R>"
    )
    start_embed.set_image(url=AOP_IMAGES[winning_aop])
    
    msg = await channel.send(content=f"<@&{PING_ROLE_ID}>", embed=start_embed)
    save_data(msg.id) # Save the start msg ID so shutdown can delete it
    await interaction.response.send_message("Session started!", ephemeral=True)

@bot.tree.command(name="ssushutdown", description="End current session")
async def ssushutdown(interaction: discord.Interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    data = load_data()
    if data["last_msg_id"]:
        try:
            old_msg = await channel.fetch_message(data["last_msg_id"])
            await old_msg.delete()
        except: pass
            
    embed = discord.Embed(color=16533327, title="Server Shutdown", 
                         description=f"Server is closed.\n\nEnded: <t:{int(time.time())}:R>")
    embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452651288012656673/image.png")
    await channel.send(embed=embed)
    save_data(None)
    await interaction.response.send_message("Session ended!", ephemeral=True)

bot.run(os.getenv('DISCORD_TOKEN'))
