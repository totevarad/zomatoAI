import requests
import re
import html

url = "https://www.zomato.com/bangalore/glens-bakehouse-indiranagar"

headers_basic = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

headers_browser = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

def try_fetch(name, headers):
    print(f"\nTrying headers: {name}")
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        # 1. Test og:image meta tags
        og_match = re.search(r'property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', response.text)
        if not og_match:
            og_match = re.search(r'content=["\']([^"\']+)["\']\s+property=["\']og:image["\']', response.text)
            
        if og_match:
            img_url = html.unescape(og_match.group(1))
            print(f"Found og:image: {img_url}")
        else:
            print("No og:image found")
            
        # 2. Test fallback search for zmtcdn pictures
        img_urls = re.findall(r'https://b.zmtcdn.com/data/[^\s"\']+\.(?:jpg|jpeg|png|webp)', response.text)
        if img_urls:
            print(f"Found {len(img_urls)} general CDN images. First: {img_urls[0]}")
        else:
            print("No CDN images found")
            
    except Exception as e:
        print(f"Error: {e}")

try_fetch("Basic Headers", headers_basic)
try_fetch("Browser Headers", headers_browser)
