import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os

import db_postgre
import check_name
import check_web

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# === CONFIG ===
CHANNEL_ID = os.getenv("CHANNEL_ID")
last_notice_id = None


# =====================
# EVENT
# =====================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    db_postgre.init_db()

    if not monitor_notice.is_running():
        monitor_notice.start()


# =====================
# AUTO BAN CHECK
# =====================
async def process_ban_notice(channel, url):
    await channel.send("🔍 Checking...")

    try:
        scraped_data = check_name.get_data_from_url(url)
        db_rows = db_postgre.get_all_with_users()

        matches = check_name.find_matches(scraped_data, db_rows)

        if matches:
            msg_lines = [
                f"{ign.replace('*','x')} ~ {db_name} → {user}"
                for ign, db_name, user in matches
            ]

            await channel.send(
                "🚨 Ada:\n" + "\n".join(msg_lines)
            )
            await channel.send("https://tenor.com/view/reza-auditore-gif-3484781624072545434")
        else:
            await channel.send("Tidak Ada")

    except Exception as e:
        await channel.send(f"Error while checking ban list: {e}")


# =====================
# BACKGROUND TASK
# =====================
@tasks.loop(seconds=60)
async def monitor_notice():
    global last_notice_id

    notice = check_web.get_latest_notice()

    if not notice:
        return

    # notice baru
    if notice["id"] != last_notice_id:
        last_notice_id = notice["id"]

        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("Channel not found!")
            return

        # kirim info notice
        await channel.send(
            f"📰 Ada yang baru:\n{notice['title']}\n{notice['url']}"
        )

        # kalau ban → auto check
        if notice["is_ban"]:
            await channel.send("🚨 Absen!")
            await process_ban_notice(channel, notice["url"])


# =====================
# COMMANDS
# =====================
@bot.command()
async def add(ctx, *, name):
    db_postgre.save_search(str(ctx.author.id), str(ctx.author), name)
    await ctx.send(f"Saved: {name}")


@bot.command()
async def checkurl(ctx, url):
    await ctx.send("Checking...")

    scraped_data = check_name.get_data_from_url(url)
    db_rows = db_postgre.get_all_with_users()

    matches = check_name.find_matches(scraped_data, db_rows)

    if matches:
        msg_lines = [
            f"{ign.replace('*','x')} ~ {db_name} → {user}"
            for ign, db_name, user in matches
        ]
        await ctx.send("Ada:\n" + "\n".join(msg_lines))
        await ctx.send("https://tenor.com/view/reza-auditore-gif-3484781624072545434")
    else:
        await ctx.send("Tidak Ketemu")


@bot.command()
async def list(ctx):
    data = db_postgre.get_all_grouped()

    if not data:
        await ctx.send("No data found")
        return

    messages = []

    for user, names in data.items():
        section = f"## {user}\n" + ", ".join(names)
        messages.append(section)

    full_message = "\n\n".join(messages)

    for i in range(0, len(full_message), 1900):
        await ctx.send(full_message[i:i+1900])


@bot.command()
async def delete(ctx, *, name):
    deleted_count = db_postgre.delete_name(str(ctx.author.id), name)

    if deleted_count > 0:
        await ctx.send(f"Deleted: {name}")
    else:
        await ctx.send(f"No matching name found for {name}")


# =====================
# RUN
# =====================
bot.run(TOKEN)