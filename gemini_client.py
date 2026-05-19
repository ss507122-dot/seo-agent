import os, json, time, requests

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

def generate(prompt: str, json_mode: bool = False, retries: int = 3) -> str:
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    if json_mode:
        body["generationConfig"] = {"responseMimeType": "application/json", "temperature": 0.7}
    else:
        body["generationConfig"] = {"temperature": 0.8}
    last = ""
    for i in range(retries):
        try:
            r = requests.post(URL, json=body, timeout=120)
            if r.status_code == 200:
                data = r.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            last = f"{r.status_code}: {r.text[:200]}"
        except Exception as e:
            last = str(e)
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"Gemini failed: {last}")

def generate_json(prompt: str) -> dict:
    text = generate(prompt, json_mode=True)
    try:
        return json.loads(text)
    except Exception:
        s, e = text.find("{"), text.rfind("}")
        if s >= 0 and e > s:
            return json.loads(text[s:e+1])
        raise
