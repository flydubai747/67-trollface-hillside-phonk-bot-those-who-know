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

# Dictionary to keep track of active views in memory for pinging
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
    async def vote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.voters: 
            self.voters.remove(interaction.user.id)
        else: 
            self.voters.add(interaction.user.id)
        button.label = f"({len(self.voters)}) Vote"
        if len(self.voters) >= self.target and not self.goal_notified:
            self.goal_notified = True
            log_chan = interaction.client.get_channel(STAFF_LOG_CHANNEL_ID)
            if log_chan:
                await log_chan.send(f"🔔 {self.staff_member.mention}, the SSU poll has reached the goal of **{self.target}** votes!")
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="(0) NF & HPH402", style=discord.ButtonStyle.gray, emoji="<:northwindfalls:1462090977291403409>", row=0)
    async def nf_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.hc_votes: self.hc_votes.remove(interaction.user.id)
        if interaction.user.id in self.nf_votes: self.nf_votes.remove(interaction.user.id)
        else: self.nf_votes.add(interaction.user.id)
        button.label = f"({len(self.nf_votes)}) NF & HPH402"
        for item in self.children:
            if isinstance(item, discord.ui.Button) and "Hillside City" in str(item.label):
                item.label = f"({len(self.hc_votes)}) Hillside City"
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="(0) Hillside City", style=discord.ButtonStyle.gray, emoji="<:hillsidecity:1453055474101391558>", row=0)
    async def hc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.nf_votes: self.nf_votes.remove(interaction.user.id)
        if interaction.user.id in self.hc_votes: self.hc_votes.remove(interaction.user.id)
        else: self.hc_votes.add(interaction.user.id)
        button.label = f"({len(self.hc_votes)}) Hillside City"
        for item in self.children:
            if isinstance(item, discord.ui.Button) and "NF & HPH402" in str(item.label):
                item.label = f"({len(self.nf_votes)}) NF & HPH402"
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
        self.add_view(JoinButtonView())
        await self.tree.sync()

    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            member_count = len(member.guild.members)
            embed = discord.Embed(
                title="Welcome to Hillside Provincial Roleplay!",
                description=f"Welcome {member.mention} to the server! You are member **#{member_count}**. Make sure to read the rules and enjoy your stay.",
                color=16533327
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Hillside RP | Member Count: {member_count}")
            await channel.send(embed=embed)

    async def on_message(self, message):
        if message.author == self.user: return
        if message.channel.id == 1443909455866626240:
            content = message.content.strip()
            if content.lower().startswith("say "):
                parts = content.split()
                if len(parts) >= 3:
                    try:
                        target_id = int(parts[-1])
                        text_to_send = " ".join(parts[1:-1])
                        target_channel = self.get_channel(target_id)
                        if target_channel:
                            await target_channel.send(text_to_send)
                            await message.add_reaction("✅")
                    except: pass
        await self.process_commands(message)

bot = MyBot()

# --- COMMANDS ---

@bot.tree.command(name="ssupoll", description="Start SSU & AOP Poll")
async def ssupoll(interaction: discord.Interaction, minutes: int, votes_needed: int):
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    async for message in channel.history(limit=5):
        if message.author == bot.user and message.embeds:
            if "Server Shutdown" in str(message.embeds[0].title):
                try: await message.delete()
                except: pass
    view = SessionVoteView(minutes, votes_needed, interaction.user)
    msg = await channel.send(content=f"<@&{PING_ROLE_ID}>", embed=view.create_embed(), view=view)
    save_msg_id(msg.id) 
    # Store the view in our dictionary so we can access voters later
    active_polls[msg.id] = view
    await interaction.response.send_message("Poll posted!", ephemeral=True)

@bot.tree.command(name="ssustart", description="Start session and post AOP winner")
async def ssustart(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(SESSION_CHANNEL_ID)
    old_id = load_msg_id()
    winning_aop = "NF & HPH402" 
    voter_pings = ""
    
    if old_id:
        # Check if the poll is in our memory
        if old_id in active_polls:
            view = active_polls[old_id]
            # Create a string of pings for everyone who voted
            if view.voters:
                voter_pings = " ".join([f"<@{v_id}>" for v_id in view.voters])
            
            # Decide winning AOP based on view data
            if len(view.hc_votes) > len(view.nf_votes):
                winning_aop = "Hillside City"
            
            # Clean up the memory
            del active_polls[old_id]

        try:
            old_msg = await channel.fetch_message(old_id)
            await old_msg.delete()
        except: pass

    main_embed = discord.Embed(
        color=16533327, title="Server Start Up",
        description=(f"Our ingame server is now open, ensure you follow all rules found in https://discord.com/channels/1336141468519239790/1337225457380098109.\n\n"
                     f"**Server**: `Hillside Provincial Roleplay I Strict I Canada`\n"
                     f"**Owner**: `xRectico`\n"
                     f"**Join Code**: `{SERVER_JOIN_CODE}`\n\n"
                     f"Session started: <t:{int(time.time())}:R>")
    )
    main_embed.set_thumbnail(url="https://media.discordapp.net/attachments/1322319257131946034/1441759845081546843/0a931781c210724549c829d241b0dc28_1.png")
    main_embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1452709174868971601/image.png")

    if winning_aop == "Hillside City":
        aop_embed = discord.Embed(color=16533327, description="### The area of play ingame is <:hillsidecity:1453055474101391558> [Hillside City](https://media.discordapp.net/attachments/1322319257131946034/1446923553894170801/hillside_hillside_city_aop_map.png)")
        aop_embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1446923553894170801/hillside_hillside_city_aop_map.png")
    else:
        aop_embed = discord.Embed(color=16533327, description="### The area of play ingame is <:northwindfalls:1462090977291403409> [Northwind Falls](https://media.discordapp.net/attachments/1322319257131946034/1446923555743993926/hillside_nf_and_hph402_aop_map.png) and <:hph402:1455577343132307476> [Hillside Provincial Highway 402](https://cdn.discordapp.com/attachments/1453065520390607050/1453065558709764258/tiny_transparent.png)")
        aop_embed.set_image(url="https://media.discordapp.net/attachments/1322319257131946034/1446923555743993926/hillside_nf_and_hph402_aop_map.png")

    # This sends the start message, the role ping, AND the voter pings
    full_content = f"<@&{PING_ROLE_ID}> **The session is now starting!**\n{voter_pings}"
    await channel.send(content=full_content, embed=main_embed, view=JoinButtonView())
    aop_msg = await channel.send(embed=aop_embed)
    save_msg_id(aop_msg.id) 
    await interaction.followup.send("Session started!")

# ... (aopmw, aopnf, aophs, aopnfhph, aopnfhphnrnp, and ssushutdown remain the same) ...

bot.run(os.getenv('DISCORD_TOKEN'))
