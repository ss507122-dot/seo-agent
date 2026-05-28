import os, json, logging, html, asyncio, requests
from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import gemini_client as gc
import wp_client as wp
import seo_prompts as P
import internal_linker as IL

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("seo-bot")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER = int(os.getenv("TELEGRAM_OWNER_ID", "0"))

def auth_ok(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == OWNER

async def guard(update: Update) -> bool:
    if not auth_ok(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return False
    return True

def esc(s: str) -> str:
    return html.escape(str(s) if s is not None else "")

def get_professional_image_url(data, topic):
    """
    Gemini ke output se image prompt nikal kar professional title-based image link generate karne ka function.
    """
    img_prompt = data.get("image_prompt") or f"A professional high-resolution studio photograph of a clean, modern clinical pharmacy setting with branded medicine box for {topic}, WebP digital commercial photography."
    encoded_prompt = requests.utils.quote(img_prompt) if hasattr(requests, 'utils') else topic.replace(" ", "_")
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&private=true"

async def start(update, ctx):
    if not await guard(update): return
    await update.message.reply_text(
        "👋 <b>MedzPalace SEO Bot</b> ready.\n\nSend /help for full command list.",
        parse_mode=ParseMode.HTML)

async def help_cmd(update, ctx):
    if not await guard(update): return
    msg = (
"<b>📝 Blog</b>\n"
"<code>/blog Topic | keyword | words</code> — full SEO blog (draft)\n"
"<code>/quickblog Topic</code> — 800 words quick blog\n"
"<code>/seopost POST_ID</code> — regenerate Rank Math meta for an existing post\n"
"<code>/listposts</code> — latest 10 posts with IDs\n\n"
"<b>🛒 Products</b>\n"
"<code>/product Name | salt | pack | category | price</code>\n"
"<code>/seoproduct PRODUCT_ID</code>\n"
"<code>/listproducts [search]</code>\n\n"
"<b>🎯 SEO helpers</b>\n"
"<code>/meta Topic</code> — meta title + desc + keyword\n"
"<code>/keywords Topic</code> — 25 keyword ideas\n"
"<code>/faq Topic</code> — 8 SEO FAQs\n"
"<code>/rewrite &lt;text&gt;</code>\n\n"
"<b>📊 Bulk (Google Sheet)</b>\n"
"<code>/bulkblog</code>\n\n"
"<b>🔧</b> <code>/whoami</code>")
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def whoami(update, ctx):
    if not await guard(update): return
    code, data = wp.whoami()
    if code == 200:
        await update.message.reply_text(f"✅ WP OK as <b>{esc(data.get('name'))}</b> (id {data.get('id')})", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"❌ WP {code}: {esc(str(data)[:300])}", parse_mode=ParseMode.HTML)

def parse_pipe(text, n):
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < n: return None
    return parts

async def blog(update, ctx):
    if not await guard(update): return
    raw = update.message.text.split(" ", 1)
    if len(raw) < 2:
        await update.message.reply_text("Usage: /blog Topic | keyword | words"); return
    parts = parse_pipe(raw[1], 1)
    topic = parts[0]
    keyword = parts[1] if len(parts) > 1 else topic
    words = parts[2] if len(parts) > 2 else "1000"
    await update.message.reply_text(f"✍️ Writing blog… ({esc(words)} words)\nTopic: {esc(topic)}", parse_mode=ParseMode.HTML)
    try:
        data = gc.generate_json(P.BLOG_PROMPT.format(topic=topic, keyword=keyword, words=words))
        
        # Dynamic image url generation based on title/prompt
        img_url = get_professional_image_url(data, topic)
        
        post = wp.create_post(
            title=data["title"], content=data["content_html"], status="draft",
            excerpt=data.get("excerpt"),
            rm_title=data.get("meta_title"), rm_desc=data.get("meta_description"),
            rm_focus=data.get("focus_keyword"),
            featured_image_url=img_url)
            
        link = post.get("link") or f"https://medzpalace.com/?p={post['id']}"
        await update.message.reply_text(
            f"✅ Draft created (ID <b>{post['id']}</b>)\n<b>Title:</b> {esc(data['title'])}\n"
            f"<b>Meta:</b> {esc(data.get('meta_title'))}\n<b>Focus KW:</b> {esc(data.get('focus_keyword'))}\n"
            f"🔗 {esc(link)}\n\nReview & publish from WP dashboard.",
            parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        log.exception("blog failed")
        await update.message.reply_text(f"❌ Error: {esc(str(e))[:500]}")

async def quickblog(update, ctx):
    if not await guard(update): return
    raw = update.message.text.split(" ", 1)
    if len(raw) < 2:
        await update.message.reply_text("Usage: /quickblog Topic"); return
    topic = raw[1]
    update.message.text = f"/blog {topic} | {topic} | 800"
    await blog(update, ctx)

async def seopost(update, ctx):
    if not await guard(update): return
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text("Usage: /seopost POST_ID"); return
    try:
        pid = int(parts[1])
        post = wp.get_post(pid)
        title = post["title"]["rendered"]
        excerpt = post.get("excerpt",{}).get("rendered","")
        prompt = f'Topic from existing post title="{title}" excerpt="{excerpt[:300]}"\n' + P.META_PROMPT.format(topic=title)
        meta = gc.generate_json(prompt)
        wp.update_post_meta(pid, rm_title=meta["meta_title"], rm_desc=meta["meta_description"], rm_focus=meta["focus_keyword"])
        await update.message.reply_text(
            f"✅ Meta updated for post {pid}\n<b>Title:</b> {esc(meta['meta_title'])}\n"
            f"<b>Desc:</b> {esc(meta['meta_description'])}\n<b>KW:</b> {esc(meta['focus_keyword'])}",
            parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ {esc(str(e))[:400]}")

async def listposts(update, ctx):
    if not await guard(update): return
    try:
        posts = wp.list_posts(10)
        lines = [f"<b>{p['id']}</b> [{p['status']}] {esc(p['title']['rendered'])[:70]}" for p in posts]
        await update.message.reply_text("\n".join(lines) or "No posts.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ {esc(str(e))[:300]}")

async def product(update, ctx):
    if not await guard(update): return
    raw = update.message.text.split(" ", 1)
    if len(raw) < 2:
        await update.message.reply_text("Usage: /product Name | salt | pack | category | price"); return
    parts = parse_pipe(raw[1], 5)
    if not parts:
        await update.message.reply_text("Need 5 pipe-separated values: Name | salt | pack | category | price"); return
    name, salt, pack, cat, price = parts[:5]
    await update.message.reply_text(f"🛒 Creating product: {esc(name)}…", parse_mode=ParseMode.HTML)
    try:
        data = gc.generate_json(P.PRODUCT_PROMPT.format(name=name, salt=salt, pack=pack, category=cat, price=price))
        prod = wp.create_product(
            name=data["name"], description=data["long_description_html"],
            short_description=data["short_description_html"], regular_price=price,
            sku=data.get("sku"), categories=[cat], status="draft",
            rm_title=data.get("meta_title"), rm_desc=data.get("meta_description"),
            rm_focus=data.get("focus_keyword"))
        await update.message.reply_text(
            f"✅ Product draft created (ID <b>{prod['id']}</b>)\nSKU: {esc(data.get('sku'))}\n"
            f"Meta: {esc(data.get('meta_title'))}\n🔗 {esc(prod.get('permalink'))}",
            parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        log.exception("product failed")
        await update.message.reply_text(f"❌ {esc(str(e))[:500]}")

async def seoproduct(update, ctx):
    if not await guard(update): return
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text("Usage: /seoproduct PRODUCT_ID"); return
    try:
        pid = int(parts[1])
        import requests
        from requests.auth import HTTPBasicAuth
        base = os.getenv("WP_BASE_URL").rstrip("/")
        r = requests.get(f"{base}/wp-json/wc/v3/products/{pid}",
                         auth=HTTPBasicAuth(os.getenv("WP_USER"), os.getenv("WP_APP_PASS","").replace(" ","")),
                         timeout=30)
        r.raise_for_status()
        p = r.json()
        topic = p["name"]
        meta = gc.generate_json(P.META_PROMPT.format(topic=topic))
        wp.update_product_meta(pid, rm_title=meta["meta_title"], rm_desc=meta["meta_description"], rm_focus=meta["focus_keyword"])
        await update.message.reply_text(
            f"✅ Product meta updated\n<b>Title:</b> {esc(meta['meta_title'])}\n<b>Desc:</b> {esc(meta['meta_description'])}\n<b>KW:</b> {esc(meta['focus_keyword'])}",
            parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ {esc(str(e))[:400]}")

async def listproducts(update, ctx):
    if not await guard(update): return
    parts = update.message.text.split(" ", 1)
    search = parts[1] if len(parts) > 1 else None
    try:
        items = wp.list_products(10, search=search)
        lines = [f"<b>{p['id']}</b> [{p['status']}] {esc(p['name'])[:60]} — ₹{esc(p.get('price'))}" for p in items]
        await update.message.reply_text("\n".join(lines) or "No products.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ {esc(str(e))[:300]}")

async def meta_cmd(update, ctx):
    if not await guard(update): return
    raw = update.message.text.split(" ", 1)
    if len(raw) < 2:
        await update.message.reply_text("Usage: /meta Topic"); return
    try:
        m = gc.generate_json(P.META_PROMPT.format(topic=raw[1]))
        await update.message.reply_text(
            f"<b>Title:</b> {esc(m['meta_title'])}\n<b>Desc:</b> {esc(m['meta_description'])}\n<b>KW:</b> {esc(m['focus_keyword'])}",
            parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ {esc(str(e))[:300]}")

async def keywords(update, ctx):
    if not await guard(update): return
    raw = update.message.text.split(" ", 1)
    if len(raw) < 2:
        await update.message.reply_text("Usage: /keywords Topic"); return
    try:
        d = gc.generate_json(P.KEYWORDS_PROMPT.format(topic=raw[1]))
        lines = [f"• {esc(k['kw'])} <i>({esc(k.get('intent',''))} / {esc(k.get('volume_guess',''))})</i>" for k in d["keywords"][:25]]
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ {esc(str(e))[:300]}")

async def faq_cmd(update, ctx):
    if not await guard(update): return
    raw = update.message.text.split(" ", 1)
    if len(raw) < 2:
        await update.message.reply_text("Usage: /faq Topic"); return
    try:
        d = gc.generate_json(P.FAQ_PROMPT.format(topic=raw[1]))
        out = []
        for i, f in enumerate(d["faqs"], 1):
            out.append(f"<b>Q{i}. {esc(f['q'])}</b>\n{esc(f['a'])[:400]}")
        text = "\n\n".join(out)
        for chunk_start in range(0, len(text), 3800):
            await update.message.reply_text(text[chunk_start:chunk_start+3800], parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ {esc(str(e))[:300]}")

async def rewrite(update, ctx):
    if not await guard(update): return
    raw = update.message.text.split(" ", 1)
    if len(raw) < 2:
        await update.message.reply_text("Usage: /rewrite <text>"); return
    try:
        d = gc.generate_json(P.REWRITE_PROMPT.format(text=raw[1]))
        text = d["rewritten_html"]
        for chunk_start in range(0, len(text), 3800):
            await update.message.reply_text(text[chunk_start:chunk_start+3800], parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ {esc(str(e))[:300]}")

async def bulkblog(update, ctx):
    if not await guard(update): return
    try:
        import sheets_client as sc
        rows = sc.read_topics()
    except Exception as e:
        await update.message.reply_text(f"⚠️ Sheet not configured: {esc(str(e))[:200]}\nUpload service_account.json to enable."); return
    await update.message.reply_text(f"📊 {len(rows)} topics found. Starting…")
    ok, fail = 0, 0
    for i, row in enumerate(rows, 1):
        topic = row.get("topic"); kw = row.get("keyword") or topic; w = row.get("words") or 1000
        if not topic: continue
        try:
            d = gc.generate_json(P.BLOG_PROMPT.format(topic=topic, keyword=kw, words=w))
            
            img_url = get_professional_image_url(d, topic)
            
            post = wp.create_post(title=d["title"], content=d["content_html"], status="draft",
                                  excerpt=d.get("excerpt"), rm_title=d.get("meta_title"),
                                  rm_desc=d.get("meta_description"), rm_focus=d.get("focus_keyword"),
                                  featured_image_url=img_url)
            ok += 1
            await update.message.reply_text(f"✅ {i}/{len(rows)} → post {post['id']} ({esc(topic)[:60]})", parse_mode=ParseMode.HTML)
        except Exception as e:
            fail += 1
            await update.message.reply_text(f"❌ {i}/{len(rows)} {esc(topic)[:40]}: {esc(str(e))[:200]}", parse_mode=ParseMode.HTML)
    await update.message.reply_text(f"🏁 Done. ✅ {ok}   ❌ {fail}")



async def linkposts_cmd(update, ctx):
    if not await guard(update): return
    await update.message.reply_text("🔗 Internal linking started...")
    try:
        IL.run(dry_run=False, post_types=["posts", "pages"])
        await update.message.reply_text("✅ Internal links injected successfully!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {esc(str(e))[:400]}")



async def fallback(update, ctx):
    if not await guard(update): return
    await update.message.reply_text("Type /help to see commands.")

def main():
    if not TOKEN or not OWNER:
        raise SystemExit("TELEGRAM_BOT_TOKEN / TELEGRAM_OWNER_ID missing in .env")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CommandHandler("blog", blog))
    app.add_handler(CommandHandler("quickblog", quickblog))
    app.add_handler(CommandHandler("seopost", seopost))
    app.add_handler(CommandHandler("listposts", listposts))
    app.add_handler(CommandHandler("product", product))
    app.add_handler(CommandHandler("seoproduct", seoproduct))
    app.add_handler(CommandHandler("listproducts", listproducts))
    app.add_handler(CommandHandler("meta", meta_cmd))
    app.add_handler(CommandHandler("keywords", keywords))
    app.add_handler(CommandHandler("faq", faq_cmd))
    app.add_handler(CommandHandler("rewrite", rewrite))
    app.add_handler(CommandHandler("bulkblog", bulkblog))
    app.add_handler(CommandHandler("linkposts", linkposts_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))
    log.info("Bot starting (long-poll)…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
