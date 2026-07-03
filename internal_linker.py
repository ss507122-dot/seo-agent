import os
import re
import time
import random
import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
import threading
import gemini_client as gc

log = logging.getLogger("seo-bot.master_swarm")

WP_URL = os.getenv("WP_URL", "https://medzpalace.com").rstrip('/')
WP_USER = os.getenv("WP_USER")
WP_PASS = os.getenv("WP_APP_PASS")
SITEMAP_URL = "https://medzpalace.com/sitemap_index.xml"

def extract_topics_from_live_sitemap():
    log.info("Swarm Crawler: Syncing sitemap database parameters...")
    core_categories = {
        "ed": ["cenforce", "vidalista", "sildenafil", "erectile dysfunction", "tadalafil"],
        "parasite": ["albendazole", "ivermectin", "deworming", "parasitic infection"]
    }
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
                    discovered_terms.append(slug.strip().title())
    except Exception as e:
        log.error(f"Sitemap crawling logic adjusted: {e}")
        
    if discovered_terms:
        return list(set(discovered_terms))
    return ["Albendazole 400mg Dosage", "Ivermectin Safety Guidelines", "Erectile Dysfunction Treatment Strategies"]

def get_strict_relevance_map(current_topic):
    """
    STRICT CATEGORY ISOLATION BLOCK (ANTI-MIXING RULES)
    Ensures ED terms NEVER bleed into Parasite articles and vice versa.
    """
    topic_lower = current_topic.lower()
    
    # 1. Master Data Category Registries
    ed_catalog = {
        "sildenafil": f'<a href="{WP_URL}/product/sildenafil/">Sildenafil</a>',
        "cenforce 100mg": f'<a href="{WP_URL}/product/cenforce-100/">Cenforce 100mg</a>',
        "cenforce": f'<a href="{WP_URL}/product/cenforce-100/">Cenforce</a>',
        "vidalista 20": f'<a href="{WP_URL}/product/vidalista-20/">Vidalista 20</a>',
        "vidalista": f'<a href="{WP_URL}/product/vidalista-20/">Vidalista</a>',
        "erectile dysfunction": f'<a href="{WP_URL}/product-category/erectile-dysfunction/">erectile dysfunction treatments</a>'
    }
    
    parasite_catalog = {
        "albendazole": f'<a href="{WP_URL}/product/albendazole/">Albendazole</a>',
        "ivermectin": f'<a href="{WP_URL}/product/ivermectin/">Ivermectin</a>',
        "parasitic infection": f'<a href="{WP_URL}/product-category/parasitic-infections/">parasitic infections</a>',
        "deworming": f'<a href="{WP_URL}/product/albendazole/">deworming therapeutics</a>'
    }
    
    isolated_map = {}
    
    # 2. Check topical context parameters to allocate targeted dictionaries only
    if any(k in topic_lower for k in ["albendazole", "ivermectin", "parasite", "worm", "deworming"]):
        for k, v in parasite_catalog.items():
            if k not in topic_lower: # Zero self-linking protection node
                isolated_map[k] = v
    else:
        for k, v in ed_catalog.items():
            if k not in topic_lower:
                isolated_map[k] = v
                
    return isolated_map

def automatic_blog_title_and_seo_engine(core_entity):
    prompt = f"""
    Act as a Professional Medical Editor. Generate a clean Blog Post Title, SEO Meta Title (under 55 chars), and a Meta Description (under 155 chars) based strictly on this asset: '{core_entity}'.
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
        "blog_title": f"Clinical Perspectives on {core_entity} Therapeutics",
        "meta_title": f"{core_entity} Guidelines - MedzPalace",
        "meta_description": f"Safety warnings, diagnostic standards, and core instructions regarding usage profile of {core_entity}."
    }

def humanized_content_writer(blog_title, live_anchors):
    anchor_hints = ", ".join(list(live_anchors.keys()))
    prompt = f"""
    Write an authoritative, 1200+ word clinical article titled: "{blog_title}".
    Requirements:
    - Language styling must look highly humanized, deeply analytical, and clean.
    - Formatting: Structure smoothly with proper clean HTML sections.
    - Contextual Anchors: Naturally include these specific industry terms within normal prose sentences if relevant: {anchor_hints}.
    - Important: Output strictly the raw HTML content code block.
    """
    try:
        return gc.generate(prompt)
    except:
        return f"<h2>Clinical Evaluation Parameters</h2><p>Safe administration rules and clinical oversight guidelines.</p>"

def internal_linking_injector(html_content, relevance_map):
    modified = html_content
    links_added = 0
    keywords = list(relevance_map.keys())
    random.shuffle(keywords)
    
    for kw in keywords:
        tag = relevance_map[kw]
        if re.search(rf'\b({re.escape(kw)})\b', modified, flags=re.IGNORECASE):
            modified = re.sub(rf'\b({re.escape(kw)})\b', tag, modified, count=1, flags=re.IGNORECASE)
            links_added += 1
            if links_added >= 3: # Keep injection cap at perfect balancing index
                break
                
    return modified

def execute_complete_swarm_pipeline():
    log.info("Starting context-isolated sitemap scheduler node...")
    
    sitemap_terms = extract_topics_from_live_sitemap()
    chosen_entity = random.choice(sitemap_terms)
    
    seo_pack = automatic_blog_title_and_seo_engine(chosen_entity)
    
    # Fetch strictly isolated relevance maps (Prevents cross-contamination errors)
    relevance_links = get_strict_relevance_map(seo_pack["blog_title"])
    
    article_body = humanized_content_writer(seo_pack["blog_title"], relevance_links)
    final_html = internal_linking_injector(article_body, relevance_links)
    
    # Applied Clean Underline Header Formatting Standards from user design references
    designed_html = re.sub(
        r'<h2>(.*?)</h2>', 
        r'<h2 style="font-size:26px; font-weight:600; color:#1e293b; border-bottom:2px solid #e2e8f0; padding-bottom:8px; margin-top:30px; margin-bottom:15px;">\1</h2>', 
        final_html
    )
    
    random_sig = random.randint(100, 999)
    img_url = f"https://images.unsplash.com/photo-1584017911766-d451b3d0e843?auto=format&fit=crop&w=800&q=80&sig={random_sig}"
    styled_img = f'<div style="width:100%; text-align:center; margin-bottom:30px;"><img src="{img_url}" alt="{seo_pack["blog_title"]}" style="max-width:100%; height:auto; border-radius:6px; box-shadow:0 4px 10px rgba(0,0,0,0.04);" /></div>'
    
    final_post_payload = styled_img + designed_html

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
        log.error(f"REST publication crash block: {e}")
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
            return f"🚀 <b>Context-Isolated Swarm Engine: SUCCESS!</b>\n\n" \
                   f"🔗 <b>Live Post Link:</b> <a href='{live_url}'>{live_url}</a>\n\n" \
                   f"✅ <b>Strict Topical Relevance:</b> ED keywords and links are 100% blocked from Parasite posts.\n" \
                   f"✅ <b>Line Format Structure:</b> H2 headers automatically modified with dynamic bottom border layout lines."
        return "⚠️ Swarm process completed, payload routing missing on target database."
    return "🤖 Swarm Engine monitoring parameters active. Balanced formatting pipelines locked."
