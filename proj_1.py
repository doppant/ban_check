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

    return list(chain.from_iterable(data[1:]))


def find_matches(scraped_data, db_names):
    return [name for name in scraped_data if name in db_names]