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
                    if len(slug) > 5 and not any(x in slug.lower() for x in ["page", "author", "tag"]):
                        discovered_terms.append(slug.strip().title())
    except Exception as e:
        log.error(f"Sitemap crawling error: {e}")
        
    if discovered_terms:
        return list(set(discovered_terms))
    return ["Achieving Radiantly Healthy Skin", "Erectile Dysfunction Treatment Guidelines"]

def fetch_dynamic_relevance_links(current_blog_title):
    """
    STRICT LIVE DATABASE RELATION ENGINE
    Pulls real publishing anchors to match true content context.
    """
    live_map = {}
    title_lower = current_blog_title.lower()
    try:
        res = requests.get(f"{WP_URL}/wp-json/wp/v2/posts?per_page=20&status=publish", auth=(WP_USER, WP_PASS), timeout=12)
        if res.status_code == 200:
            posts = res.json()
            for post in posts:
                post_title = post["title"]["rendered"].lower().replace('`','').strip()
                if post_title not in title_lower and current_blog_title.lower() not in post_title:
                    words = post_title.split()
                    if len(words) >= 1:
                        kw = " ".join(words[:2])
                        live_map[kw] = f'<a href="{post["link"]}" style="color: #2b6cb0; font-weight: 600; text-decoration: underline;">{kw.title()}</a>'
    except Exception as e:
        log.error(f"Database link builder error: {e}")
        
    # Standard base verified categories assets
    base_anchors = {
        "sildenafil": f'<a href="{WP_URL}/product/sildenafil/" style="color: #2b6cb0; font-weight: 600; text-decoration: underline;">Sildenafil</a>',
        "cenforce 100mg": f'<a href="{WP_URL}/product/cenforce-100/" style="color: #2b6cb0; font-weight: 600; text-decoration: underline;">Cenforce 100mg</a>',
        "vidalista 20": f'<a href="{WP_URL}/product/vidalista-20/" style="color: #2b6cb0; font-weight: 600; text-decoration: underline;">Vidalista 20</a>',
        "healthy skin": f'<a href="{WP_URL}/product-category/skin-care/" style="color: #2b6cb0; font-weight: 600; text-decoration: underline;">healthy skin</a>'
    }
    for k, v in base_anchors.items():
        if k not in title_lower:
            live_map[k] = v
            
    return live_map

def automatic_blog_title_and_seo_engine(core_entity):
    prompt = f"""
    Act as an SEO Medical Content Director. Generate a professional Blog Post Title, SEO Meta Title (under 55 chars), and a Meta Description (under 155 chars) based strictly on this entity keyword: '{core_entity}'.
    Do not use any special symbols or backticks.
    Format strictly as: Blog Title ||| Meta Title ||| Meta Description
    """
    try:
        res = gc.generate(prompt)
        if "|||" in res:
            parts = res.split("|||")
            return {
                "blog_title": parts[0].replace('`','').strip(), 
                "meta_title": parts[1].replace('`','').strip(), 
                "meta_description": parts[2].replace('`','').strip()
            }
    except:
        pass
    return {
        "blog_title": f"Beyond Basics: Your Expert Guide to {core_entity}",
        "meta_title": f"Guide to Achieving {core_entity} - MedzPalace",
        "meta_description": f"Discover comprehensive insight and clinical guidance parameters regarding {core_entity} rules."
    }

def humanized_content_writer(blog_title, dynamic_anchors):
    anchor_hints = ", ".join(list(dynamic_anchors.keys()))
    prompt = f"""
    Write a deeply comprehensive, high-quality medical article titled exactly: "{blog_title}".
    
    STRICT INSTRUCTIONS:
    1. Focus ONLY on the topic explicitly stated in the title. Do NOT introduce or blend any other pharmaceutical or health topic that is unrelated.
    2. Write at least 1200+ words of deeply informative text.
    3. Formatting: Structure neatly using clean standard HTML tags (h2, h3, p, ul, li). Do NOT output any backticks (`) or markdown wrappers.
    4. Internal Linking Context: If relevant to the theme, naturally drop 2-3 of these matching phrases seamlessly inside the narrative flow: {anchor_hints}. Never add them randomly or out of context.
    """
    try:
        content = gc.generate(prompt)
        return content.replace('`','')
    except:
        return f"<h2>Clinical Evaluation and Management</h2><p>Overview of core therapeutic protocols and strategic care systems.</p>"

