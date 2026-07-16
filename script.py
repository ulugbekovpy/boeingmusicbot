import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin

BASE_URL = "https://muzbomb.net"

async def search(query: str):
    target_url = f"{BASE_URL}/?song={quote_plus(query)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url, headers=headers, ssl=False, timeout=10) as response:
                if response.status != 200:
                    print(f"Muzbomb отдал статус-код: {response.status}")
                    return []
                html_content = await response.text()
    except Exception as e:
        print(f"Ошибка сети: {e}")
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    tracks = []

    # Находим все контейнеры треков по правильному классу
    song_blocks = soup.find_all("div", class_="tmtMus_blc")

    for block in song_blocks:
        try:
            # 1. Вытаскиваем артиста
            artist_elem = block.find("a", class_="tmtMus_blc_artist")
            artist = artist_elem.get_text(strip=True) if artist_elem else "Неизвестен"

            # 2. Вытаскиваем название трека
            track_elem = block.find("a", class_="tmtMus_blc_tracklink")
            title = track_elem.get_text(strip=True) if track_elem else "Без названия"

            # 3. Вытаскиваем длительность
            duration_elem = block.find("span", class_="dur")
            duration = duration_elem.get_text(strip=True) if duration_elem else "0:00"

            # 4. Вытаскиваем ссылку на скачивание MP3
            download_elem = block.find("a", class_="tmtMus_blc_download")
            download_url = ""
            if download_elem and download_elem.get("href"):
                raw_url = download_elem.get("href")
                # Если ссылка начинается с //, добавляем протокол https:
                if raw_url.startswith("//"):
                    download_url = f"https:{raw_url}"
                else:
                    download_url = urljoin(BASE_URL, raw_url)

            # Добавляем в массив, если нашли хоть какую-то инфу
            if artist != "Неизвестен" or title != "Без названия":
                tracks.append({
                    "artist": artist,
                    "title": title,
                    "duration": duration,
                    "url": download_url
                })

        except Exception as e:
            print(f"Ошибка парсинга трека: {e}")
            continue

    return tracks