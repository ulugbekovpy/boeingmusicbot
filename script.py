import requests
from bs4 import BeautifulSoup
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = "https://eu.hitmoz.com/"

SCRAPE_DO_TOKEN = "725687a9ec4d49b991be66fb3fc00b45de5d9a6dbb3"

def search(query):
    target_url = base_url + f"search?q={query}"
    
    proxy_url = f"https://api.scrape.do/?token={SCRAPE_DO_TOKEN}&url={requests.utils.quote(target_url)}"
    
    html_content = None
    
    try:
        print(f"Отправляем запрос к Hitmoz через Scrape.do API...")
        page = requests.get(proxy_url, timeout=25)
        print(f"SCRAPE.DO STATUS CODE: {page.status_code}")
        
        if page.status_code == 200:
            html_content = page.text
        else:
            print(f"Scrape.do вернул код: {page.status_code}")
            
    except Exception as e:
        print(f"Ошибка при запросе через Scrape.do: {e}")

    if not html_content:
        print("Scrape.do не вернул данные. Пробуем напрямую...")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            }
            page = requests.get(target_url, headers=headers, verify=False, timeout=10)
            html_content = page.text
        except Exception as e:
            print(f"Прямой запрос упал: {e}")
            return []

    try:
        soup = BeautifulSoup(html_content, "html.parser")
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

            if mp3_url:
                if mp3_url.startswith("/"):
                    mp3_url = base_url.rstrip("/") + mp3_url
                elif "hitmoz" in mp3_url:
                    path_start = mp3_url.find("/get/")
                    if path_start != -1:
                        mp3_url = base_url.rstrip("/") + mp3_url[path_start:]

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
        print(f"Ошибка парсинга: {e}")
        return []