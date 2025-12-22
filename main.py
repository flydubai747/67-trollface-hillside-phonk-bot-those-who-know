import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# --- CONFIGURATION (FILL THESE IN) ---
TOKEN = 'MTQ1MjM5MzAyMTcyNjUyMzQzMw.GMvE8U.MHun-IaSY9d433fm_ZtBhq9I-ssuEleFg4MljA'
SESSION_CHANNEL_ID = 1443909455866626240 
WELCOME_CHANNEL_ID = 1443909455866626240
STAFF_LOG_CHANNEL_ID = 1443909455866626240
SERVER_JOIN_CODE = "HillsideRP"
# -------------------------------------

DATA_FILE = "session_data.json"

def save_msg_id(msg_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"last_msg_id": msg_id}, f)

def load_msg_id():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f).get("last_msg_id")
    return None

class SessionVoteView(discord.ui.View):
    def __init__(self, time, target, staff_member):
        super().__init__(timeout=None)
        self.voters = set()
        self.time = time
        self.target = target
        self.staff_member = staff_member
        self.goal_reached = False

    def create_embed(self):
        count = len(self.voters)
        voter_list = ", ".join([f"<@{uid}>" for uid in self.voters]) if self.voters else "No one yet!"
        progress = min(count / self.target, 1.0)
        bar = "🟩" * int(progress * 10) + "⬜" * (10 - int(progress * 10))

        embed = discord.Embed(title="🚔 ERLC Session Interest", color=discord.Color.gold())
        embed.add_field(name="Time", value=self.time, inline=True)
        embed.add_field(name="Goal", value=f"{count}/{self.target}", inline=True)
        embed.add_field(name="Progress", value=bar, inline=False)
        embed.add_field(name="Attendees", value=voter_list, inline=False)
        return embed

    @discord.ui.button(label="Attend", style=discord.ButtonStyle.blurple, emoji="✅")
    async def vote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.voters:
            self.voters.remove(interaction.user.id)
        else:
            self.voters.add(interaction.user.id)
        
        if len(self.voters) >= self.target and not self.goal_reached:
            self.goal_reached = True
            log_chan = interaction.client.get_channel(STAFF_LOG_CHANNEL_ID)
            if log_chan: await log_chan.send(f"🔔 {self.staff_member.mention}, goal reached for **{self.time}**!")

        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.staff_member.id or interaction.user.guild_permissions.manage_messages:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("Only staff can cancel this.", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Logged in as {self.user} and synced commands.")

bot = MyBot()

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        count = len(member.guild.members)
        embed = discord.Embed(title="Welcome!", description=f"{member.mention} joined! Member **#{count}**", color=discord.Color.blue())
        await channel.send(embed=embed)

@bot.tree.command(name="poll", description="Start interest check")
async def poll(interaction: discord.Interaction, time: str, target: int):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    view = SessionVoteView(time, target, interaction.user)
    await channel.send(embed=view.create_embed(), view=view)
    await interaction.response.send_message("Poll posted!", ephemeral=True)

@bot.tree.command(name="start", description="Start the ERLC session")
async def start(interaction: discord.Interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    embed = discord.Embed(title="🟢 SESSION STARTED", description=f"The server is now **OPEN**.\nJoin Code: `{SERVER_JOIN_CODE}`", color=discord.Color.green())
    msg = await channel.send(embed=embed)
    save_msg_id(msg.id)
    await interaction.response.send_message("Session started!", ephemeral=True)

@bot.tree.command(name="end", description="End session and delete start message")
async def end(interaction: discord.Interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    old_msg_id = load_msg_id()
    if old_msg_id:
        try:
            old_msg = await channel.fetch_message(old_msg_id)
            await old_msg.delete()
        except: pass
            
    embed = discord.Embed(title="🔴 SESSION ENDED", description="The server is now **CLOSED**.", color=discord.Color.red())
    await channel.send(embed=embed)
    save_msg_id(None)
    await interaction.response.send_message("Session ended!", ephemeral=True)

bot.run(TOKEN)