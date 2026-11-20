# NatřiTo – web

Statický web pro www.natrito.cz (broušení a nátěry srubů a roubenek – Pavel Ehl).
Čisté HTML + CSS + trocha JS, žádný framework, žádná databáze. Stačí libovolný hosting statických souborů.

## Struktura

```
index.html            hlavní stránka (jednostránkový web)
clanky/               převzaté články z původního webu
css/base.css          rozvržení a komponenty
css/theme-a|b|c.css   tři návrhy vzhledu (PROTOTYP – po výběru zůstane jeden)
js/main.js            menu, prohlížeč fotek
img/                  zpracované obrázky pro web (generuje tools/build.py)
favicon.ico, img/favicon.svg, img/apple-touch-icon.png
tools/realizace.json  seznam realizací (popisky, pořadí, fotky)
tools/build.py        zpracování fotek + vložení galerií do index.html
assets/               originály (NEJSOU v gitu)
```

## Přidání nové realizace

1. Nahrajte originální fotky do `assets/images/`.
2. Do `tools/realizace.json` přidejte položku do sekce `realizace` (nejnovější nahoru):
   ```json
   { "id": "2025-06-srub-hrabova", "title": "Srub v ořechovém odstínu", "place": "Hrabová",
     "desc": "Broušení a nátěr Remmers", "date": "2025-06",
     "photos": ["assets/images/IMG_xxx.jpg", "assets/images/IMG_yyy.jpg"] }
   ```
   `id` = název výsledných souborů (rok-měsíc-popis, bez diakritiky). První fotka je titulní.
3. Spusťte `python tools/build.py` (potřebuje `pip install Pillow`).
   Vytvoří `img/realizace/<id>-01.webp` (velká) a `-01-t.webp` (náhled) a aktualizuje `index.html`.

## Lokální náhled

```
python -m http.server 8765
```
a otevřít http://127.0.0.1:8765/ (návrhy: `?v=a`, `?v=b`, `?v=c`).

## Nasazení

Na hosting se nahrává vše kromě `assets/`, `tools/` a `README.md`.
