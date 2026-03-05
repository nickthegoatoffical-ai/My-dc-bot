import discord
from discord.ext import commands
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

delete_tracker = defaultdict(list)
ban_tracker = defaultdict(list)
message_tracker = defaultdict(list)

ANTI_RAID_THRESHOLD = 3
TIME_WINDOW = 10
TEMP_BAN_DURATION = 300

async def temp_ban(guild, user):
    try:
        await guild.ban(user, reason="Anti-Raid Protection Triggered")
        await asyncio.sleep(TEMP_BAN_DURATION)
        await guild.unban(user)
    except:
        pass

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        user = entry.user
        now = datetime.utcnow()
        delete_tracker[user.id].append(now)
        delete_tracker[user.id] = [t for t in delete_tracker[user.id] if (now - t).seconds < TIME_WINDOW]

        if len(delete_tracker[user.id]) >= ANTI_RAID_THRESHOLD:
            await temp_ban(channel.guild, user)

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        mod = entry.user
        now = datetime.utcnow()
        ban_tracker[mod.id].append(now)
        ban_tracker[mod.id] = [t for t in ban_tracker[mod.id] if (now - t).seconds < TIME_WINDOW]

        if len(ban_tracker[mod.id]) >= ANTI_RAID_THRESHOLD:
            await temp_ban(guild, mod)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = datetime.utcnow()
    message_tracker[message.author.id].append(now)
    message_tracker[message.author.id] = [
        t for t in message_tracker[message.author.id]
        if (now - t).seconds < 5
    ]

    if len(message_tracker[message.author.id]) >= 6:
        try:
            await message.author.timeout(timedelta(minutes=5))
        except:
            pass

    await bot.process_commands(message)

bot.run(os.getenv("TOKEN"))
