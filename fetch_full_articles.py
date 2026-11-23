import json
import time
import urllib.request
import urllib.error
from bs4 import BeautifulSoup

with open("articles-corpus.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body
    if not main:
        return ""
    paragraphs = [p.get_text(" ", strip=True) for p in main.find_all(["p", "h1", "h2", "h3", "li"])]
    paragraphs = [p for p in paragraphs if len(p) > 25]
    return "\n\n".join(paragraphs)

success = 0
for i, item in enumerate(articles):
    if item.get("bodyText"):
        continue
    url = item["url"]
    print(f"[{i+1}/{len(articles)}] Fetching: {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            text = extract_text(html)
            item["bodyText"] = text
            item["wordCount"] = len(text.split())
            if text:
                success += 1
    except Exception as e:
        item["scrapeError"] = str(e)
    
    if (i + 1) % 25 == 0:
        with open("articles-corpus-enriched.json", "w", encoding="utf-8") as out:
            json.dump(articles, out, ensure_ascii=False, indent=2)
    time.sleep(0.5)

with open("articles-corpus-enriched.json", "w", encoding="utf-8") as out:
    json.dump(articles, out, ensure_ascii=False, indent=2)

print(f"Done! Successfully extracted content from {success}/{len(articles)} URLs.")
