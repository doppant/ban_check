import requests
from itertools import chain
from bs4 import BeautifulSoup


url = "https://assets.playnccdn.com/static-conti/1774778135671.html"

res = requests.get(url)
res.encoding = res.apparent_encoding  # fix Korean encoding

soup = BeautifulSoup(res.text, "html.parser")

table = soup.find("table")

data = []

for row in table.find_all("tr"):
    cols = [col.get_text(strip=True) for col in row.find_all(["td", "th"])]
    
    if cols:  # skip empty rows
        data.append(cols)

all_data = list(chain.from_iterable(data[1:]))

word_find = ["브론aldza", "aogih"]

matches = []

for word in word_find:
    for ign in all_data:
        if (ign[:2] == word[:2]) and (len(ign) == len(word)):
            matches.append(ign)

if matches:
    print("Found:", matches)
else:
    print("Not found")