import discord
import os
import time
from discord import app_commands
from discord.ext import commands
import json
import os

# --- CONFIGURATION (FILL THESE IN) ---
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
        # Calculate the end timestamp for the Discord dynamic time
        end_timestamp = int(time.time() + (self.time * 60))
        
        embed = discord.Embed(
            color=16533327,
            title="Server Start Up Poll",
            description=(
                f"{self.staff_member.mention} has started an ssu poll. "
                f"**{self.target}** votes are required to start up the server. "
                f"Poll lasts **{self.time}** minutes.\n\n"
                f"Poll ends: <t:{end_timestamp}:R>"
            )
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1322319257131946034/1441759845081546843/0a931781c210724549c829d241b0dc28_1.png")
        embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452718197714325565/image.png")
        
        # Adding the progress bar as a field so it doesn't clutter the description
        progress = min(count / self.target, 1.0)
        bar = "🟩" * int(progress * 10) + "⬜" * (10 - int(progress * 10))
        embed.add_field(name="Current Progress", value=f"{bar} ({count}/{self.target})", inline=False)
        
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
        # This bypasses the Server ID error and stops duplicates
        await self.tree.sync()
        print(f"Logged in as {self.user} - Global Sync Complete")

bot = MyBot()

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        count = len(member.guild.members)
        embed = discord.Embed(title="Welcome!", description=f"{member.mention} joined! Member **#{count}**", color=discord.Color.blue())
        await channel.send(embed=embed)

@bot.tree.command(name="ssupoll", description="Start an SSU interest check")
async def ssupoll(interaction: discord.Interaction, minutes: int, votes_needed: int):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    
    if not channel:
        return await interaction.response.send_message("Error: Session channel not found.", ephemeral=True)

    # We pass 'minutes' into the view so it can calculate the timestamp
    view = SessionVoteView(minutes, votes_needed, interaction.user)
    
    await channel.send(embed=view.create_embed(), view=view)
    await interaction.response.send_message(f"SSU Poll posted in <#{SESSION_CHANNEL_ID}>!", ephemeral=True)

@bot.tree.command(name="ssustart", description="Start the ERLC session")
async def ssustart(interaction: discord.Interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    
    if not channel:
        return await interaction.response.send_message("Error: Session channel not found.", ephemeral=True)

    # Get the current time for the dynamic timestamp
    current_timestamp = int(time.time())

    # Create the specialized embed
    embed = discord.Embed(
        color=16533327,
        title="Server Start Up",
        description=(
            "Our ingame server is now open. Members can now join the in game server for many good roleplays. "
            "Ensure you have read all of our ingame regulations that can be found in "
            "https://discord.com/channels/1336141468519239790/1337225457380098109.\n\n"
            "**Server**: `Hillside Provincial Roleplay I Strict I Canada`\n"
            "**Server Owner**: `xRectico`\n"
            "**Join Code**: `HillsideRP`\n\n"
            f"Session started: <t:{current_timestamp}:R>"
        )
    )
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1322319257131946034/1441759845081546843/0a931781c210724549c829d241b0dc28_1.png?ex=694a83fd&is=6949327d&hm=e1b895533edf161ba71d7aec82ad594053289ee91b6debab512e66798dd718a5&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452709174868971601/image.png?ex=694acc59&is=69497ad9&hm=35bd175de664960fd1a9b858fbdfb573d07b18fd1dc012308e5e5e86fdcba007&=&format=webp&quality=lossless")

    msg = await channel.send(embed=embed)
    save_msg_id(msg.id)
    await interaction.response.send_message(f"Session started in <#{SESSION_CHANNEL_ID}>!", ephemeral=True)

@bot.tree.command(name="ssushutdown", description="End current session")
async def ssushutdown(interaction: discord.Interaction):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    
    # 1. Get the current time for the dynamic timestamp
    current_timestamp = int(time.time())
    
    # 2. Try to delete the old "Session Started" message
    old_msg_id = load_msg_id()
    if old_msg_id:
        try:
            old_msg = await channel.fetch_message(old_msg_id)
            await old_msg.delete()
        except:
            pass # Ignore if the message was already deleted manually
            
    # 3. Create the Shutdown Embed
    embed = discord.Embed(
        color=16533327,
        title="Server Shutdown",
        description=(
            "Our ingame server is now closed. Please refrain from joining the "
            "ingame server as it is prohibited and you will be moderated.\n\n"
            f"Last session ended: <t:{current_timestamp}:R>"
        )
    )
    
    # Add the images you provided
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1322319257131946034/1441759845081546843/0a931781c210724549c829d241b0dc28_1.png?ex=694a83fd&is=6949327d&hm=e1b895533edf161ba71d7aec82ad594053289ee91b6debab512e66798dd718a5&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452651288012656673/image.png?ex=694a9670&is=694944f0&hm=eae11ac227e909bd3511827daed62cc5abee5b9effb12fb0e566303ee057d13a&=&format=webp&quality=lossless")

    # 4. Send the embed and clear the saved message ID
    await channel.send(embed=embed)
    save_msg_id(None)
    
    # 5. Confirm to the staff member that it worked
    await interaction.response.send_message("Session successfully ended!", ephemeral=True)

token = os.getenv('DISCORD_TOKEN')
bot.run(token)








