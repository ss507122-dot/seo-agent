import os, requests, base64
from requests.auth import HTTPBasicAuth

BASE = os.getenv("WP_BASE_URL", "").rstrip("/")
USER = os.getenv("WP_USER")
APP_PASS = os.getenv("WP_APP_PASS", "").replace(" ", "")
AUTH = HTTPBasicAuth(USER, APP_PASS)
H = {"Content-Type": "application/json"}

def whoami():
    r = requests.get(f"{BASE}/wp-json/wp/v2/users/me", auth=AUTH, timeout=30)
    return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else r.text

def upload_image_from_url(image_url, title="Feature Image"):
    """
    Image URL se image download karke WordPress Media Library me upload karne ka function.
    """
    try:
        img_resp = requests.get(image_url, timeout=30)
        img_resp.raise_for_status()
        filename = f"{title.lower().replace(' ', '_')[:20]}.jpg"
        media_headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/jpeg"
        }
        r = requests.post(f"{BASE}/wp-json/wp/v2/media", data=img_resp.content, auth=AUTH, headers=media_headers, timeout=60)
        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        print(f"Image upload error: {e}")
        return None

def create_post(title, content, status="draft", categories=None, tags=None,
                rm_title=None, rm_desc=None, rm_focus=None, excerpt=None, featured_image_url=None):
    meta = {}
    if rm_title: meta["rank_math_title"] = rm_title
    if rm_desc:  meta["rank_math_description"] = rm_desc
    if rm_focus: meta["rank_math_focus_keyword"] = rm_focus
    payload = {"title": title, "content": content, "status": status}
    if excerpt: payload["excerpt"] = excerpt
    if categories: payload["categories"] = categories
    if tags: payload["tags"] = tags
    if meta: payload["meta"] = meta
    
    # Image upload system
    if featured_image_url:
        media_id = upload_image_from_url(featured_image_url, title)
        if media_id: 
            payload["featured_media"] = media_id
            
    r = requests.post(f"{BASE}/wp-json/wp/v2/posts", json=payload, auth=AUTH, headers=H, timeout=60)
    r.raise_for_status()
    return r.json()

def update_post_meta(post_id, rm_title=None, rm_desc=None, rm_focus=None):
    meta = {}
    if rm_title: meta["rank_math_title"] = rm_title
    if rm_desc:  meta["rank_math_description"] = rm_desc
    if rm_focus: meta["rank_math_focus_keyword"] = rm_focus
    r = requests.post(f"{BASE}/wp-json/wp/v2/posts/{post_id}", json={"meta": meta}, auth=AUTH, headers=H, timeout=60)
    r.raise_for_status()
    return r.json()

def list_posts(per_page=10, search=None):
    p = {"per_page": per_page, "status": "publish,draft"}
    if search: p["search"] = search
    r = requests.get(f"{BASE}/wp-json/wp/v2/posts", params=p, auth=AUTH, timeout=30)
    r.raise_for_status()
    return r.json()

def get_post(post_id):
    r = requests.get(f"{BASE}/wp-json/wp/v2/posts/{post_id}", auth=AUTH, timeout=30)
    r.raise_for_status()
    return r.json()

def create_product(name, description, short_description, regular_price,
                   sku=None, categories=None, status="draft",
                   rm_title=None, rm_desc=None, rm_focus=None):
    meta_data = []
    if rm_title: meta_data.append({"key":"rank_math_title","value":rm_title})
    if rm_desc:  meta_data.append({"key":"rank_math_description","value":rm_desc})
    if rm_focus: meta_data.append({"key":"rank_math_focus_keyword","value":rm_focus})
    payload = {
        "name": name, "type": "simple", "status": status,
        "description": description, "short_description": short_description,
        "regular_price": str(regular_price),
    }
    if sku: payload["sku"] = sku
    if categories: payload["categories"] = [{"id": c} if isinstance(c,int) else {"name": c} for c in categories]
    if meta_data: payload["meta_data"] = meta_data
    r = requests.post(f"{BASE}/wp-json/wc/v3/products", json=payload, auth=AUTH, headers=H, timeout=60)
    r.raise_for_status()
    return r.json()

def list_products(per_page=10, search=None):
    p = {"per_page": per_page}
    if search: p["search"] = search
    r = requests.get(f"{BASE}/wp-json/wc/v3/products", params=p, auth=AUTH, timeout=30)
    r.raise_for_status()
    return r.json()

def update_product_meta(product_id, rm_title=None, rm_desc=None, rm_focus=None):
    meta_data = []
    if rm_title: meta_data.append({"key":"rank_math_title","value":rm_title})
    if rm_desc:  meta_data.append({"key":"rank_math_description","value":rm_desc})
    if rm_focus: meta_data.append({"key":"rank_math_focus_keyword","value":rm_focus})
    r = requests.put(f"{BASE}/wp-json/wc/v3/products/{product_id}", json={"meta_data": meta_data}, auth=AUTH, headers=H, timeout=60)
    r.raise_for_status()
    return r.json()
