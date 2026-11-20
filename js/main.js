/* NatřiTo – drobné interakce: mobilní menu, hlavička, prohlížeč fotek. Bez závislostí. */
(function () {
  'use strict';

  /* ---------- Mobilní menu ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) { toggle.setAttribute('aria-expanded', 'false'); nav.classList.remove('is-open'); }
    });
  }

  /* ---------- Stín hlavičky po odrolování ---------- */
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- Aktuální rok v patičce ---------- */
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ---------- Prohlížeč fotek (lightbox) ---------- */
  var box = document.querySelector('.lightbox');
  if (box && typeof box.showModal === 'function') {
    var img = box.querySelector('.lightbox__img');
    var cap = box.querySelector('.lightbox__caption');
    var items = [], index = 0;

    var show = function (i) {
      if (!items.length) return;
      index = (i + items.length) % items.length;
      var a = items[index];
      img.src = a.getAttribute('href');
      img.alt = a.dataset.caption || '';
      cap.textContent = a.dataset.caption || '';
      // přednačtení další fotky
      var next = items[(index + 1) % items.length];
      if (next && next !== a) { var pre = new Image(); pre.src = next.getAttribute('href'); }
    };

    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[data-lightbox]');
      if (!a) return;
      e.preventDefault();
      items = Array.prototype.slice.call(document.querySelectorAll('a[data-lightbox="' + a.dataset.lightbox + '"]'));
      // pořadí podle průběhu prací (data-i), ne podle pořadí v HTML
      items.sort(function (x, y) { return (+x.dataset.i || 0) - (+y.dataset.i || 0); });
      box.classList.toggle('lightbox--single', items.length < 2);
      // u renovací (před → po) začíná prohlížení titulní fotkou příběh od původního stavu
      var story = a.classList.contains('project__link') && a.closest('.project--story');
      show(story ? 0 : items.indexOf(a));
      box.showModal();
    });

    box.querySelector('.lightbox__prev').addEventListener('click', function () { show(index - 1); });
    box.querySelector('.lightbox__next').addEventListener('click', function () { show(index + 1); });
    box.querySelector('.lightbox__close').addEventListener('click', function () { box.close(); });
    box.addEventListener('click', function (e) { if (e.target === box || e.target.classList.contains('lightbox__figure')) box.close(); });
    box.addEventListener('close', function () { img.removeAttribute('src'); });
    document.addEventListener('keydown', function (e) {
      if (!box.open) return;
      if (e.key === 'ArrowLeft') show(index - 1);
      if (e.key === 'ArrowRight') show(index + 1);
    });

    // swipe na mobilu
    var x0 = null;
    box.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    box.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
      x0 = null;
    });
  }

  /* ---------- Interaktivní mapa Mapy.com (načte se až po kliknutí) ---------- */
  var mapBtn = document.querySelector('.map__open');
  var mapBox = document.getElementById('mapa-live');
  var dataEl = document.getElementById('mista-data');
  if (mapBtn && mapBox && dataEl) {
    var loadOnce = function (tag, attrs) {
      return new Promise(function (resolve, reject) {
        var el = document.createElement(tag);
        Object.keys(attrs).forEach(function (k) { el[k] = attrs[k]; });
        el.onload = resolve; el.onerror = reject;
        document.head.appendChild(el);
      });
    };

    mapBtn.addEventListener('click', function () {
      if (mapBox.dataset.ready) return;
      mapBtn.disabled = true;
      mapBtn.textContent = 'Načítám mapu…';
      Promise.all([
        loadOnce('link', { rel: 'stylesheet', href: 'vendor/leaflet/leaflet.css' }),
        loadOnce('script', { src: 'vendor/leaflet/leaflet.js' })
      ]).then(function () {
        var L = window.L;
        var key = mapBtn.dataset.mapyKey;
        var mista = JSON.parse(dataEl.textContent);
        var svg = document.querySelector('.map__svg');

        if (svg) { svg.parentNode.insertBefore(mapBox, svg); svg.style.display = 'none'; }
        mapBox.hidden = false;
        mapBtn.parentNode.hidden = true;
        mapBox.dataset.ready = '1';

        var map = L.map(mapBox, { scrollWheelZoom: false });
        var retina = window.devicePixelRatio > 1 ? '@2x' : '';
        L.tileLayer('https://api.mapy.com/v1/maptiles/basic/256' + retina + '/{z}/{x}/{y}?lang=cs&apikey=' + key, {
          minZoom: 5, maxZoom: 16,
          attribution: '<a href="https://api.mapy.com/copyright" target="_blank" rel="noopener">&copy; Seznam.cz a.s. a další</a>'
        }).addTo(map);

        // povinné logo Mapy.com
        var Logo = L.Control.extend({
          options: { position: 'bottomleft' },
          onAdd: function () {
            var a = L.DomUtil.create('a', 'map__mapy-logo');
            a.href = 'https://mapy.com/'; a.target = '_blank'; a.rel = 'noopener';
            a.innerHTML = '<img src="https://api.mapy.com/img/api/logo.svg" alt="Mapy.com" width="100" height="30">';
            L.DomEvent.disableClickPropagation(a);
            return a;
          }
        });
        new Logo().addTo(map);

        var bounds = [];
        mista.forEach(function (m) {
          var ll = [m.lat, m.lon];
          bounds.push(ll);
          var url = 'https://mapy.cz/zakladni?q=' + encodeURIComponent(m.obec) + '&x=' + m.lon + '&y=' + m.lat + '&z=12';
          L.circleMarker(ll, {
            radius: m.sidlo ? 9 : 7, weight: 2, color: '#fff',
            fillColor: m.sidlo ? '#3b2a1e' : '#9a4c1a', fillOpacity: 1
          }).addTo(map)
            .bindTooltip(m.obec + (m.sidlo ? ' – sídlo firmy' : ''), { direction: 'top', offset: [0, -6] })
            .bindPopup('<strong>' + m.obec + '</strong>' + (m.sidlo ? '<br>sídlo firmy' : '') +
              '<br><a href="' + url + '" target="_blank" rel="noopener">Otevřít na Mapy.cz</a>');
        });
        // velikost mapy se ustálí až po zobrazení kontejneru
        requestAnimationFrame(function () {
          map.invalidateSize();
          map.fitBounds(bounds, { padding: [20, 20], maxZoom: 9 });
        });
        // kolečkem myši přibližovat až po kliknutí do mapy (nebrání scrollování stránky)
        map.once('focus click', function () { map.scrollWheelZoom.enable(); });
      }).catch(function () {
        mapBtn.disabled = false;
        mapBtn.textContent = 'Mapu se nepodařilo načíst – zkusit znovu';
      });
    });
  }

})();
