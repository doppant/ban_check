import discord
import asyncio

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
        
        selected_name = self.values[0]
        
        await interaction.response.defer(ephemeral=True)

        await interaction.delete_original_response()

        new_msg = await interaction.followup.send(
            f"{selected_name}",
            ephemeral=False
        )

        await asyncio.sleep(5)
        await new_msg.delete()