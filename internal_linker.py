"""
internal_linker.py
==================
Sitemap-based internal linking for medzpalace.com
- Fetches all URLs from sitemap
- Extracts keywords from slugs
- Injects anchor tags into WordPress post/page content
- Safe: only first occurrence per keyword, max 5 links per post
- Does NOT modify wp_client.py
"""

import os
import re
import time
import logging
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from html import unescape

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
WP_URL    = os.getenv("WP_URL", "https://medzpalace.com")
WP_USER   = os.getenv("WP_USER", "")          # WP username
WP_PASS   = os.getenv("WP_APP_PASS", "")      # WP application password
MAX_LINKS = int(os.getenv("MAX_LINKS", "5"))   # max internal links to inject per post
MIN_WORD_LEN = 4                               # ignore very short slug words

SITEMAP_INDEX = f"{WP_URL}/sitemap_index.xml"

# ─── Skip self-link guard ───────────────────────────────────────────────────────
# We never link a page to itself — checked at inject time.

# ─── Sitemap fetching ──────────────────────────────────────────────────────────

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

def fetch_xml(url: str) -> ET.Element | None:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return ET.fromstring(r.text)
    except Exception as e:
        log.warning(f"fetch_xml failed {url}: {e}")
        return None


def get_all_urls() -> list[str]:
    """Fetch every URL from sitemap index → child sitemaps."""
    root = fetch_xml(SITEMAP_INDEX)
    if root is None:
        return []
    urls = []
    for sitemap in root.findall("sm:sitemap", NS):
        loc = sitemap.findtext("sm:loc", namespaces=NS)
        if loc:
            child = fetch_xml(loc)
            if child:
                for url in child.findall("sm:url", NS):
                    u = url.findtext("sm:loc", namespaces=NS)
                    if u:
                        urls.append(u.strip())
    log.info(f"Total URLs from sitemap: {len(urls)}")
    return urls


# ─── Keyword extraction ────────────────────────────────────────────────────────

# Words to ignore when building keyword→URL map
STOPWORDS = {
    "the","and","for","with","how","what","why","does","are","can","not",
    "from","that","this","your","you","have","when","will","more","into",
    "was","its","but","use","all","any","our","their","about","also",
    "been","being","which","there","these","those","than","then","them",
    "like","just","some","over","such","only","even","most","very",
    "take","make","after","before","during","while","other","each",
    "between","both","through","without","within","against","under",
    "should","could","would","might","may","must","shall",
    "get","got","has","had","did","do","is","in","of","to","on","at","by",
    "mg","ml","tablet","tablets","capsule","capsules","oral","jelly",
    "buy","online","price","india","usa","uk","australia",
    "review","reviews","side","effects","dosage","dose",
    # product line noise words
    "super","extra","professional","forte","strong","soft","gold","plus",
    "chewable","active","double","black","force",
}

def slug_to_keywords(slug: str) -> list[str]:
    """
    Convert URL slug to ranked keyword phrases.
    Returns multi-word phrases (best) and single keywords.
    """
    # strip .html and leading/trailing slashes
    slug = re.sub(r"\.html$", "", slug)
    slug = slug.strip("/")
    # remove trailing /
    words = re.split(r"[-_\s/]+", slug.lower())
    words = [w for w in words if len(w) >= MIN_WORD_LEN and w not in STOPWORDS and w.isalpha()]

    phrases = []
    # 3-gram
    for i in range(len(words) - 2):
        phrases.append(" ".join(words[i:i+3]))
    # 2-gram
    for i in range(len(words) - 1):
        phrases.append(" ".join(words[i:i+2]))
    # 1-gram
    phrases.extend(words)
    return phrases


def build_keyword_map(urls: list[str]) -> dict[str, str]:
    """
    Returns {keyword_phrase: url} mapping.
    Longer phrases preferred (they match more specifically).
    Sorted so longest phrases appear first in the dict.
    """
    kw_map: dict[str, str] = {}
    for url in urls:
        path = urlparse(url).path
        slug = path.split("/")[-1] or path.split("/")[-2]
        for kw in slug_to_keywords(slug):
            if kw and kw not in kw_map:
                kw_map[kw] = url
    # sort by phrase length desc so longer matches win
    return dict(sorted(kw_map.items(), key=lambda x: len(x[0].split()), reverse=True))


# ─── HTML-safe content injection ──────────────────────────────────────────────

