"""Fetch the official sources in sources.json to plain-text snapshots under guidance/sources/.

    python3 guidance/fetch_sources.py            # all sources
    python3 guidance/fetch_sources.py dvla-public

The snapshots are not committed: several sources (NICE, Diabetes Care, ISPAD) are copyright
and this repository is public. references.json records the SHA-256 of the snapshot each quote
was taken from, and the tests check every quote against its snapshot whenever one is present,
so a refetch shows at once whether a source has changed under a quote.
"""
import hashlib
import html
import json
import os
import re
import sys
import urllib.request
from datetime import date
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sources")
SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer"}
BLOCK = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "br", "section", "table",
         "article", "dt", "dd", "td", "th", "ul", "ol"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        elif tag in BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        elif tag in BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def to_text(raw: str) -> str:
    p = _Text()
    p.feed(raw)
    text = html.unescape("".join(p.parts)).replace(" ", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln) + "\n"


def snapshot_text(path: str) -> str:
    """The body of a snapshot, without its two header lines."""
    with open(path, encoding="utf-8") as fh:
        return fh.read().split("\n", 2)[2]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    sources = json.load(open(os.path.join(os.path.dirname(HERE), "report", "guidance", "sources.json")))
    want = set(sys.argv[1:])
    os.makedirs(OUT, exist_ok=True)
    for s in sources:
        if want and s["id"] not in want:
            continue
        req = urllib.request.Request(s["url"], headers={"User-Agent": "Mozilla/5.0 (Macintosh)"})
        body = urllib.request.urlopen(req, timeout=60).read()
        if s["url"].lower().endswith(".pdf"):
            # pdftotext (poppler) keeps reading order; its output is normalised like the HTML's
            import subprocess
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                tmp.write(body)
                tmp.flush()
                raw = subprocess.run(["pdftotext", tmp.name, "-"], capture_output=True,
                                     text=True, check=True).stdout
            lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.replace("\u00a0", " ").split("\n")]
            text = "\n".join(ln for ln in lines if ln) + "\n"
        else:
            text = to_text(body.decode("utf-8", "replace"))
        with open(os.path.join(OUT, s["id"] + ".txt"), "w", encoding="utf-8") as fh:
            fh.write(f"# {s['url']}\n# retrieved {date.today().isoformat()}\n{text}")
        print(f"{s['id']}: {len(text):,} chars, sha256 {digest(text)[:16]}")


if __name__ == "__main__":
    main()
