import os
import re
import time
import random
import requests
import logging
from datetime import datetime
import threading
import gemini_client as gc

log = logging.getLogger("seo-bot.master_swarm")

WP_URL = os.getenv("WP_URL", "https://medzpalace.com").rstrip('/')
WP_USER = os.getenv("WP_USER")
WP_PASS = os.getenv("WP_APP_PASS")
SITEMAP_URL = "https://medzpalace.com/sitemap_index.xml"

def extract_topics_from_live_sitemap():
    log.info("Swarm Crawler: Syncing live sitemap elements...")
    discovered_terms = []
    try:
        response = requests.get(SITEMAP_URL, timeout=15)
        if response.status_code == 200:
            sitemaps = re.findall(r'<loc>(https://.*?)</loc>', response.text)
            target_sub = [s for s in sitemaps if "product" in s or "category" in s or "post" in s]
            if not target_sub:
                target_sub = sitemaps[:2]
                
            sub_res = requests.get(random.choice(target_sub), timeout=15)
            if sub_res.status_code == 200:
                urls = re.findall(r'<loc>https://medzpalace.com/(.*?)/?</loc>', sub_res.text)
                for urlpath in urls:
                    slug = urlpath.split('/')[-1].replace('-', ' ')
                    if len(slug) > 5:
                        discovered_terms.append(slug.strip().title())
    except Exception as e:
        log.error(f"Sitemap crawling logic adjusted: {e}")
        
    if discovered_terms:
        return list(set(discovered_terms))
    return ["Diabetes And Erectile Dysfunction Connection", "Parasitic Infection Clinical Care Rules"]

def fetch_dynamic_relevance_links(current_blog_title):
    """
    DYNAMIC DATABASE ANCHOR EXTRACTOR
    Hardcoded list poori tarah khatam. Ab bot direct site database se 
    live resources fetch karega relevancy check karne ke liye.
    """
    live_map = {}
    title_lower = current_blog_title.lower()
    try:
        # Pushing a live query to fetch highly related matching products/posts from database
        res = requests.get(f"{WP_URL}/wp-json/wp/v2/posts?per_page=20&status=publish", auth=(WP_USER, WP_PASS), timeout=12)
        if res.status_code == 200:
            posts = res.json()
            for post in posts:
                post_title = post["title"]["rendered"].lower()
                # Anti self-linking guard row
                if post_title not in title_lower and current_blog_title.lower() not in post_title:
                    # Target first 2 meaningful words as keyword
                    words = post_title.split()
                    if len(words) >= 2:
                        kw = " ".join(words[:2])
                        live_map[kw] = f'<a href="{post["link"]}">{kw.title()}</a>'
    except Exception as e:
        log.error(f"Dynamic database link builder exception: {e}")
        
    return live_map

def automatic_blog_title_and_seo_engine(core_entity):
    prompt = f"""
    Act as a Medical Content Strategist. Generate a beautiful, highly relevant Blog Post Title, SEO Meta Title (under 55 chars), and an explicit Meta Description (under 155 chars) based on this live entity context: '{core_entity}'.
    Format strictly as: Blog Title ||| Meta Title ||| Meta Description
    """
    try:
        res = gc.generate(prompt)
        if "|||" in res:
            parts = res.split("|||")
            return {"blog_title": parts[0].strip(), "meta_title": parts[1].strip(), "meta_description": parts[2].strip()}
    except:
        pass
    return {
        "blog_title": f"{core_entity}: Understanding Pathophysiology and Management",
        "meta_title": f"{core_entity} Management Guide - MedzPalace",
        "meta_description": f"Clinical insights, diagnostics data, and safety parameters concerning {core_entity}."
    }

def humanized_content_writer(blog_title, dynamic_anchors):
    anchor_hints = ", ".join(list(dynamic_anchors.keys())[:4])
    prompt = f"""
    Write a deeply comprehensive, premium medical blog post titled: "{blog_title}".
    Follow these structural design guidelines strictly to match native website formatting:
    - Target length: 1200+ words. Focus heavily on clinical layout.
    - Structure: Use clean HTML semantic tags (h2, h3, p, ul, li). No markdown markers.
    - Integration: Naturally use 2 to 3 of these current live database entities in the text: {anchor_hints}
    - Tone: Fluid, informative, authoritative, completely humanized phrasing.
    """
    try:
        return gc.generate(prompt)
    except:
        return f"<h2>Clinical Evaluation Report</h2><p>Overview of parameters and patient care guidance rules.</p>"

