import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
import asyncio
from collections import defaultdict

welcome_cache = set()

async def clear_welcome_cache(user_id):
    await asyncio.sleep(60)
    welcome_cache.discard(user_id)

# =========================
# TOKEN
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ No TOKEN")

# =========================
# INTENTS
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# DATA
# =========================
FILE = "data.json"

def load():
    try:
        with open(FILE,"r") as f:
            data = json.load(f)

        data.setdefault("autoroles", {"user": [], "bot": []})
        data.setdefault("warns", {})

        return data

    except:
        return {"warns": {}, "autoroles": {"user": [], "bot": []}}

def save():
    with open(FILE,"w") as f:
        json.dump(data, f, indent=4)

data = load()

# =========================
# SYSTEMS
# =========================
xp = defaultdict(int)
level = defaultdict(int)
spam = defaultdict(list)
join_tracker = []

LOG_CHANNEL_ID = 1454399890405851198

# =========================
# STATUS BOT
# =========================
async def status_loop():
    await bot.wait_until_ready()

    while not bot.is_closed():

        total = sum(g.member_count for g in bot.guilds)

        online = sum(
            1 for g in bot.guilds
            for m in g.members
            if m.status != discord.Status.offline
        )

        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{total} miembros | {online} online"
            )
        )

        await asyncio.sleep(60)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print(f"BOT ACTIVO {bot.user}")
    await bot.tree.sync()
    asyncio.create_task(status_loop())

# =========================
# WELCOME + AUTO ROLE (FIXED)
# =========================
@bot.event
async def on_member_join(member):

    if member.id in welcome_cache:
        return

    welcome_cache.add(member.id)
    asyncio.create_task(clear_welcome_cache(member.id))

    # ANTI RAID
    now = datetime.datetime.utcnow().timestamp()
    join_tracker.append(now)
    join_tracker[:] = [t for t in join_tracker if now - t < 10]

    if len(join_tracker) >= 5:
        for c in member.guild.text_channels:
            try:
                await c.set_permissions(member.guild.default_role, send_messages=False)
            except:
                pass

    # =========================
    # AUTO ROLE 🔥 ARREGLADO PRO
    # =========================
    tipo = "bot" if member.bot else "user"
    roles = data["autoroles"].get(tipo, [])

    if not isinstance(roles, list):
        roles = [roles]

    for role_id in roles:
        try:
            role = discord.utils.get(member.guild.roles, id=int(role_id))
            if role:
                await member.add_roles(role, reason="Autorole system")
        except:
            pass

    # =========================
    # WELCOME
    # =========================
    ch = member.guild.get_channel(LOG_CHANNEL_ID)

    if ch:
        embed = discord.Embed(
            title="🔥 BIENVENIDO A GUATE XITER 🔥",
            description=f"""
👤 {member.mention}

✅ 100% confiables: trabajamos sin estafas, sin engaños y con total transparencia.
⚡ Servicio rápido y eficiente: entregas inmediatas y soporte activo.
🔒 Seguridad garantizada: protegemos a nuestros clientes en todo momento.
📈 Top 1 en confianza: cada día más personas nos eligen por nuestra reputación.
🤝 Atención personalizada: siempre estamos para ayudarte.

REVISA NUESTROS CANALES

REGLAS
No te hagas pasar por alguien mas ni uses imagenes de perfil inapropiadas; No se permiten nombres de usuarios o imagenes inapropiadas o irrespetuosas.
https://discord.com/channels/1454399889604608064/1480435358964645939
REDES
https://discord.com/channels/1454399889604608064/1484708297104818317
https://discord.com/channels/1454399889604608064/1484708228674883725
PARA COMPRAR Y RECOMENDACIONES
https://discord.com/channels/1454399889604608064/1484371103605461012
https://discord.com/channels/1454399889604608064/1484424979272695838
https://discord.com/channels/1454399889604608064/1484425102819983500

""",
            color=0xff0000
        )

        embed.set_image(url="https://images-ext-1.discordapp.net/external/F4k_qFjcE9WKfv-6kIwnREYX_3CeHj_dmUE2sY1LmiQ/https/image2url.com/r2/bucket1/images/1775964084960-ad8bbae0-d686-491a-b3b3-34da64837ff8.png?format=webp&quality=lossless&width=754&height=940")
        embed.set_thumbnail(url=member.display_avatar.url)

        await ch.send(embed=embed)

# =========================
# XP + ANTI SPAM + LINK
# =========================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    uid = str(message.author.id)

    xp[uid] += 5
    if xp[uid] % 100 == 0:
        level[uid] += 1

    now = datetime.datetime.utcnow().timestamp()

    spam[uid].append(now)
    spam[uid] = [t for t in spam[uid] if now - t < 5]

    if len(spam[uid]) > 5:
        await message.delete()
        return

    if "http" in message.content or "discord.gg" in message.content:
        await message.delete()
        return

    await bot.process_commands(message)

