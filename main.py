import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

# from db import init_db, save_search, get_all_names, get_all_grouped
# from check_name import get_data_from_url, find_matches
import db
import check_name


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    db.init_db()


@bot.command()
async def add(ctx, *, name):
    db.save_search(str(ctx.author.id), str(ctx.author), name)
    await ctx.send(f"Saved: {name}")


@bot.command()
async def checkurl(ctx, url):
    await ctx.send("Checking...")

    scraped_data = check_name.get_data_from_url(url)
    db_rows = db.get_all_with_users()  # ambil tuple (discord_name, name)

    matches = check_name.find_matches(scraped_data, db_rows)

    if matches:
        msg_lines = [f"{ign} → {user}" for ign, user in matches]
        await ctx.send("Matched:\n" + "\n".join(msg_lines))
    else:
        await ctx.send("No matches found")

@bot.command()
async def list(ctx):
    data = db.get_all_grouped()

    if not data:
        await ctx.send("No data found")
        return

    messages = []

    for user, names in data.items():
        section = f"## {user}\n" + ", ".join(names)
        messages.append(section)

    full_message = "\n\n".join(messages)

    # handle limit discord
    for i in range(0, len(full_message), 1900):
        await ctx.send(full_message[i:i+1900])

@bot.command()
async def delete(ctx, *, name):
    deleted_count = db.delete_name(str(ctx.author.id), name)

    if deleted_count > 0:
        await ctx.send(f"Deleted: {name}")
    else:
        await ctx.send(f"No matching name found for {name}")


bot.run(TOKEN)