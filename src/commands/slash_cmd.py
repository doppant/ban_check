import discord
from discord import app_commands
import re
from src.database import postgree
from src.utils.check import name as check_name
from src.utils.util import run_db
from src.view.viewer import NameSelectView


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
                postgree.save_search,
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

        scraped_data = await run_db(check_name.get_data_from_url, url)
        db_postgre_rows = await run_db(postgree.get_all_with_users)
        
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

        data = await run_db(postgree.get_all_grouped)

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

        deleted_count = await run_db(
                            postgree.delete_name, 
                            str(interaction.user.id), 
                            name
                        )

        if deleted_count > 0:
            await interaction.followup.send(f"Deleted: {name}")
        else:
            await interaction.followup.send("Not found")