"""Build skript pro web NatřiTo.

Co dělá:
  1. Z originálních fotek (assets/...) vytvoří webové verze ve formátu WebP:
       img/realizace/<id>-NN.webp     (velká, max 1600 px – pro prohlížeč fotek)
       img/realizace/<id>-NN-t.webp   (náhled pro mřížku)
     a „extra“ obrázky (hero, ilustrace postupu, články).
  2. Vygeneruje HTML galerií a vloží ho do index.html mezi značky
       <!-- gen:realizace --> ... <!-- /gen:realizace -->  (stejně archiv, ostatni)

Použití:  python tools/build.py           (zpracuje jen nové/změněné fotky)
          python tools/build.py --force   (přegeneruje vše)
Vyžaduje: Pillow  (pip install Pillow)
"""
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "realizace.json"
HTML_FILES = [ROOT / "index.html"]
FORCE = "--force" in sys.argv
sys.stdout.reconfigure(encoding="utf-8")  # české názvy souborů ve výpisu (Windows konzole)

LARGE = 1600          # delší strana velké fotky
THUMB_W, THUMB_H = 720, 540   # minimální rozměr náhledu (pokryje kartu 4:3 na retina displeji)
Q_LARGE, Q_THUMB = 80, 74

MONTHS = ["leden", "únor", "březen", "duben", "květen", "červen", "červenec",
          "srpen", "září", "říjen", "listopad", "prosinec"]


def fresh(src: Path, dst: Path) -> bool:
    return not FORCE and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime


def load(src: Path, crop=None) -> Image.Image:
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert("RGB")
    if crop:
        l, t, r, b = crop
        w, h = im.size
        im = im.crop((int(w * l / 100), int(h * t / 100), int(w * (1 - r / 100)), int(h * (1 - b / 100))))
    return im


def save_fit(im, dst: Path, longest: int, q: int):
    im = im.copy()
    im.thumbnail((longest, longest), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=q, method=6)
    return im.size


def save_width(im, dst: Path, width: int, q: int):
    w, h = im.size
    if w > width:
        im = im.resize((width, round(h * width / w)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=q, method=6)
    return im.size


def save_thumb(im, dst: Path):
    w, h = im.size
    scale = max(THUMB_W / w, THUMB_H / h)
    if scale < 1:
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=Q_THUMB, method=6)
    return im.size


def size_of(p: Path):
    with Image.open(p) as im:
        return im.size


def photo_word(n):
    return "fotka" if n == 1 else "fotky" if 2 <= n <= 4 else "fotek"


def fmt_date(d):
    if not d:
        return ""
    y, m = d.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def process_project(p):
    outs = []
    crops = p.get("crop", {})
    for i, rel in enumerate(p["photos"], 1):
        src = ROOT / rel
        base = ROOT / "img" / "realizace" / f"{p['id']}-{i:02d}"
        big, th = base.with_suffix(".webp"), Path(str(base) + "-t.webp")
        if fresh(src, big) and fresh(src, th):
            bsize, tsize = size_of(big), size_of(th)
        else:
            im = load(src, crops.get(rel))
            bsize = save_fit(im, big, LARGE, Q_LARGE)
            tsize = save_thumb(im, th)
            print(f"  {rel} -> {big.relative_to(ROOT).as_posix()}")
        outs.append((big.relative_to(ROOT).as_posix(), th.relative_to(ROOT).as_posix(), bsize, tsize))
    return outs


def card_html(p, outs, place_first=False):
    e = html.escape
    title = p["title"]
    place = p.get("place", "")
    if place_first and place:
        # starší realizace: nadpisem je lokalita, popisem provedená práce
        p = dict(p, title=place, place="", desc=" · ".join(x for x in [title, p.get("desc", "")] if x))
        title, place = p["title"], ""
    caption = " – ".join(x for x in [title, place, p.get("desc", "")] if x)
    big, th, _, (tw, thh) = outs[0]
    n = len(outs)
    meta_bits = [x for x in [place, fmt_date(p.get("date"))] if x]
    extra = "".join(
        f'<a href="{o[0]}" data-lightbox="{p["id"]}" data-caption="{e(caption)} ({k}/{n})"></a>'
        for k, o in enumerate(outs[1:], 2))
    return (
        f'<li class="project">\n'
        f'  <a class="project__link" href="{big}" data-lightbox="{p["id"]}" data-caption="{e(caption)}{f" (1/{n})" if n > 1 else ""}">\n'
        f'    <img src="{th}" width="{tw}" height="{thh}" alt="{e(caption)}" loading="lazy" decoding="async">\n'
        f'    <span class="project__count">{n} {photo_word(n)}</span>\n'
        f'  </a>\n'
        f'  <div class="project__meta">\n'
        f'    <h3 class="project__title">{e(title)}</h3>\n'
        + (f'    <p class="project__desc">{e(p["desc"])}</p>\n' if p.get("desc") else "")
        + (f'    <p class="project__place">{e(" · ".join(meta_bits))}</p>\n' if meta_bits else "")
        + f'  </div>\n'
        + (f'  <div hidden>{extra}</div>\n' if extra else "")
        + f'</li>'
    )


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fragments = {}
    for key, projects in data["sections"].items():
        print(f"[{key}]")
        cards = [card_html(p, process_project(p), place_first=(key != "realizace")) for p in projects]
        fragments[key] = "\n".join(cards)

    print("[extra]")
    for x in data.get("extra", []):
        src = ROOT / x["src"]
        im = None
        for w in x["widths"]:
            dst = ROOT / f"{x['out']}-{w}.webp"
            if fresh(src, dst):
                continue
            im = im or load(src, x.get("crop"))
            save_width(im, dst, w, Q_LARGE)
            print(f"  {x['src']} -> {dst.relative_to(ROOT).as_posix()}")

    for f in HTML_FILES:
        if not f.exists():
            continue
        s = f.read_text(encoding="utf-8")
        for key, frag in fragments.items():
            s = re.sub(rf"(<!-- gen:{key} -->).*?(<!-- /gen:{key} -->)",
                       lambda m: f"{m.group(1)}\n{frag}\n{m.group(2)}", s, flags=re.S)
        f.write_text(s, encoding="utf-8")
        print(f"HTML aktualizováno: {f.name}")


if __name__ == "__main__":
    main()