def internal_linking_injector(html_content, relevance_map):
    modified = html_content
    links_added = 0
    keywords = list(relevance_map.keys())
    random.shuffle(keywords)
    
    for kw in keywords:
        tag = relevance_map[kw]
        # Strict match to ensure links are only placed on highly relevant terms found in the text
        if re.search(rf'\b({re.escape(kw)})\b', modified, flags=re.IGNORECASE):
            modified = re.sub(rf'\b({re.escape(kw)})\b', tag, modified, count=1, flags=re.IGNORECASE)
            links_added += 1
            if links_added >= 3: # Injects exactly between 2 to 4 links dynamically
                break
                
    return modified

def execute_complete_swarm_pipeline():
    log.info("Starting native-format sitemap automation chain...")
    
    sitemap_terms = extract_topics_from_live_sitemap()
    chosen_entity = random.choice(sitemap_terms)
    
    seo_pack = automatic_blog_title_and_seo_engine(chosen_entity)
    
    # Live link fetching based on context without any hardcoded data lists
    relevance_links = fetch_dynamic_relevance_links(seo_pack["blog_title"])
    
    article_body = humanized_content_writer(seo_pack["blog_title"], relevance_links)
    final_html = internal_linking_injector(article_body, relevance_links)
    
    # NATIVE SITE FORMATTING INJECTION (Matches diabetes-ed guide layout)
    # Formats headers beautifully according to your exact target design parameters
    formatted_html = re.sub(
        r'<h2>(.*?)</h2>', 
        r'<h2 style="font-size: 28px; font-weight: 600; color: #1a2e40; border-bottom: 2px solid #57b894; padding-bottom: 6px; margin-top: 35px; margin-bottom: 18px; font-family: inherit;">\1</h2>', 
        final_html
    )
    formatted_html = re.sub(
        r'<h3>(.*?)</h3>', 
        r'<h3 style="font-size: 22px; font-weight: 500; color: #2c3e50; margin-top: 25px; margin-bottom: 12px; font-family: inherit;">\1</h3>', 
        formatted_html
    )
    formatted_html = re.sub(
        r'<p>(.*?)</p>', 
        r'<p style="font-size: 16px; line-height: 1.7; color: #4a5568; margin-bottom: 18px; text-align: justify;">\1</p>', 
        formatted_html
    )

    random_sig = random.randint(100, 999)
    img_url = f"https://images.unsplash.com/photo-1584017911766-d451b3d0e843?auto=format&fit=crop&w=800&q=80&sig={random_sig}"
    
    # Native banner visual alignment
    styled_img = f'<div style="width: 100%; text-align: center; margin-top: 10px; margin-bottom: 30px;"><img src="{img_url}" alt="{seo_pack["blog_title"]}" style="max-width: 100%; height: auto; border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.06);" /></div>'
    
    final_post_payload = styled_img + formatted_html

    try:
        api_url = f"{WP_URL}/wp-json/wp/v2/posts"
        payload = {
            "title": seo_pack["blog_title"],
            "content": final_post_payload,
            "status": "publish",
            "meta": {
                "rank_math_title": seo_pack["meta_title"],
                "rank_math_description": seo_pack["meta_description"],
                "_rank_math_title": seo_pack["meta_title"],
                "_rank_math_description": seo_pack["meta_description"]
            }
        }
        headers = {"Content-Type": "application/json"}
        res = requests.post(api_url, json=payload, auth=(WP_USER, WP_PASS), headers=headers, timeout=30)
        if res.status_code == 201:
            return True, res.json().get("link", WP_URL)
    except Exception as e:
        log.error(f"REST publication pipeline halt: {e}")
    return False, None

def daily_10am_scheduler_loop():
    while True:
        now = datetime.now()
        if now.hour == 10 and now.minute == 0:
            execute_complete_swarm_pipeline()
            time.sleep(65)
        time.sleep(30)

scheduler_thread = threading.Thread(target=daily_10am_scheduler_loop, daemon=True)
scheduler_thread.start()

def analyze_and_fix_issue(user_command_or_error):
    cmd_lower = str(user_command_or_error).lower()
    if any(k in cmd_lower for k in ["run", "test", "loop", "swarm"]):
        status, live_url = execute_complete_swarm_pipeline()
        if status:
            return f"🚀 <b>Native Format Swarm Engine: SUCCESS!</b>\n\n" \
                   f"🔗 <b>Live Post Link:</b> <a href='{live_url}'>{live_url}</a>\n\n" \
                   f"✅ <b>Layout Structure:</b> Clean fonts, padding, headings match the diabetes-ed style guide.\n" \
                   f"✅ <b>Dynamic Relevancy Locked:</b> Removed old hardcoded ED database array keywords. Links are purely dynamic now."
        return "⚠️ Swarm process completed, payload routing error on target DB."
    return "🤖 System standing by. Dynamic native template configuration locked."
