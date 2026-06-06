import requests
import re

url = "https://www.zomato.com/bangalore/glens-bakehouse-indiranagar"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

response = requests.get(url, headers=headers, timeout=5)
meta_tags = re.findall(r'<meta\s+[^>]+>', response.text)
for tag in meta_tags:
    if "image" in tag or "og:" in tag:
        print(tag)