# =========================
# CLEAR
# =========================
@bot.tree.command(name="clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 {amount} mensajes borrados", ephemeral=True)

# =========================
# BAN / KICK / TIMEOUT
# =========================
@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction, member: discord.Member):
    await member.ban()
    await interaction.response.send_message("🔨 baneado")

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message("👢 kick")

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction, member: discord.Member, minutes: int):
    await member.timeout(datetime.timedelta(minutes=minutes))
    await interaction.response.send_message("⏳ timeout")

# =========================
# INFO
# =========================
@bot.tree.command(name="info")
async def info(interaction):

    g = interaction.guild

    online = sum(1 for m in g.members if m.status != discord.Status.offline)
    bots = sum(m.bot for m in g.members)

    embed = discord.Embed(title="📊 INFO SERVER", color=0xff0000)
    embed.add_field(name="👥 Miembros", value=g.member_count)
    embed.add_field(name="🟢 Online", value=online)
    embed.add_field(name="🤖 Bots", value=bots)
    embed.add_field(name="🚀 Boosts", value=g.premium_subscription_count)

    await interaction.response.send_message(embed=embed)

# =========================
# ONLINE
# =========================
@bot.tree.command(name="online")
async def online(interaction):
    online = sum(1 for m in interaction.guild.members if m.status != discord.Status.offline)
    await interaction.response.send_message(f"🟢 Online: {online}")

# =========================
# MEMBERS
# =========================
@bot.tree.command(name="members")
async def members(interaction):
    await interaction.response.send_message(f"👥 {interaction.guild.member_count}")

# =========================
# BOOSTS
# =========================
@bot.tree.command(name="boosts")
async def boosts(interaction):
    await interaction.response.send_message(f"🚀 {interaction.guild.premium_subscription_count}")

# =========================
# PING
# =========================
@bot.tree.command(name="ping")
async def ping(interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency*1000)}ms")

# =========================
# USERINFO
# =========================
@bot.tree.command(name="userinfo")
async def userinfo(interaction, member: discord.Member=None):

    member = member or interaction.user

    embed = discord.Embed(title="USER INFO")
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Creado", value=member.created_at)

    await interaction.response.send_message(embed=embed)

# =========================
# AVATAR
# =========================
@bot.tree.command(name="avatar")
async def avatar(interaction, member: discord.Member=None):

    member = member or interaction.user

    embed = discord.Embed()
    embed.set_image(url=member.display_avatar.url)

    await interaction.response.send_message(embed=embed)

# =========================
# SERVER BANNER
# =========================
@bot.tree.command(name="guildbanner")
async def guildbanner(interaction):

    g = interaction.guild

    if not g.banner:
        return await interaction.response.send_message("sin banner")

    embed = discord.Embed()
    embed.set_image(url=g.banner.url)

    await interaction.response.send_message(embed=embed)

# =========================
# USER BANNER
# =========================
@bot.tree.command(name="banner")
async def banner(interaction, member: discord.Member=None):

    member = member or interaction.user
    user = await bot.fetch_user(member.id)

    if not user.banner:
        return await interaction.response.send_message("sin banner")

    embed = discord.Embed()
    embed.set_image(url=user.banner.url)

    await interaction.response.send_message(embed=embed)

# =========================
# AUTOROLE FIX
# =========================
class RoleSelect(discord.ui.Select):
    def __init__(self, roles, tipo):

        self.tipo = tipo

        options = [
            discord.SelectOption(label=r.name, value=str(r.id))
            for r in roles if r.name != "@everyone"
        ][:25]

        super().__init__(
            placeholder="Selecciona roles",
            options=options,
            min_values=1,
            max_values=len(options)
        )

    async def callback(self, interaction: discord.Interaction):

        data["autoroles"][self.tipo] = [int(v) for v in self.values]
        save()

        await interaction.response.send_message("✔ Autoroles guardados", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self, roles, tipo):
        super().__init__(timeout=60)
        self.add_item(RoleSelect(roles, tipo))

@bot.tree.command(name="autorole_add")
async def autorole_add(interaction: discord.Interaction, tipo: str):

    if tipo not in ["user","bot"]:
        return await interaction.response.send_message("user o bot", ephemeral=True)

    await interaction.response.send_message(
        "Selecciona roles:",
        view=RoleView(interaction.guild.roles, tipo),
        ephemeral=True
    )

# =========================
# RUN
# =========================
bot.run(TOKEN)