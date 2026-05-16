import os
import json
import re
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

# ── RSS Feed Registry ─────────────────────────────
# ── RSS Feed Registry ─────────────────────────────
NEWS_SOURCES = {
    "tagesschau": {
        "label": "Tagesschau (ARD)",
        "type": "json_api",
        "url": "https://www.tagesschau.de/api2u/news",
        "bias": "neutral"
    },
    "zdf": {
        "label": "ZDF heute",
        "type": "rss",
        "url": "https://www.zdf.de/rss/zdf/nachrichten",
        "bias": "neutral"
    },
    "dw": {
        "label": "Deutsche Welle",
        "type": "rss",
        "url": "https://rss.dw.com/xml/rss-de-news",
        "bias": "neutral"
    },
    "spiegel": {
        "label": "Spiegel Online",
        "type": "rss",
        "url": "https://www.spiegel.de/schlagzeilen/index.rss",
        "bias": "left-liberal"
    },
    "zeit": {
        "label": "Zeit Online",
        "type": "rss",
        "url": "https://newsfeed.zeit.de/index",
        "bias": "left-liberal"
    },
    "sz": {
        "label": "Süddeutsche Zeitung",
        "type": "rss",
        "url": "https://rss.sueddeutsche.de/rss/Alles",
        "bias": "left-liberal"
    },
    "stern": {
        "label": "Stern",
        "type": "rss",
        "url": "https://www.stern.de/feed/standard/all/",
        "bias": "left-liberal"
    },
    "taz": {
        "label": "taz",
        "type": "rss",
        "url": "https://taz.de/!p4608;rss/",
        "bias": "left"
    },
    "faz": {
        "label": "FAZ",
        "type": "rss",
        "url": "https://www.faz.net/rss/aktuell",
        "bias": "conservative-liberal"
    },
    "cicero": {
        "label": "Cicero",
        "type": "rss",
        "url": "https://www.cicero.de/rss.xml",
        "bias": "conservative-liberal"
    },
    "nzz": {
        "label": "Neue Zürcher Zeitung",
        "type": "rss",
        "url": "https://www.nzz.ch/recent.rss",
        "bias": "conservative-liberal"
    },
    "handelsblatt": {
        "label": "Handelsblatt",
        "type": "rss",
        "url": "https://www.handelsblatt.com/contentexport/feed/top-themen",
        "bias": "economic-liberal"
    },
    "welt": {
        "label": "Die Welt",
        "type": "rss",
        "url": "https://www.welt.de/feeds/latest.rss",
        "bias": "right-conservative"
    },
    "focus": {
        "label": "Focus Online",
        "type": "rss",
        "url": "https://www.focus.de/schlagzeilen/rss",
        "bias": "right-conservative"
    },
    "ntv": {
        "label": "n-tv",
        "type": "rss",
        "url": "https://www.n-tv.de/rss",
        "bias": "right-conservative"
    },
    "bild": {
        "label": "BILD",
        "type": "rss",
        "url": "https://www.bild.de/feed/alles.xml",
        "bias": "populist-mixed"
    },
    "tichys": {
        "label": "Tichys Einblick",
        "type": "rss",
        "url": "https://www.tichyseinblick.de/feed/",
        "bias": "far-right"
    },
    "achgut": {
        "label": "Achse des Guten",
        "type": "rss",
        "url": "https://www.achgut.com/rss",
        "bias": "far-right"
    },
    "junge_freiheit": {
        "label": "Junge Freiheit",
        "type": "rss",
        "url": "https://jungefreiheit.de/feed",
        "bias": "far-right"
    },
}



# ── Helpers ───────────────────────────────────────
def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_rss(url: str, timeout: int = 15) -> list[dict]:
    """Fetches and parses an RSS feed."""
    headers = {"User-Agent": "Diskursraum/1.0 (research project)"}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for item in root.iter("item"):
        title = strip_html(item.findtext("title", ""))
        description = strip_html(item.findtext("description", ""))
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()
        items.append({
            "title": title,
            "description": description,
            "url": link,
            "published_at": pub_date
        })
    return items


def fetch_tagesschau(keyword: str) -> list[dict]:
    """Fetches from Tagesschau JSON API."""
    headers = {"User-Agent": "Diskursraum/1.0 (research project)"}
    params = {"search": keyword, "pageSize": 20}
    response = requests.get(
        "https://www.tagesschau.de/api2u/search",
        params=params,
        headers=headers,
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    items = []
    for article in data.get("searchResults", []):
        items.append({
            "title": article.get("title", "").strip(),
            "description": article.get("firstSentence", "").strip(),
            "url": article.get("shareURL", ""),
            "published_at": article.get("date", "")
        })
    return items


def filter_by_keywords(items: list[dict], keywords: list[str]) -> list[dict]:
    """Keeps only items containing at least one keyword."""
    keywords_lower = [k.lower() for k in keywords]
    return [
        item for item in items
        if any(kw in f"{item['title']} {item['description']}".lower()
               for kw in keywords_lower)
    ]


def normalize(items: list[dict], source_id: str, topic_id: str) -> list[dict]:
    """Normalizes items to unified schema."""
    source = NEWS_SOURCES[source_id]
    results = []
    for i, item in enumerate(items):
        text = " ".join(filter(None, [
            item["title"],
            item["description"]
        ])).strip()
        if len(text) < 20:
            continue
        results.append({
            "id": f"{source_id}_{i}",
            "text": text,
            "title": item["title"],
            "source": source["label"],
            "source_id": source_id,
            "bias": source["bias"],
            "url": item["url"],
            "published_at": item["published_at"],
            "data_source": "news_rss",
            "topic": topic_id
        })
    return results


# ── Main Collector ────────────────────────────────
def collect_news(topic_id: str, keywords: list[str], cache_dir: str) -> str:
    """
    Collects news from all 11 sources for a topic.
    Filters by keywords, normalizes, saves to cache.
    Returns path to cached JSON file.
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{topic_id}_news.json")

    all_results = []

    for source_id, source in NEWS_SOURCES.items():
        try:
            print(f"  Fetching {source['label']}...")

            if source_id == "tagesschau":
                raw_items = []
                for kw in keywords[:2]:
                    raw_items += fetch_tagesschau(kw)
            else:
                raw_items = fetch_rss(source["url"])
                raw_items = filter_by_keywords(raw_items, keywords)

            normalized = normalize(raw_items, source_id, topic_id)
            all_results.extend(normalized)
            print(f"    → {len(normalized)} articles")

        except Exception as e:
            print(f"    ⚠ {source['label']} failed: {e}")
            continue

    print(f"\nTotal: {len(all_results)} articles for '{topic_id}'")

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"Cached to: {cache_path}")
    return cache_path


# ── Quick test ────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from config import TOPICS, CACHE_DIR

    topic_id = "nuclear_energy"
    topic = TOPICS[topic_id]

    path = collect_news(topic_id, topic["newsapi_keywords"], CACHE_DIR)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n=== Sample (first 3) ===")
    for item in data[:3]:
        print(f"\n[{item['source']} / {item['bias']}]")
        print(f"{item['text'][:120]}...")