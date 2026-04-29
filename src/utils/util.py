import asyncio
import json
from pathlib import Path

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

def get_asset(category, key):
    path = Path(__file__).resolve().parent.parent.parent / "media" / "assets.json"
    with open(path, "r") as f:
        data = json.load(f)
    return data.get(category, {}).get(key)