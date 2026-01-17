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
        embed = discord.Embed(
            color=16533327,
            title="Server Start Up Poll",
            description=(
                f"{self.staff_member.mention} has started an ssu poll. "
                f"**{self.target}** votes are required to start up the server. Poll lasts **{self.duration_mins}** minutes.\n\n"
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
    async def vote_button(self, interaction, button):
        if interaction.user.id in self.voters: self.voters.remove(interaction.user.id)
        else: self.voters.add(interaction.user.id)
        button.label = f"({len(self.voters)}) Vote"
        if len(self.voters) >= self.target and not self.goal_notified:
            self.goal_notified = True
            log_chan = interaction.client.get_channel(STAFF_LOG_CHANNEL_ID)
            if log_chan:
                await log_chan.send(f"🔔 {self.staff_member.mention}, the SSU poll has reached the goal of **{self.target}** votes!")
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="(0) NF & HPH402", style=discord.ButtonStyle.gray, emoji="<:northwindfalls:1462090977291403409>", row=0)
    async def nf_button(self, interaction, button):
        if interaction.user.id in self.hc_votes: self.hc_votes.remove(interaction.user.id)
        if interaction.user.id in self.nf_votes: self.nf_votes.remove(interaction.user.id)
        else: self.nf_votes.add(interaction.user.id)
        button.label = f"({len(self.nf_votes)}) NF & HPH402"
        for item in self.children:
            if isinstance(item, discord.ui.Button) and "Hillside City" in str(item.label):
                item.label = f"({len(self.hc_votes)}) Hillside City"
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="(0) Hillside City", style=discord.ButtonStyle.gray, emoji="<:hillsidecity:1453055474101391558>", row=0)
    async def hc_button(self, interaction, button):
        if interaction.user.id in self.nf_votes: self.nf_votes.remove(interaction.user.id)
        if interaction.user.id in self.hc_votes: self.hc_votes.remove(interaction.user.id)
        else: self.hc_votes.add(interaction.user.id)
        button.label = f"({len(self.hc_votes)}) Hillside City"
        for item in self.children:
            if isinstance(item, discord.ui.Button) and "NF & HPH402" in str(item.label):
                item.label = f"({len(self.nf_votes)}) NF & HPH402"
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def cancel_button(self, interaction, button):
        # Cancel button still requires staff/admin to prevent random deletions
        if any(role.id == STAFF_ROLE_ID for role in interaction.user.roles) or interaction.user.guild_permissions.administrator:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("loser 🤣😂", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(JoinButtonView())
        @self.tree.error
        async def on_app_command_error(interaction, error):
            if isinstance(error, app_commands.errors.MissingRole) or isinstance(error, app_commands.errors.MissingPermissions):
                await interaction.response.send_message("loser 🤣😂", ephemeral=True)
            else: raise error
        await self.tree.sync()

    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            count = len(member.guild.members)
            await channel.send(f"Welcome to the Province of Hillside, {member.mention}! You are member **#{count}**. Make sure to read the rules and enjoy your stay!")

    async def on_message(self, message):
        if message.author == self.user: return
        
        if message.channel.id == 1462097638102012054:
            content = message.content.strip()
            
            # --- SAY COMMAND (No Role Check) ---
            if content.lower().startswith("say "):
                parts = content.split()
                try:
                    target_id = int(parts[-1])
                    text_to_send = " ".join(parts[1:-1])
                    target_channel = self.get_channel(target_id)
                    if target_channel:
                        await target_channel.send(text_to_send)
                        await message.add_reaction("✅")
                except: 
                    await message.add_reaction("❌")

            # --- ADDROLE COMMAND (No Role Check) ---
            elif content.lower().startswith("addrole "):
                parts = content.split()
                if len(parts) == 3:
                    try:
                        user_id = int(parts[1])
                        role_id = int(parts[2])
                        member = message.guild.get_member(user_id)
                        role = message.guild.get_role(role_id)
                        
                        if member and role:
                            await member.add_roles(role)
                            await message.add_reaction("✅")
                        else:
                            await message.add_reaction("❌")
                    except:
                        await message.add_reaction("⚠️")

        await self.process_commands(message)

bot = MyBot()

# --- AOP & SSU SLASH COMMANDS (These still use @has_role) ---
# ... [Rest of the slash commands remain the same as previously provided] ...

bot.run(os.getenv('DISCORD_TOKEN'))
