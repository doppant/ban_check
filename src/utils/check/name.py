import requests
from bs4 import BeautifulSoup
from itertools import chain
import re
import json


def get_data_from_url(url):
    try:
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            print("❌ Failed request:", res.status_code)
            return []

        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        table = soup.find("table")

        if not table:
            print("❌ Table not found in page")
            return []

        data = []

        for row in table.find_all("tr"):
            cols = [col.get_text(strip=True) for col in row.find_all(["td", "th"])]
            if cols:
                data.append(cols)

        if len(data) <= 1:
            print("❌ No data rows")
            return []

        # flatten (skip header)
        all_data = list(chain.from_iterable(data[1:]))

        print(f"✅ Scraped {len(all_data)} entries")

        return all_data

    except Exception as e:
        print("❌ get_data_from_url error:", e)
        return []


def find_matches(scraped_data, db_rows):
    matches = []

    for discord_name, db_name in db_rows:
        # db_name = db_name.lower()

        for ign in scraped_data:
            # ign_clean = ign.lower()

            if len(ign) < 2 or len(db_name) < 2:
                continue

            if (
                ign[:2] == db_name[:2] and
                len(ign) == len(db_name)
            ):
                matches.append((ign, db_name, discord_name))

    # remove duplicate
    return list(set(matches))

def get_character_details(link: str) -> tuple[str | None, str | None]:
    search_url = "https://aion2tool.com/api/character/search"
    
    # Ekstrak server_id dan nama dari Link menggunakan regex
    match = re.search(r"serverid=(\d+)/([^/]+)$", link)

    if not match:
        print(f"[Error] Format link tidak valid: {link}")
        return None, None

    server_id = int(match.group(1))
    name = match.group(2)
    
    payload = {
        "race": str(server_id)[0],             
        "server_id": server_id, 
        "keyword": name         
    }
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://aion2tool.com",
        "Referer": "https://aion2tool.com/"
    }

    try:
        r = requests.post(
            search_url,
            json=payload,
            headers=headers,
            timeout=15
        )

        if r.status_code != 200:
            print(f"[API Error] Status code: {r.status_code}")
            return None, None

        data = r.json()
        
        # Ambil list karakter dari key "data"
        character_list = data.get("data", [])
        
        # Jika responsenya berbentuk LIST (karena hasil search keyword)
        if isinstance(character_list, list):
            for char in character_list:
                # Cari yang namanya benar-benar pas (case-insensitive)
                if char.get("name", "").lower() == name.lower():
                    job_class = char.get("job")
                    
                    # Ambil nama server atau ID server dari response API
                    server_res = char.get("server") or char.get("server_id") or server_id
                    
                    # Return dalam bentuk (class, server) string
                    return str(job_class), str(server_res)
                    
        # Jika responsenya ternyata langsung berbentuk DICT satu karakter
        elif isinstance(character_list, dict):
            job_class = character_list.get("job")
            server_res = character_list.get("server") or server_id
            return str(job_class), str(server_res)

        print(f"❌ Karakter {name} tidak ditemukan di hasil API pencarian.")
        return None, None

    except Exception as e:
        print(f"❌ Gagal memproses JSON atau request bermasalah: {e}")
        return None, None    