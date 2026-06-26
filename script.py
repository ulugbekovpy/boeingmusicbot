import aiohttp
from bs4 import BeautifulSoup
import json

base_url = "https://eu.hitmoz.com/"

# Функция стала асинхронной (async def)
async def search(query):
    target_url = base_url + f"search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    try:
        # Используем aiohttp вместо requests
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url, headers=headers, ssl=False, timeout=10) as response:
                if response.status != 200:
                    return []
                html_content = await response.text()
    except Exception as e:
        print(f"Ошибка асинхронного запроса: {e}")
        return []

    # Парсинг остается прежним, так как bs4 работает быстро в памяти
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        tracks = soup.find_all("li", class_="tracks__item")
        
        results = []
        for t in tracks:
            data = t.get("data-musmeta")
            if not data:
                continue
            
            meta = json.loads(data.replace("&quot;", '"'))
            mp3_url = meta.get("url")
            
            if mp3_url:
                if mp3_url.startswith("/"):
                    mp3_url = base_url.rstrip("/") + mp3_url
                elif "hitmoz" in mp3_url:
                    path_start = mp3_url.find("/get/")
                    if path_start != -1:
                        mp3_url = base_url.rstrip("/") + mp3_url[path_start:]

            results.append({
                "artist": meta.get("artist", "").strip(),
                "title": meta.get("title", "").strip(),
                "duration": t.select_one(".track__fulltime").text.strip() if t.select_one(".track__fulltime") else "N/A",
                "image": meta.get("img"),
                "url": mp3_url
            })
        return results
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return []