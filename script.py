import requests
from bs4 import BeautifulSoup
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://eu.hitmoz.com/"

def search(query):
    search_url = url + f"search?q={query}"
    page = requests.get(search_url, verify=False)
    soup = BeautifulSoup(page.text, "html.parser")

    tracks = soup.find_all("li", class_="tracks__item")

    results = []
    for t in tracks:
        data = t.get("data-musmeta")
        if not data:
            continue
        meta = json.loads(data.replace("&quot;", '"'))

        title = meta.get("title", "").strip()
        artist = meta.get("artist", "").strip()
        mp3_url = meta.get("url")
        img = meta.get("img")

        time_div = t.select_one(".track__fulltime")
        duration = time_div.text.strip() if time_div else "N/A"

        results.append({
            "artist": artist,
            "title": title,
            "duration": duration,
            "image": img,
            "url": mp3_url
        })
    return results
