import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio

import db_postgre
import check_name
import check_web

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

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
# SAFE CHANNEL GET
# =====================
async def get_channel_safe():
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print("⚠️ Channel not cached, fetching...")
        try:
            channel = await bot.fetch_channel(CHANNEL_ID)
            print("✅ Channel fetched")
        except Exception as e:
            print("❌ Fetch error:", e)
            return None

    return channel


# =====================
# BAN PROCESS
# =====================
async def process_ban_notice(channel, url):
    await channel.send("🔍 Checking ban list...")

    try:
        scraped_data = check_name.get_data_from_url(url)
        db_postgre_rows = db_postgre.get_all_with_users()

        matches = check_name.find_matches(scraped_data, db_postgre_rows)

        if matches:
            msg_lines = [
                f"{ign.replace('*','x')} ~ {db_postgre_name} → {user}"
                for ign, db_postgre_name, user in matches
            ]

            await channel.send("Ada:\n" + "\n".join(msg_lines))
            await channel.send("https://tenor.com/view/reza-auditore-gif-3484781624072545434")
        else:
            await channel.send("Tidak Ada")

    except Exception as e:
        await channel.send(f"Error: {e}")


# =====================
# LOOP
# =====================
@tasks.loop(seconds=60)
async def monitor_notice():
    global last_notice_id

    notice = check_web.get_latest_notice()

    if not notice:
        print("No data")
        return

    print(f"Latest: {notice['id']}")

    if notice["id"] != last_notice_id:
        print("New notice!")

        last_notice_id = notice["id"]

        if not notice["is_ban"]:
            print("Skip non-ban notice")
            return

        channel = await get_channel_safe()

        if not channel:
            print("Channel not found")
            return

        await channel.send(
            f"📰 {notice['title']}\n{notice['ban_url']}"
        )

        if notice["is_ban"]:
            print("BAN DETECTED")
            await process_ban_notice(channel, notice["ban_url"])
    else:
        print("No update")

# =====================
# UTILITY: RUN IN THREAD
# =====================
# Fungsi ini penting agar database yang lambat tidak membuat bot "pingsan"
async def run_db(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


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
    db_postgre_rows = db_postgre.get_all_with_users()

    matches = check_name.find_matches(scraped_data, db_postgre_rows)

    if matches:
        msg_lines = [
            f"{ign.replace('*','x')} ~ {db_postgre_name} → {user}"
            for ign, db_postgre_name, user in matches
        ]
        await ctx.send("Ada:\n" + "\n".join(msg_lines))
    else:
        await ctx.send("Tidak Ketemu")


@bot.command()
async def list(ctx):
    data = await run_db(db_postgre.get_all_grouped)

    loading = await ctx.send("Mengambil data ....")

    if not data:
        await loading.edit(content="📭 Database kosong.")
        return

    await loading.delete()

    for user, names in data.items():
        msg = f"## {user}\n" + ", ".join(names)
        await ctx.send(msg)


@bot.command()
async def delete(ctx, *, name):
    deleted_count = db_postgre.delete_name(str(ctx.author.id), name)

    if deleted_count > 0:
        await ctx.send(f"Deleted: {name}")
    else:
        await ctx.send("Not found")


# =====================
# RUN
# =====================
bot.run(TOKEN)