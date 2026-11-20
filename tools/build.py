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
import urllib.parse
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


STAGES = {"pred": "původní stav", "behem": "během broušení", "po": "po nátěru"}
CACHE_FILE = ROOT / "tools" / ".build-cache.json"
CACHE = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}


def norm_photos(p):
    """Fotka může být řetězec (cesta) nebo {"src": cesta, "stage": "pred|behem|po"}."""
    return [x if isinstance(x, dict) else {"src": x} for x in p["photos"]]


def process_project(p):
    outs = []
    crops = p.get("crop", {})
    for i, ph in enumerate(norm_photos(p), 1):
        rel = ph["src"]
        src = ROOT / rel
        base = ROOT / "img" / "realizace" / f"{p['id']}-{i:02d}"
        big, th = base.with_suffix(".webp"), Path(str(base) + "-t.webp")
        key = big.relative_to(ROOT).as_posix()
        sig = [rel, crops.get(rel)]
        if fresh(src, big) and fresh(src, th) and CACHE.get(key) == sig:
            bsize, tsize = size_of(big), size_of(th)
        else:
            im = load(src, crops.get(rel))
            bsize = save_fit(im, big, LARGE, Q_LARGE)
            tsize = save_thumb(im, th)
            CACHE[key] = sig
            print(f"  {rel} -> {key}")
        outs.append({"big": key, "th": th.relative_to(ROOT).as_posix(), "tsize": tsize, "stage": ph.get("stage")})
    return outs


def card_html(p, outs, place_first=False):
    e = html.escape
    title = p["title"]
    place = p.get("place", "")
    if place_first and place:
        # starší realizace: nadpisem je lokalita, popisem provedená práce
        p = dict(p, title=place, place="", desc=" · ".join(x for x in [title, p.get("desc", "")] if x))
        title, place = p["title"], ""
    caption = " – ".join(x for x in [title, place] if x)
    n = len(outs)
    # titulní fotka = první „po“ (jinak první); malý náhled v rohu = první „před“
    cover = next((i for i, o in enumerate(outs) if o["stage"] == "po"), 0)
    before = next((i for i, o in enumerate(outs) if o["stage"] == "pred"), None)
    has_story = before is not None

    def attrs(i):
        o = outs[i]
        stage = STAGES.get(o["stage"])
        cap = caption + (f" – {stage}" if stage else (f" – {p['desc']}" if p.get("desc") else ""))
        cap += f" ({i + 1}/{n})" if n > 1 else ""
        return f'href="{o["big"]}" data-lightbox="{p["id"]}" data-i="{i}" data-caption="{e(cap)}"'

    c = outs[cover]
    tw, thh = c["tsize"]
    meta_bits = [x for x in [place, fmt_date(p.get("date"))] if x]
    hidden = "".join(f"<a {attrs(i)}></a>" for i in range(n) if i not in (cover, before))
    inset = ""
    if has_story:
        b = outs[before]
        inset = (f'  <a class="project__before" {attrs(before)}>\n'
                 f'    <img src="{b["th"]}" alt="Původní stav – {e(title)}" loading="lazy" decoding="async"><span>před</span>\n'
                 f'  </a>\n')
    return (
        f'<li class="project{" project--story" if has_story else ""}">\n'
        f'  <a class="project__link" {attrs(cover)}>\n'
        f'    <img src="{c["th"]}" width="{tw}" height="{thh}" alt="{e(caption)}" loading="lazy" decoding="async">\n'
        f'    <span class="project__count">{n} {photo_word(n)}</span>\n'
        f'  </a>\n'
        + inset
        + f'  <div class="project__meta">\n'
        f'    <h3 class="project__title">{e(title)}</h3>\n'
        + (f'    <p class="project__desc">{e(p["desc"])}</p>\n' if p.get("desc") else "")
        + (f'    <p class="project__place">{e(" · ".join(meta_bits))}</p>\n' if meta_bits else "")
        + f'  </div>\n'
        + (f'  <div hidden>{hidden}</div>\n' if hidden else "")
        + f'</li>'
    )


def cz_key(text):
    """Řazení podle české abecedy (č za c, ř za r, š za s, ž za z, ch za h)."""
    t = text.lower()
    letters = ["a", "b", "c", "č", "d", "e", "f", "g", "h", "ch", "i", "j", "k", "l", "m", "n", "o", "p", "q",
               "r", "ř", "s", "š", "t", "u", "v", "w", "x", "y", "z", "ž"]
    base = str.maketrans("áďéěíňóťúůý", "adeeinotuuy")
    key, i = [], 0
    while i < len(t):
        if t.startswith("ch", i):
            key.append(letters.index("ch")); i += 2; continue
        c = t[i]
        c2 = c if c in letters else c.translate(base)
        key.append(letters.index(c2) if c2 in letters else 100 + ord(c2))
        i += 1
    return key