def inject_links(content: str, kw_map: dict[str, str],
                 current_url: str, max_links: int = MAX_LINKS) -> tuple[str, int]:
    """
    Inject anchor tags into HTML content.
    - Only first occurrence of each keyword
    - Skip if keyword already inside <a> tag
    - Skip self-links
    - Max `max_links` total injections
    Returns (new_content, links_added).
    """
    added = 0
    used_urls: set[str] = set()
    already_linked: set[str] = set()

    # Find all existing anchor text to avoid double-linking
    existing_links = re.findall(r'<a[^>]*>(.*?)</a>', content, re.IGNORECASE | re.DOTALL)
    for el in existing_links:
        already_linked.add(re.sub(r'<[^>]+>', '', el).lower().strip())

    for phrase, target_url in kw_map.items():
        if added >= max_links:
            break
        if target_url == current_url:
            continue
        if target_url in used_urls:
            continue
        if phrase in already_linked:
            continue

        # Case-insensitive replacement of first occurrence NOT inside a tag
        # Pattern: phrase not preceded by href= or inside <a...>
        # Simple approach: replace first occurrence outside tags
        pattern = re.compile(
            r'(?<!["\'/\w])(' + re.escape(phrase) + r')(?!["\'/\w])',
            re.IGNORECASE
        )

        # Check if this phrase exists in content (outside HTML tags)
        # Strip tags to test presence
        text_only = re.sub(r'<[^>]+>', '', content)
        if not re.search(pattern, text_only):
            continue

        # Now inject: walk through content, replace first plain-text occurrence
        new_content, n = _replace_first_in_text(content, pattern, target_url)
        if n > 0:
            content = new_content
            added += 1
            used_urls.add(target_url)
            already_linked.add(phrase.lower())
            log.debug(f"  Linked '{phrase}' → {target_url}")

    return content, added


def _replace_first_in_text(html: str, pattern: re.Pattern, url: str) -> tuple[str, int]:
    """
    Replace first regex match in HTML that is NOT inside a tag or existing anchor.
    Returns (new_html, count_replaced).
    """
    # Split into tag / non-tag segments
    segments = re.split(r'(<[^>]+>)', html)
    inside_anchor = False
    replaced = False
    result = []

    for seg in segments:
        if re.match(r'<a[\s>]', seg, re.IGNORECASE):
            inside_anchor = True
            result.append(seg)
        elif re.match(r'</a>', seg, re.IGNORECASE):
            inside_anchor = False
            result.append(seg)
        elif seg.startswith('<'):
            result.append(seg)
        else:
            if not replaced and not inside_anchor:
                new_seg, count = pattern.subn(
                    lambda m: f'<a href="{url}">{m.group(0)}</a>',
                    seg, count=1
                )
                if count > 0:
                    replaced = True
                    seg = new_seg
            result.append(seg)

    return "".join(result), 1 if replaced else 0


# ─── WordPress REST API ────────────────────────────────────────────────────────

def wp_auth() -> tuple[str, str] | None:
    if not WP_USER or not WP_PASS:
        log.error("WP_USER / WP_APP_PASS env vars not set")
        return None
    return (WP_USER, WP_PASS)


def get_posts(post_type: str = "posts", per_page: int = 100) -> list[dict]:
    auth = wp_auth()
    if not auth:
        return []
    all_posts = []
    page = 1
    while True:
        r = requests.get(
            f"{WP_URL}/wp-json/wp/v2/{post_type}",
            params={"per_page": per_page, "page": page, "status": "publish"},
            auth=auth, timeout=30
        )
        if r.status_code == 400:
            break
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        all_posts.extend(data)
        if len(data) < per_page:
            break
        page += 1
    log.info(f"Fetched {len(all_posts)} {post_type}")
    return all_posts


def update_post(post_id: int, post_type: str, new_content: str) -> bool:
    auth = wp_auth()
    if not auth:
        return False
    r = requests.post(
        f"{WP_URL}/wp-json/wp/v2/{post_type}/{post_id}",
        json={"content": new_content},
        auth=auth, timeout=30
    )
    if r.status_code in (200, 201):
        return True
    log.warning(f"Update failed {post_id}: {r.status_code} {r.text[:200]}")
    return False


# ─── Main runner ───────────────────────────────────────────────────────────────

def run(dry_run: bool = False, post_types: list[str] | None = None):
    """
    dry_run=True  → show what would be linked, no WP updates
    post_types    → ["posts", "pages"] or subset
    """
    if post_types is None:
        post_types = ["posts", "pages"]

    log.info("Building keyword map from sitemap…")
    urls = get_all_urls()
    kw_map = build_keyword_map(urls)
    log.info(f"Keyword map: {len(kw_map)} entries")

    total_updated = 0

    for ptype in post_types:
        wp_type = ptype  # "posts" or "pages"
        items = get_posts(wp_type)

        for item in items:
            post_id    = item["id"]
            post_link  = item.get("link", "")
            raw_content = item.get("content", {}).get("raw") or item.get("content", {}).get("rendered", "")

            if not raw_content:
                continue

            new_content, count = inject_links(raw_content, kw_map, post_link)

            if count == 0:
                continue

            log.info(f"[{ptype}] ID={post_id} '{item.get('slug','')}' → {count} links added")

            if not dry_run:
                ok = update_post(post_id, wp_type, new_content)
                if ok:
                    total_updated += 1
                time.sleep(0.5)  # gentle rate limit
            else:
                total_updated += 1  # count dry-run hits

    log.info(f"Done. Posts updated: {total_updated} (dry_run={dry_run})")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="medzpalace internal linker")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show links without updating WP")
    parser.add_argument("--types", nargs="+", default=["posts"],
                        help="post types: posts pages (default: posts)")
    parser.add_argument("--max-links", type=int, default=MAX_LINKS,
                        help=f"Max links per post (default {MAX_LINKS})")
    args = parser.parse_args()

    MAX_LINKS = args.max_links
    run(dry_run=args.dry_run, post_types=args.types)
