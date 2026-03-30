import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

from db import init_db, save_search, get_all_names
from check_name import get_data_from_url, find_matches

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

TOKEN = os.getenv("DISCORD_TOKEN")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    init_db()


@bot.command()
async def add(ctx, *, name):
    save_search(str(ctx.author.id), str(ctx.author), name)
    await ctx.send(f"Saved: {name}")


@bot.command()
async def checkurl(ctx, url):
    await ctx.send("Checking...")

    scraped_data = get_data_from_url(url)
    db_names = get_all_names()

    matches = find_matches(scraped_data, db_names)

    if matches:
        await ctx.send(f"Matched: {', '.join(matches)}")
    else:
        await ctx.send("No matches found")


bot.run(TOKEN)