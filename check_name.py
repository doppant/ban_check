import requests
from bs4 import BeautifulSoup
from itertools import chain

# def get_data_from_url(url):
#     res = requests.get(url)
#     res.encoding = res.apparent_encoding

#     soup = BeautifulSoup(res.text, "html.parser")

#     table = soup.find("table")
#     data = []

#     for row in table.find_all("tr"):
#         cols = [col.get_text(strip=True) for col in row.find_all(["td", "th"])]
#         if cols:
#             data.append(cols)

#     all_data = list(chain.from_iterable(data[1:]))

#     return all_data

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