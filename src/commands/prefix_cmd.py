import discord
from discord.ext import commands

from src.database import postgree
from src.utils.check import name as name_checker
from src.utils.util import run_db

# =====================
# Prefix Commands
# =====================
class PrefixCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def add(self, ctx, *, name):
        await run_db(postgree.save_search, str(ctx.author.id), str(ctx.author), name)
        await ctx.send(f"Saved: {name}")

    @commands.command()
    async def checkurl(self, ctx, url):
        msg = await ctx.send("Checking...")

        scraped_data = await run_db(name_checker.get_data_from_url, url)
        db_postgre_rows = await run_db(postgree.get_all_with_users)
        matches = name_checker.find_matches(scraped_data, db_postgre_rows)

        if matches:
            msg_lines = [
                f"{ign.replace('*','x')} ~ {db_name} → {user}"
                for ign, db_name, user in matches
            ]

            chunk = ""
            for line in msg_lines:
                if len(chunk) + len(line) > 1900:
                    await ctx.send(chunk)
                    chunk = ""
                chunk += line + "\n"

            if chunk:
                await ctx.send(chunk)
        else:
            await ctx.send("Tidak Ketemu")

        await msg.edit(content="Done!")

    @commands.command()
    async def list(self, ctx):
        data = await run_db(postgree.get_all_grouped)

        if not data:
            await ctx.send("📭 Database kosong.")
            return

        for user, names in data.items():
            msg = f"## {user}\n" + ", ".join(names)
            await ctx.send(msg)

    @commands.command()
    async def delete(self, ctx, *, name):
        deleted_count = await run_db(postgree.delete_name, str(ctx.author.id), name)
        await ctx.send(f"Deleted: {name}" if deleted_count > 0 else "Not found")


async def setup(bot):
    await bot.add_cog(PrefixCommands(bot))