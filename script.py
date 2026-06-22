import requests
from bs4 import BeautifulSoup
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://eu.hitmoz.com/"

def search(query):
    search_url = url + f"search?q={query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        page = requests.get(search_url, headers=headers, verify=False, timeout=10)
        print(f"STATUS CODE FROM SITE: {page.status_code}")
        print(f"HTML LENGTH: {len(page.text)}")
        
        if page.status_code != 200:
            print("Сайт вернул ошибку доступа!")
            return []
            
        soup = BeautifulSoup(page.text, "html.parser")
        tracks = soup.find_all("li", class_="tracks__item")
        print(f"FOUND TRACKS ON PAGE: {len(tracks)}") 

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

    except Exception as e:
        print(f"Ошибка при парсинге: {e}")
        return []