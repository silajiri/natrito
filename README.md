# NatřiTo – web

Statický web pro www.natrito.cz (broušení a nátěry srubů a roubenek – Pavel Ehl).
Čisté HTML + CSS + trocha JS, žádný framework, žádná databáze. Stačí libovolný hosting statických souborů.

## Struktura

```
index.html            hlavní stránka (jednostránkový web)
clanky/               převzaté články z původního webu
css/style.css         veškeré styly (vzhled „Dřevo a len“)
fonts/                písma hostovaná na webu (Fraunces, Source Sans 3)
js/main.js            menu, prohlížeč fotek
img/                  zpracované obrázky pro web (generuje tools/build.py)
favicon.ico, img/favicon.svg, img/apple-touch-icon.png
tools/realizace.json  seznam realizací (popisky, pořadí, fotky)
tools/mista.json      obce na mapě „Kde jsme pracovali“ (jen obec + souřadnice středu)
tools/cz-hranice.json obrys ČR pro mapu (© přispěvatelé OpenStreetMap)
tools/build.py        zpracování fotek + vložení galerií do index.html
assets/               originály (NEJSOU v gitu)
```

## Přidání nové realizace

1. Nahrajte originální fotky do `assets/images/`.
2. Do `tools/realizace.json` přidejte položku do sekce `realizace` (nejnovější nahoru):
   Fotky řaďte tak, jak šly práce za sebou; u renovací lze uvést fázi `"stage": "pred" | "behem" | "po"`.
   ```json
   { "id": "2025-06-srub-hrabova", "title": "Srub v ořechovém odstínu", "place": "Hrabová",
     "desc": "Broušení a nátěr Remmers", "date": "2025-06",
     "photos": ["assets/images/IMG_xxx.jpg", "assets/images/IMG_yyy.jpg"] }
   ```
   `id` = název výsledných souborů (rok-měsíc-popis, bez diakritiky). První fotka je titulní.
3. Spusťte `python tools/build.py` (potřebuje `pip install Pillow`).
   Vytvoří `img/realizace/<id>-01.webp` (velká) a `-01-t.webp` (náhled) a aktualizuje `index.html`.

## Přidání obce na mapu

Do `tools/mista.json` přidejte `{ "obec": "Název", "lat": 50.123, "lon": 15.456 }`
(souřadnice středu obce, např. z Mapy.cz) a spusťte `python tools/build.py`.

## Lokální náhled

```
python -m http.server 8765
```
a otevřít http://127.0.0.1:8765/

## Nasazení

Na hosting se nahrává vše kromě `assets/`, `tools/` a `README.md`.
