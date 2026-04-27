import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import os
import asyncio
import re

import db_postgre
import check_name
import check_web

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

    await run_db(db_postgre.init_db)

    last_notice_id = await run_db(db_postgre.get_last_article_id)
    print("Last article from DB:", last_notice_id)

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
    await channel.send("🔍 Checking ban list...")

    try:
        scraped_data = check_name.get_data_from_url(url)
        db_postgre_rows = await run_db(db_postgre.get_all_with_users)

        matches = check_name.find_matches(scraped_data, db_postgre_rows)

        if matches:
            msg_lines = [
                f"{ign.replace('*','x')} ~ {db_postgre_name} → {user}"
                for ign, db_postgre_name, user in matches
            ]

            await channel.send("Ada:\n" + "\n".join(msg_lines))
            await channel.send("https://cdn.discordapp.com/attachments/1445229252881682452/1458461450807804104/202601072043_1.gif")
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
    print(f"Last DB ID: {last_notice_id}")

    if last_notice_id is None:
        await run_db(db_postgre.update_last_article, notice["id"])
        last_notice_id = notice["id"]
        print("Initialized last_notice_id")
        return

    if notice["id"] != last_notice_id:
        print("New notice!")

        await run_db(
            db_postgre.update_last_article,
            notice["id"]
        )

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
    try:
        return await loop.run_in_executor(None, func, *args)
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return None # Kembalikan None agar loop tidak crash
    
# =====================
# UI NAME LISTS
# =====================
class NameSelectView(discord.ui.View):
    def __init__(self, names):
        super().__init__(timeout=60) # Menu hilang dalam 60 detik
        
        # Batasi maksimal 25 opsi (Limit Discord)
        options = [
            discord.SelectOption(label=name, description=f"Klik untuk Menampilkan nama {name}")
            for name in names[:25]
        ]

        self.add_item(NameDropdown(options))

class NameDropdown(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Pilih nama untuk ditampilkan...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Ini akan mengirim pesan baru yang bisa dilihat semua orang
        selected_name = self.values[0]
        await interaction.response.send_message(
            f"{selected_name}",
            ephemeral=False  # Ini kuncinya agar dilihat banyak orang
        )

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
    db_postgre_rows = await run_db(db_postgre.get_all_with_users)

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
# SLASH GROUP: /aion
# =====================
class AionGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="aion", description="Ban checking system")

    # /ban add
    @app_commands.command(name="add", description="Tambah nama ke database")
    async def add_names(self, interaction: discord.Interaction, names: str):

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        saved_names = []
        split_names = re.split(r'[,\s]+', names.strip())

        for name in split_names:
            if not name:
                continue

            await run_db(
                db_postgre.save_search,
                str(interaction.user.id),
                str(interaction.user),
                name
            )
            saved_names.append(name)

        await interaction.followup.send(f"Saved: {', '.join(saved_names)}")

    # /ban checkurl
    @app_commands.command(name="checkurl", description="Cek URL ban secara manual")
    async def checkurl(self, interaction: discord.Interaction, url: str):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        scraped_data = check_name.get_data_from_url(url)
        db_postgre_rows = db_postgre.get_all_with_users()
        
        await interaction.followup.send("Checking...")

        matches = check_name.find_matches(scraped_data, db_postgre_rows)

        if matches:
            msg_lines = [
                f"{ign.replace('*','x')} ~ {db_postgre_name} → {user}"
                for ign, db_postgre_name, user in matches
            ]
            await interaction.followup.send("Ada:\n" + "\n".join(msg_lines))
        else:
            await interaction.followup.send("Tidak Ketemu")

    # /ban list
    @app_commands.command(name="list", description="Lihat daftar nama")
    @app_commands.describe(user="Filter berdasarkan user")
    async def list(self, interaction: discord.Interaction, user: discord.User | None = None):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        data = await run_db(db_postgre.get_all_grouped)

        if not data:
            await interaction.followup.send("📭 Database kosong atau error.", ephemeral=True)
            return

        # ========================
        # MODE FILTER USER (Pakai Dropdown)
        # ========================
        if user:
            user_name = str(user)
            if user_name not in data:
                await interaction.followup.send(f"❌ Tidak ada data untuk {user_name}", ephemeral=True)
                return

            names = data[user_name]
            view = NameSelectView(names)
            await interaction.followup.send(
                f"Berikut daftar nama milik **{user_name}**:",
                view=view,
                ephemeral=True
            )
            return # Keluar dari fungsi setelah kirim dropdown

        # ========================
        # MODE SEMUA USER (Teks Biasa)
        # ========================
        full_message = ""
        for user_name, names in data.items():
            section = f"## {user_name}\n" + ", ".join(names) + "\n\n"
            # Cek limit karakter Discord (2000)
            if len(full_message) + len(section) > 2000:
                await interaction.followup.send(full_message, ephemeral=True)
                full_message = section
            else:
                full_message += section

        if full_message:
            await interaction.followup.send(full_message, ephemeral=True)

    # /ban delete
    @app_commands.command(name="delete", description="Hapus nama dari database")
    async def delete(self, interaction: discord.Interaction, name: str):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        deleted_count = db_postgre.delete_name(
            str(interaction.user.id),
            name
        )

        if deleted_count > 0:
            await interaction.followup.send(f"Deleted: {name}")
        else:
            await interaction.followup.send("Not found")


# =====================
# RUN
# =====================

bot.tree.add_command(AionGroup())
bot.run(TOKEN)