def map_html():
    """Mapa ČR s obcemi, kde jsme pracovali (inline SVG, bez externích skriptů).
    Každá obec odkazuje na Mapy.cz. Data: tools/mista.json a tools/cz-hranice.json."""
    import math
    mista = json.loads((ROOT / "tools" / "mista.json").read_text(encoding="utf-8"))["mista"]
    border = json.loads((ROOT / "tools" / "cz-hranice.json").read_text(encoding="utf-8"))["body"]
    k, kx = 100, math.cos(math.radians(49.8))
    lon0, lat0 = 12.05, 51.08

    def xy(lon, lat):
        return round((lon - lon0) * kx * k, 1), round((lat0 - lat) * k, 1)

    pts = [xy(lon, lat) for lon, lat in border]
    w = max(p[0] for p in pts) + 6
    h = max(p[1] for p in pts) + 6
    d = "M" + " L".join(f"{x},{y}" for x, y in pts) + " Z"
    e = html.escape
    marks = []
    for m in sorted(mista, key=lambda m: m.get("sidlo", False)):   # sídlo kreslit nakonec (navrch)
        x, y = xy(m["lon"], m["lat"])
        url = f"https://mapy.cz/zakladni?q={urllib.parse.quote(m['obec'])}&x={m['lon']}&y={m['lat']}&z=12"
        anchor = "end" if x > w * 0.8 else "start"
        tx = x - 7 if anchor == "end" else x + 7
        label = m["obec"] + (" – sídlo firmy" if m.get("sidlo") else "")
        cls = "map__pt map__pt--home" if m.get("sidlo") else "map__pt"
        marks.append(
            f'<a class="{cls}" href="{url}" target="_blank" rel="noopener" aria-label="{e(label)} na Mapy.cz">'
            f'<circle cx="{x}" cy="{y}" r="{6 if m.get("sidlo") else 4.2}"/>'
            f'<text x="{tx}" y="{y + 4}" text-anchor="{anchor}">{e(label)}</text></a>')
    svg = (f'<svg class="map__svg" viewBox="-6 -6 {w + 6:.0f} {h + 6:.0f}" role="img" aria-labelledby="map-title">'
           f'<title id="map-title">Mapa České republiky s obcemi, kde jsme pracovali</title>'
           f'<path class="map__land" d="{d}"/>' + "".join(marks) + "</svg>")
    items = "".join(
        f'<li><a href="https://mapy.cz/zakladni?q={urllib.parse.quote(m["obec"])}&x={m["lon"]}&y={m["lat"]}&z=12" '
        f'target="_blank" rel="noopener">{e(m["obec"])}</a></li>' for m in sorted(mista, key=lambda m: cz_key(m["obec"])))
    # data pro interaktivní mapu Mapy.com (načítá se až po kliknutí, viz js/main.js)
    data = json.dumps([{"obec": m["obec"], "lat": m["lat"], "lon": m["lon"], "sidlo": bool(m.get("sidlo"))}
                       for m in sorted(mista, key=lambda m: cz_key(m["obec"]))], ensure_ascii=False)
    return (svg + f'\n<ul class="map__list">{items}</ul>'
            + f'\n<script type="application/json" id="mista-data">{data}</script>')


def cleanup(used):
    """Smaže z img/realizace soubory, které už nepatří k žádné realizaci."""
    for f in (ROOT / "img" / "realizace").glob("*.webp"):
        key = f.relative_to(ROOT).as_posix()
        if key not in used:
            f.unlink()
            CACHE.pop(key.replace("-t.webp", ".webp"), None)
            print(f"  smazáno: {key}")


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fragments = {}
    used = set()
    for key, projects in data["sections"].items():
        print(f"[{key}]")
        cards = []
        for p in projects:
            outs = process_project(p)
            used.update(x for o in outs for x in (o["big"], o["th"]))
            cards.append(card_html(p, outs, place_first=(key != "realizace")))
        fragments[key] = "\n".join(cards)
    fragments["mapa"] = map_html()
    print("[úklid]")
    cleanup(used)
    CACHE_FILE.write_text(json.dumps(CACHE, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

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
