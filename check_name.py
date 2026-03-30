import requests
from bs4 import BeautifulSoup
from itertools import chain


def get_data_from_url(url):
    res = requests.get(url)
    res.encoding = res.apparent_encoding

    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table")
    data = []

    for row in table.find_all("tr"):
        cols = [col.get_text(strip=True) for col in row.find_all(["td", "th"])]
        if cols:
            data.append(cols)

    all_data = list(chain.from_iterable(data[1:]))

    return all_data


def find_matches(scraped_data, db_rows):
    """
    db_rows: list of tuples (discord_name, name)
    scraped_data: list of IGN from URL
    return: list of tuples (ign_from_web, discord_name)
    """
    matches = []

    for discord_name, db_name in db_rows:
        for ign in scraped_data:
            if len(ign) < 2 or len(db_name) < 2:
                continue

            # match 2 huruf pertama + panjang
            if (ign[:2] == db_name[:2]) and (len(ign) == len(db_name)):
                matches.append((ign, discord_name))

    # remove duplicate
    return list(set(matches))