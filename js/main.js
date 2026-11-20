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

  /* ---------- PROTOTYP: přepínač návrhů (ve finální verzi odstranit) ---------- */
  var sw = document.querySelector('.theme-switch');
  if (sw) {
    var mark = function () {
      var t = document.documentElement.dataset.theme;
      sw.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.setTheme === t)); });
    };
    sw.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-set-theme]');
      if (!b) return;
      var v = b.dataset.setTheme;
      document.documentElement.dataset.theme = v;
      document.getElementById('theme-css').href = 'css/theme-' + v + '.css';
      try { localStorage.setItem('natrito-theme', v); } catch (err) { /* nevadí */ }
      var u = new URL(location.href); u.searchParams.set('v', v); history.replaceState(null, '', u);
      mark();
    });
    mark();
  }
})();
