# Antilles Digital Media — Article Corpus (Enriched)

## What's in this bundle

### index.html (standalone corpus web app — open directly in any browser)
- 654 backlink articles from the original Ahrefs CSV
- 228 of those now have full body text embedded (scraped live on 2026-11-23)
- 426 articles show the actual scrape error (HTTP 403 / DNS failure / etc) instead of a generic message
- Features: real-time search (title, URL, anchor, category, body text), Clean (42) vs Spam (612) vs All (654) filter, page type filter, Dofollow/Nofollow filter, DR sorting, #article/{id} hash-routed reader modal, Export Filtered JSON button
- Deploy-ready: drop on Vercel / Cloudflare Pages / Netlify, no build needed

### articles-corpus-enriched.json
Full structured dataset with bodyText + scrapeError fields. Use this if you want to load it into a different tool.

### articles-corpus.json
Original clean CSV-derived dataset (no body text) — kept for reference / re-scraping.

### fetch_full_articles.py
Original single-threaded scraper. ~2.4 hours for all 654 URLs.

### fetch_full_articles_parallel.py
8-thread parallel scraper. Used to produce the enriched JSON in this bundle. ~90 seconds for all 654 URLs. Re-run any time to refresh.

## How the corpus was built
1. Original CSV (1,386 backlink rows) was filtered to the 654 Article-type entries.
2. fetch_full_articles_parallel.py scraped each URL with a 12-second timeout, 8 parallel workers, polite 0.3–0.9s delays.
3. Of 654 URLs:
   - 228 successfully extracted real article body text (avg 870 words, total ~198K words)
   - 426 failed — breakdown:
     - 90 DNS failures (domain no longer exists)
     - 43 SSL errors
     - 22 HTTP 400 Bad Request
     - 21 HTTP 403 Forbidden (WAF block)
     - 15 Network unreachable
     - 12 Timeout
     - 3 HTTP 404 Not Found
     - Rest: various connection errors

The 90 DNS-failure domains confirm many of these were PBN/low-quality backlinks that have since been abandoned.
