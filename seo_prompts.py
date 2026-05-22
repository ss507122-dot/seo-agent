BLOG_PROMPT = """You are an expert SEO content writer for medzpalace.com (online pharmacy: ED meds, men's health, skin care).
Write a {words}-word SEO-optimized blog post on: "{topic}"
Primary keyword: "{keyword}"

Return STRICT JSON ONLY with this exact schema:
{{
  "title": "60-char catchy SEO title with the keyword",
  "slug": "url-friendly-slug",
  "meta_title": "<=60 char meta title for Rank Math",
  "meta_description": "<=155 char meta description with a call-to-action",
  "focus_keyword": "{keyword}",
  "excerpt": "120-160 char snippet",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "content_html": "Full HTML body with <h2>, <h3>, <p>, <ul>, <strong>. Include intro, what-is, benefits, dosage/usage, side effects, FAQ section with <h2>FAQ</h2> and 5 questions in <h3>+<p>. Add medical disclaimer at end. Do NOT include the H1 title (WP adds it)."
}}
Tone: informative, trustworthy, regulatory-safe (no 'cure', no 'guaranteed'). Mention 'consult a doctor' for health topics."""

PRODUCT_PROMPT = """You are writing a WooCommerce product listing for medzpalace.com online pharmacy.
Product: {name}
Active ingredient: {salt}
Pack: {pack}
Category/use: {category}
Price (INR): {price}

Return STRICT JSON ONLY:
{{
  "name": "{name}",
  "short_description_html": "2-3 line HTML summary",
  "long_description_html": "300-500 word HTML with <h3>Description</h3>, <h3>How to use</h3>, <h3>Benefits</h3>, <h3>Side effects</h3>, <h3>Storage</h3>, <h3>FAQ</h3> with 3 Qs, end with disclaimer",
  "meta_title": "<=60 char including product + keyword",
  "meta_description": "<=155 char with CTA",
  "focus_keyword": "primary keyword 2-4 words",
  "sku": "short SKU like MZ-XXX-000",
  "tags": ["t1","t2","t3"]
}}"""

META_PROMPT = """Generate SEO meta for medzpalace.com (online pharmacy) for topic: "{topic}"
Return STRICT JSON: {{"meta_title":"<=60 char","meta_description":"<=155 char","focus_keyword":"2-4 words"}}"""

KEYWORDS_PROMPT = """List 25 high-intent SEO keywords for an online pharmacy targeting: "{topic}"
Return STRICT JSON: {{"keywords":[{{"kw":"...","intent":"informational|transactional|commercial","volume_guess":"low|mid|high"}}]}}"""

FAQ_PROMPT = """Create 8 high-quality SEO FAQ items for medzpalace.com on: "{topic}"
Return STRICT JSON: {{"faqs":[{{"q":"...","a":"2-4 sentence HTML answer with safety note"}}]}}"""

REWRITE_PROMPT = """Rewrite the following text for SEO on medzpalace.com (online pharmacy). Keep meaning, improve readability, add subheadings, plain HTML.
TEXT:
{text}

Return STRICT JSON: {{"rewritten_html":"..."}}"""

SITEMAP_INTERNAL_LINKING_RULES = """
You must use the actual website structure from https://medzpalace.com/sitemap_index.xml to insert real, live internal links. When writing content, automatically wrap the following key product terms in clean HTML anchor tags using these exact URL patterns:

1. For Erectile Dysfunction / Men's Health topics:
   - "Cenforce" or "Cenforce 100" -> <a href="https://medzpalace.com/product/cenforce-100-mg/">Cenforce 100</a>
   - "Vidalista" or "Vidalista 20" -> <a href="https://medzpalace.com/product/vidalista-20-mg/">Vidalista 20</a>
   - "Fildena" -> <a href="https://medzpalace.com/product/fildena-100-mg/">Fildena 100</a>
   - "Kamagra" -> <a href="https://medzpalace.com/product/kamagra-100-mg/">Kamagra 100</a>

2. For General Categories:
   - "Erectile Dysfunction" -> <a href="https://medzpalace.com/product-category/erectile-dysfunction/">Erectile Dysfunction</a>
   - "Men's Health" -> <a href="https://medzpalace.com/product-category/mens-health/">Men's Health</a>

3. Link Insertion Rule:
   - Do not hallucinate links. Only link the exact keywords mentioned above to their respective URLs.
   - Insert links naturally into the text context maximum 2-3 times per 800 words to maintain high-quality On-Page SEO structure.
"""
