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
JOIN_LINK = "http://www.policeroleplay.community/join?code=HillsideRP&placeld=2534724415"
# ---------------------

DATA_FILE = "session_data.json"

def save_msg_id(msg_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"last_msg_id": msg_id}, f)

def load_msg_id():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f).get("last_msg_id")
    return None

class JoinButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Join Now", url=JOIN_LINK, style=discord.ButtonStyle.link))

class SessionVoteView(discord.ui.View):
    def __init__(self, duration_mins, target, staff_member):
        super().__init__(timeout=None)
        self.voters = set()
        self.hc_votes = set()
        self.nf_votes = set()
        self.duration_mins = duration_mins
        self.target = target
        self.staff_member = staff_member
        self.goal_notified = False
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
        progress = min(count / self.target, 1.0)
        bar = "🟩" * int(progress * 10) + "⬜" * (10 - int(progress * 10))
        embed.add_field(name="Current Progress", value=f"{bar} ({count}/{self.target})", inline=False)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1322319257131946034/1441759845081546843/0a931781c210724549c829d241b0dc28_1.png")
        embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452718197714325565/image.png")
        return embed

    @discord.ui.button(label="(0) Vote", style=discord.ButtonStyle.blurple, emoji="✅", row=0)
    async def vote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.voters: self.voters.remove(interaction.user.id)
        else: self.voters.add(interaction.user.id)
        count = len(self.voters)
        button.label = f"({count}) Vote"
        if count >= self.target and not self.goal_notified:
            self.goal_notified = True
            log_chan = interaction.client.get_channel(STAFF_LOG_CHANNEL_ID)
            if log_chan:
                await log_chan.send(f"🔔 {self.staff_member.mention}, the SSU poll has reached the goal of **{self.target}** votes!")
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="(0) Hillside City", style=discord.ButtonStyle.gray, emoji="🏙️", row=0)
    async def hc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.nf_votes: self.nf_votes.remove(interaction.user.id)
        if interaction.user.id in self.hc_votes: self.hc_votes.remove(interaction.user.id)
        else: self.hc_votes.add(interaction.user.id)
        button.label = f"({len(self.hc_votes)}) Hillside City"
        for item in self.children:
            if isinstance(item, discord.ui.Button) and "NF & HPH402" in str(item.label):
                item.label = f"({len(self.nf_votes)}) NF & HPH402"
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="(0) NF & HPH402", style=discord.ButtonStyle.gray, emoji="🌲", row=0)
    async def nf_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.hc_votes: self.hc_votes.remove(interaction.user.id)
        if interaction.user.id in self.nf_votes: self.nf_votes.remove(interaction.user.id)
        else: self.nf_votes.add(interaction.user.id)
        button.label = f"({len(self.nf_votes)}) NF & HPH402"
        for item in self.children:
            if isinstance(item, discord.ui.Button) and "Hillside City" in str(item.label):
                item.label = f"({len(self.hc_votes)}) Hillside City"
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        has_role = discord.utils.get(interaction.user.roles, id=STAFF_ROLE_ID)
        if has_role or interaction.user.guild_permissions.administrator:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("Missing Permissions.", ephemeral=True)

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
    msg = await channel.send(content=f"<@&{PING_ROLE_ID}>", embed=view.create_embed(), view=view)
    save_msg_id(msg.id) 
    await interaction.response.send_message("Poll posted!", ephemeral=True)

@bot.tree.command(name="ssustart", description="Start session and post AOP winner")
async def ssustart(interaction: discord.Interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    old_id = load_msg_id()
    winning_aop = "Hillside City"
    
    if old_id:
        try:
            old_msg = await channel.fetch_message(old_id)
            hc_count, nf_count = 0, 0
            for item in old_msg.components[0].children:
                if "Hillside City" in item.label:
                    hc_count = int(item.label.split("(")[1].split(")")[0])
                if "NF & HPH402" in item.label:
                    nf_count = int(item.label.split("(")[1].split(")")[0])
            if nf_count > hc_count: winning_aop = "NF & HPH402"
            await old_msg.delete()
        except: pass

    current_ts = int(time.time())
    main_embed = discord.Embed(
        color=16533327, title="Server Start Up",
        description=(f"Our ingame server is now open. Members can now join for roleplay.\n\n"
                     f"**Server**: `Hillside Provincial Roleplay I Strict I Canada`\n"
                     f"**Join Code**: `{SERVER_JOIN_CODE}`\n\n"
                     f"Session started: <t:{current_ts}:R>")
    )
    main_embed.set_thumbnail(url="https://media.discordapp.net/attachments/1322319257131946034/1441759845081546843/0a931781c210724549c829d241b0dc28_1.png")
    main_embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452709174868971601/image.png")

    # Suppression of link text using <URL>
    if winning_aop == "Hillside City":
        aop_text = "**The current Area of Play is Hillside City 🌆**"
        aop_img = "<https://media.discordapp.net/attachments/1322319257131946034/1446923553894170801/hillside_hillside_city_aop_map.png>"
    else:
        aop_text = "**The current Area of Play is Northwind Falls 🌊 and Hillside Provincial Highway 402 🚗**"
        # Updated to the correct NF map URL
        aop_img = "<https://media.discordapp.net/attachments/1322319257131946034/1446923555743993926/hillside_nf_and_hph402_aop_map.png>"

    await channel.send(content=f"<@&{PING_ROLE_ID}>", embed=main_embed, view=JoinButtonView())
    aop_msg = await channel.send(content=f"{aop_text}\n{aop_img}")
    save_msg_id(aop_msg.id) 
    await interaction.response.send_message("Session started!", ephemeral=True)

@bot.tree.command(name="ssushutdown", description="End current session")
async def ssushutdown(interaction: discord.Interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    async for message in channel.history(limit=10):
        if message.author == bot.user:
            if message.embeds and ("Server Start Up" in str(message.embeds[0].title)):
                await message.delete()
            elif "Area of Play" in message.content:
                await message.delete()
                
    embed = discord.Embed(color=16533327, title="Server Shutdown", description=f"Server is closed.\n\nEnded: <t:{int(time.time())}:R>")
    embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452651288012656673/image.png")
    await channel.send(embed=embed)
    save_msg_id(None)
    await interaction.response.send_message("Session ended!", ephemeral=True)

bot.run(os.getenv('DISCORD_TOKEN'))
