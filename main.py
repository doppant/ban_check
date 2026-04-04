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

    # 🔥 DEBUG SERVER & CHANNEL
    # print("\n=== DEBUG SERVER & CHANNEL ===")
    # for guild in bot.guilds:
    #     print(f"Server: {guild.name} (ID: {guild.id})")
    #     for ch in guild.channels:
    #         print(f" - {ch.name} | ID: {ch.id}")
    # print("================================\n")

    db_postgre.init_db()

    if not monitor_notice.is_running():
        monitor_notice.start()


# =====================
# GET CHANNEL SAFE
# =====================
async def get_channel_safe():
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print("⚠️ Channel not in cache, trying fetch...")
        try:
            channel = await bot.fetch_channel(CHANNEL_ID)
            print("✅ Channel fetched successfully")
        except Exception as e:
            print("❌ Channel fetch error:", e)
            return None

    return channel


# =====================
# AUTO BAN CHECK
# =====================
async def process_ban_notice(channel, url):
    await channel.send("🔍 Checking ban list...")

    try:
        scraped_data = check_name.get_data_from_url(url)
        db_rows = db_postgre.get_all_with_users()

        matches = check_name.find_matches(scraped_data, db_rows)

        if matches:
            msg_lines = [
                f"{ign.replace('*','x')} ~ {db_name} → {user}"
                for ign, db_name, user in matches
            ]

            await channel.send("🚨 MATCH FOUND:\n" + "\n".join(msg_lines))
        else:
            await channel.send("✅ No match found in ban list")

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
        print("No notice data")
        return

    print(f"Latest notice: {notice['id']} - {notice['title']}")

    if notice["id"] != last_notice_id:
        print("🔔 New notice detected")

        last_notice_id = notice["id"]

        channel = await get_channel_safe()

        if not channel:
            print("❌ Channel still not found")
            return

        await channel.send(
            f"📰 New Notice:\n{notice['title']}\n{notice['url']}"
        )

        if notice["is_ban"]:
            print("🚨 BAN NOTICE DETECTED")
            await channel.send("🚨 BAN NOTICE DETECTED!")
            await process_ban_notice(channel, notice["url"])
    else:
        print("No new notice")


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