"""
Parallel article scraper for the Antilles Digital Media backlink corpus.
8 worker threads, polite delay, periodic save. Produces articles-corpus-enriched.json
in the same directory as this script.
"""
import json
import os
import time
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(HERE, "articles-corpus.json")
OUTPUT_PATH = os.path.join(HERE, "articles-corpus-enriched.json")

WORKERS = 8
TIMEOUT = 12
POLITE_DELAY = 0.3  # per-worker delay between requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Lock for periodic file writes
write_lock = threading.Lock()
progress_lock = threading.Lock()
counters = {"done": 0, "success": 0, "fail": 0, "total": 0}


def extract_text(html: str) -> tuple[str, int]:
    soup = BeautifulSoup(html, "html.parser")
    # Strip noise first
    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                     "noscript", "form", "iframe"]):
        tag.decompose()
    # Prefer semantic main/article containers
    main = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li"], recursive=True):
        text = el.get_text(" ", strip=True)
        if len(text) > 25:
            paragraphs.append(text)
    # Deduplicate consecutive duplicates (often happens with nested markup)
    deduped = []
    for p in paragraphs:
        if not deduped or deduped[-1] != p:
            deduped.append(p)
    body = "\n\n".join(deduped)
    return body, len(body.split())


def fetch_one(item: dict) -> dict:
    # Skip if already enriched in a prior run
    if item.get("bodyText"):
        with progress_lock:
            counters["done"] += 1
            counters["success"] += 1
        return item

    url = item["url"]
    time.sleep(POLITE_DELAY * (hash(threading.current_thread().name) % 3 + 1) * 0.3)
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            final_url = resp.geturl()
            html = resp.read().decode("utf-8", errors="ignore")
        text, wc = extract_text(html)
        item["bodyText"] = text
        item["wordCount"] = wc
        item["finalUrl"] = final_url
        item.pop("scrapeError", None)
        with progress_lock:
            counters["success"] += 1
    except urllib.error.HTTPError as e:
        item["bodyText"] = ""
        item["wordCount"] = 0
        item["scrapeError"] = f"HTTP {e.code}: {e.reason}"
        with progress_lock:
            counters["fail"] += 1
    except Exception as e:
        item["bodyText"] = ""
        item["wordCount"] = 0
        # Truncate very long error strings
        err = str(e)
        item["scrapeError"] = err[:200]
        with progress_lock:
            counters["fail"] += 1

    with progress_lock:
        counters["done"] += 1
        idx = counters["done"]
        if idx % 25 == 0:
            print(f"  [{idx}/{counters['total']}] success={counters['success']} fail={counters['fail']}", flush=True)
            with write_lock:
                # Re-read latest articles list from shared store
                pass  # handled by main thread
    return item


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)
    counters["total"] = len(articles)
    print(f"Enriching {len(articles)} articles with {WORKERS} workers...", flush=True)

    last_save = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_one, a): i for i, a in enumerate(articles)}
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                articles[idx] = fut.result()
            except Exception as e:
                print(f"  [worker error idx={idx}] {e}", flush=True)
            # Periodic save every 10 completed items
            if counters["done"] % 10 == 0:
                with write_lock:
                    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
                        json.dump(articles, out, ensure_ascii=False, indent=2)
                last_save = time.time()
                print(f"  [checkpoint] saved {counters['done']}/{counters['total']} (success={counters['success']})", flush=True)

    # Final save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        json.dump(articles, out, ensure_ascii=False, indent=2)
    print(f"\nDONE. Total={counters['total']} Success={counters['success']} Fail={counters['fail']}", flush=True)
    print(f"Output: {OUTPUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
