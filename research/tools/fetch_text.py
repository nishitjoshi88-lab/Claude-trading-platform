#!/usr/bin/env python3
"""Fetch a URL and print readable text. Usage: fetch_text.py URL [max_chars] [offset]
Handles HTML and PDF. Honors the session HTTPS proxy via environment."""
import io, re, sys
import requests
url = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0
h = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9"}
try:
    r = requests.get(url, headers=h, timeout=40, allow_redirects=True)
except Exception as e:
    print(f"FETCH_ERROR {type(e).__name__}: {str(e)[:300]}"); sys.exit(1)
ct = r.headers.get("content-type", "")
if r.status_code >= 400:
    print(f"HTTP_{r.status_code} for {url}"); sys.exit(1)
if "pdf" in ct or url.lower().split("?")[0].endswith(".pdf"):
    from pypdf import PdfReader
    text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(r.content)).pages)
else:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form"]):
        t.decompose()
    text = soup.get_text("\n")
text = re.sub(r"\n\s*\n+", "\n", text)
text = re.sub(r"[ \t]+", " ", text)
print(f"[{len(text)} chars total; showing {offset}..{offset+limit}]")
print(text[offset:offset + limit])
