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
active_polls = {}

def save_msg_id(msg_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"last_msg_id": msg_id}, f)

def load_msg_id():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f).get("last_msg_id")
    return None

async def cleanup_aop(channel):
    async for message in channel.history(limit=10):
        if message.author.id == bot.user.id and message.embeds:
            desc = str(message.embeds[0].description).lower()
            if "area of play" in desc:
                try: await message.delete()
                except: pass

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
        embed = discord.Embed(color=16533327, title="Server Start Up Poll")
        embed.description = (f"{self.staff_member.mention} started a poll. **{self.target}** votes needed.\n"
                             f"Ends: <t:{self.end_timestamp}:R>")
        progress = min(count / self.target, 1.0)
        bar = "🟩" * int(progress * 10) + "⬜" * (10 - int(progress * 10))
        embed.add_field(name="Progress", value=f"{bar} ({count}/{self.target})", inline=False)
        return embed

    @discord.ui.button(label="Vote", style=discord.ButtonStyle.blurple, emoji="✅")
    async def vote_button(self, interaction, button):
        if interaction.user.id in self.voters: self.voters.remove(interaction.user.id)
        else: self.voters.add(interaction.user.id)
        button.label = f"({len(self.voters)}) Vote"
        if len(self.voters) >= self.target and not self.goal_notified:
            self.goal_notified = True
            log_chan = interaction.client.get_channel(STAFF_LOG_CHANNEL_ID)
            if log_chan: await log_chan.send(f"🔔 {self.staff_member.mention}, goal reached!")
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def cancel_button(self, interaction, button):
        # Staff check for the button
        if any(role.id == STAFF_ROLE_ID for role in interaction.user.roles) or interaction.user.guild_permissions.administrator:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("loser :rof", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(JoinButtonView())
        # Global Error Handler for Slash Commands
        @self.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.errors.MissingRole) or isinstance(error, app_commands.errors.MissingPermissions):
                await interaction.response.send_message("loser :rof", ephemeral=True)
            else:
                raise error
        await self.tree.sync()

    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            count = len(member.guild.members)
            embed = discord.Embed(title="Welcome!", description=f"Welcome {member.mention}! You are member **#{count}**.", color=16533327)
            await channel.send(embed=embed)

    async def on_message(self, message):
        if message.author == self.user: return
        if message.channel.id == 1443909455866626240:
            if message.content.lower().startswith("say "):
                # Checking role for the !say command too
                if any(role.id == STAFF_ROLE_ID for role in message.author.roles) or message.author.guild_permissions.administrator:
                    parts = message.content.split()
                    try:
                        chan = self.get_channel(int(parts[-1]))
                        if chan:
                            await chan.send(" ".join(parts[1:-1]))
                            await message.add_reaction("✅")
                    except: pass
                else:
                    await message.channel.send("loser :rof", delete_after=3)
        await self.process_commands(message)

bot = MyBot()

# --- AOP UPDATES (STAFF ONLY) ---
@bot.tree.command(name="aopnfhphnrnp")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def aopnfhphnrnp(interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    await cleanup_aop(channel)
    embed = discord.Embed(color=16533327, description="### AOP Update Sent")
    await channel.send(embed=embed)
    await interaction.followup.send("Updated")

@bot.tree.command(name="aopnfhph")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def aopnfhph(interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    await cleanup_aop(channel)
    await interaction.followup.send("Updated")

@bot.tree.command(name="aophs")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def aophs(interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    await cleanup_aop(channel)
    await interaction.followup.send("Updated")

@bot.tree.command(name="aopnf")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def aopnf(interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    await cleanup_aop(channel)
    await interaction.followup.send("Updated")

@bot.tree.command(name="aopmw")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def aopmw(interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    await cleanup_aop(channel)
    await interaction.followup.send("Updated")

# --- SSU COMMANDS (STAFF ONLY) ---
@bot.tree.command(name="ssupoll")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def ssupoll(interaction, minutes: int, votes_needed: int):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    view = SessionVoteView(minutes, votes_needed, interaction.user)
    msg = await channel.send(content=f"<@&{PING_ROLE_ID}>", embed=view.create_embed(), view=view)
    save_msg_id(msg.id) 
    active_polls[msg.id] = view
    await interaction.response.send_message("Posted!", ephemeral=True)

@bot.tree.command(name="ssustart")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def ssustart(interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    old_id = load_msg_id()
    voters = ""
    if old_id in active_polls:
        voters = " ".join([f"<@{uid}>" for uid in active_polls[old_id].voters])
    
    embed = discord.Embed(color=16533327, title="Server Start Up", description=f"Server Open!")
    await channel.send(content=f"<@&{PING_ROLE_ID}> {voters}", embed=embed, view=JoinButtonView())
    await interaction.followup.send("Started!")

@bot.tree.command(name="ssushutdown")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def ssushutdown(interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    embed = discord.Embed(color=16533327, title="Shutdown", description="Server Closed.")
    await channel.send(embed=embed)
    await interaction.response.send_message("Closed", ephemeral=True)

bot.run(os.getenv('DISCORD_TOKEN'))