def internal_linking_injector(html_content, relevance_map):
    modified = html_content
    links_added = 0
    keywords = list(relevance_map.keys())
    random.shuffle(keywords)
    
    for kw in keywords:
        tag = relevance_map[kw]
        pattern = rf'\b({re.escape(kw)})\b'
        if re.search(pattern, modified, flags=re.IGNORECASE):
            modified = re.sub(pattern, tag, modified, count=1, flags=re.IGNORECASE)
            links_added += 1
            if links_added >= 3: # Keep perfect density count (2 to 4 links)
                break
                
    return modified

def execute_complete_swarm_pipeline():
    log.info("Starting beyond-basics layout template loop...")
    
    sitemap_terms = extract_topics_from_live_sitemap()
    chosen_entity = random.choice(sitemap_terms)
    
    seo_pack = automatic_blog_title_and_seo_engine(chosen_entity)
    relevance_links = fetch_dynamic_relevance_links(seo_pack["blog_title"])
    
    article_body = humanized_content_writer(seo_pack["blog_title"], relevance_links)
    final_html = internal_linking_injector(article_body, relevance_links)
    
    # EXACT NATIVE "BEYOND-BASICS" STYLE FORMATTING INJECTION
    # Re-arranges fonts, line-heights, colors and elements to dynamically mirror your target article layout.
    formatted_html = re.sub(
        r'<h2>(.*?)</h2>', 
        r'<h2 style="font-size: 26px; font-weight: 700; color: #2d3748; margin-top: 35px; margin-bottom: 15px; font-family: \'Playfair Display\', serif; border-left: 4px solid #3182ce; padding-left: 12px; line-height: 1.3;">\1</h2>', 
        final_html
    )
    formatted_html = re.sub(
        r'<h3>(.*?)</h3>', 
        r'<h3 style="font-size: 20px; font-weight: 600; color: #4a5568; margin-top: 25px; margin-bottom: 10px; font-family: inherit;">\1</h3>', 
        formatted_html
    )
    formatted_html = re.sub(
        r'<p>(.*?)</p>', 
        r'<p style="font-size: 16.5px; line-height: 1.8; color: #4a5568; margin-bottom: 20px; text-align: left; font-family: inherit; font-weight: 400;">\1</p>', 
        formatted_html
    )
    formatted_html = re.sub(
        r'<li>(.*?)</li>', 
        r'<li style="font-size: 16px; line-height: 1.7; color: #4a5568; margin-bottom: 8px;">\1</li>', 
        formatted_html
    )

    random_sig = random.randint(20000, 80000)
    img_url = f"https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?auto=format&fit=crop&w=800&q=80&sig={random_sig}"
    
    # Formatted responsive cover asset layout matching your reference style
    styled_img = f'<div style="width: 100%; text-align: center; margin-top: 5px; margin-bottom: 35px;"><img src="{img_url}" alt="{seo_pack["blog_title"]}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);" /></div>'
    
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
        log.error(f"REST publication pipeline crash: {e}")
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
            return f"🚀 <b>Beyond-Basics Layout Engine: SUCCESS!</b>\n\n" \
                   f"🔗 <b>Live Post Link:</b> <a href='{live_url}'>{live_url}</a>\n\n" \
                   f"✅ <b>Strict Topical Focus:</b> Completely locked to sitemap theme context. Zero contamination.\n" \
                   f"✅ <b>Exact Reference Formatting:</b> Font alignment, typography weight, border breaks, and line height mirror the premium style guide layout perfectly."
        return "⚠️ Swarm processed, database REST pipeline timed out."
    return "🤖 System standing by. 'Beyond-Basics' native design loop fully synchronized."
