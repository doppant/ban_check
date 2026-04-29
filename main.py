import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio

from src.database import postgree
from src.utils.check import name as name_checker
from src.utils.check import web
from src.utils.util import run_db, get_asset
from src.commands.slash_cmd import AionGroup


load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
last_notice_id = None


# =====================
# EVENT
# =====================
@bot.event
async def on_ready():
    global last_notice_id
    print(f"Logged in as {bot.user}")

    await run_db(postgree.init_db)

    last_notice_id = await run_db(postgree.get_last_article_id)
    print("Last article from DB:", last_notice_id)

    if not any(cmd.name == "aion" for cmd in bot.tree.get_commands()):
        bot.tree.add_command(AionGroup())
    await bot.tree.sync()

    print("Slash command synced")

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
    try:
        scraped_data = name_checker.get_data_from_url(url)
        db_postgre_rows = await run_db(postgree.get_all_with_users)

        matches = name_checker.find_matches(scraped_data, db_postgre_rows)

        if matches:
            msg_lines = [
                f"{ign.replace('*','x')} ~ {db_postgre_name} → {user}"
                for ign, db_postgre_name, user in matches
            ]

            chunk = ""
            for line in msg_lines:
                if len(chunk) + len(line) > 1900:
                    await channel.send(chunk)
                    chunk = ""
                chunk += line + "\n"

            if chunk:
                await channel.send("Ada:\n" + chunk)
                await channel.send(get_asset(
                                        "gifs", 
                                        "ban")
                                    )
        else:
            await channel.send("Tidak Ada")

    except Exception as e:
        await channel.send(f"Error: {e}")

async def load_extensions():
    await bot.load_extension("src.commands.prefix_cmd")
    print("✅ Prefix commands loaded")


# =====================
# LOOP
# =====================
@tasks.loop(seconds=60)
async def monitor_notice():
    global last_notice_id

    try:
        notice = await run_db(web.get_latest_notice)
    except Exception as e:
        print("Loop error:", e)
        return

    if not notice:
        print("No data")
        return

    print(f"Latest: {notice['id']}")
    print(f"Last DB ID: {last_notice_id}")

    if last_notice_id is None:
        await run_db(postgree.update_last_article, notice["id"])
        last_notice_id = notice["id"]
        return

    if notice["id"] == last_notice_id:
        print("No update")
        return

    print("New notice!")

    await run_db(postgree.update_last_article, notice["id"])
    last_notice_id = notice["id"]

    if not notice["is_ban"]:
        print("Skip non-ban notice")
        return

    channel = await get_channel_safe()
    if not channel:
        return

    await channel.send(f"📰 {notice['title']}\n{notice['ban_url']}")

    print("BAN DETECTED")
    await process_ban_notice(channel, notice["ban_url"])

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

# =====================
# RUN
# =====================

if __name__ == "__main__":
    asyncio.run(main())