// Shared "loading quotes" screen (#55). While an ebook paginates or an
// audiobook session spins up, show a random highlight the user has saved —
// quote in italics with book / chapter / author below — instead of a bare
// "Loading…" string. Used by reader.html (.loading), player.html (#overlay-msg),
// web/index.html (#content .loading), and the GreatReads pages (#loading-state).
//
// Press-and-hold to keep reading (Instagram-stories style): while a pointer is
// held down the rotation pauses AND — if the page's content finishes loading
// mid-hold — the reveal is deferred until release, so a long quote isn't yanked
// away. We watch the host element for the host's own "hide" (display:none /
// .hidden / .d-none) via a MutationObserver and, while held, revert it and
// replay it on release. This needs no cooperation from the host pages.
//
// Design notes:
//  - Reads a localStorage cache FIRST so a quote paints instantly (even
//    offline), then refreshes from /api/highlights?type=highlight for next time.
//  - Rotates every few seconds with a gentle cross-fade while loading lasts.
//  - Falls back to boilerplate literary quotes ONLY when the user has none.
//  - Theme-agnostic: quote inherits the host color; meta uses opacity.
//  - Auto-stops if the host gets hidden or its content is replaced (error text).
(function () {
    'use strict';

    var CACHE_KEY = 'gr.quotes.cache';
    var MAX_CACHE = 200;
    var ROTATE_MS = 7000;
    var FADE_MS = 450;

    // Shown only when the user has zero highlights. Real attributions; rendered
    // WITHOUT the "From your highlights" caption since they aren't the user's.
    var BOILERPLATE = [
        { text: 'A reader lives a thousand lives before he dies. The man who never reads lives only one.', author: 'George R.R. Martin', book: 'A Dance with Dragons' },
        { text: 'Until I feared I would lose it, I never loved to read. One does not love breathing.', author: 'Harper Lee', book: 'To Kill a Mockingbird' },
        { text: 'Books are a uniquely portable magic.', author: 'Stephen King', book: 'On Writing' },
        { text: 'That is part of the beauty of all literature. You discover that your longings are universal longings, that you’re not lonely and isolated from anyone. You belong.', author: 'F. Scott Fitzgerald' },
        { text: 'There is no friend as loyal as a book.', author: 'Ernest Hemingway' },
        { text: 'I have always imagined that Paradise will be a kind of library.', author: 'Jorge Luis Borges' },
        { text: 'We read to know we are not alone.', author: 'C.S. Lewis' },
        { text: 'A word after a word after a word is power.', author: 'Margaret Atwood' }
    ];

    var styleInjected = false;
    function injectStyle() {
        if (styleInjected) return;
        styleInjected = true;
        var css = ''
            + '.grq{max-width:560px;width:86vw;margin:0 auto;padding:8px 4px;text-align:center;'
            + 'opacity:0;transition:opacity ' + FADE_MS + 'ms ease;'
            + 'font-family:Georgia,"Times New Roman",serif;line-height:1.5;'
            + '-webkit-user-select:none;user-select:none;-webkit-touch-callout:none;'
            + '-webkit-tap-highlight-color:transparent;}'
            + '.grq.grq-in{opacity:1;}'
            + '.grq.grq-held{opacity:1 !important;}'
            + '.grq-cap{font-family:-apple-system,system-ui,sans-serif;font-style:normal;'
            + 'font-size:11px;letter-spacing:.14em;text-transform:uppercase;'
            + 'opacity:.5;margin-bottom:18px;}'
            + '.grq-text{font-style:italic;font-size:20px;margin:0 0 18px;'
            + 'display:-webkit-box;-webkit-line-clamp:9;-webkit-box-orient:vertical;overflow:hidden;}'
            + '.grq.grq-held .grq-text{-webkit-line-clamp:30;}'
            + '.grq-meta{font-family:-apple-system,system-ui,sans-serif;font-style:normal;'
            + 'font-size:13px;opacity:.7;line-height:1.7;}'
            + '.grq-book{font-weight:600;}'
            + '.grq-chapter{opacity:.85;}'
            + '.grq-author{display:block;opacity:.7;margin-top:2px;}'
            + '.grq-sep{opacity:.5;margin:0 7px;}'
            + '.grq-hint{font-family:-apple-system,system-ui,sans-serif;font-style:normal;'
            + 'font-size:11px;letter-spacing:.06em;opacity:.32;margin-top:22px;'
            + 'transition:opacity .3s ease;}'
            + '.grq.grq-held .grq-hint{opacity:.55;}';
        var el = document.createElement('style');
        el.id = 'grq-style';
        el.textContent = css;
        (document.head || document.documentElement).appendChild(el);
    }

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function readCache() {
        try {
            var raw = localStorage.getItem(CACHE_KEY);
            var arr = raw ? JSON.parse(raw) : null;
            return Array.isArray(arr) ? arr : [];
        } catch (_) { return []; }
    }

    function refreshCache(apiUrl, cb) {
        try {
            fetch(apiUrl + '/highlights?type=highlight')
                .then(function (r) { return r.ok ? r.json() : null; })
                .then(function (data) {
                    if (!data || !Array.isArray(data.items)) return;
                    var out = [];
                    for (var i = 0; i < data.items.length; i++) {
                        var it = data.items[i];
                        var t = (it && it.text ? String(it.text) : '').trim();
                        if (!t) continue;
                        out.push({
                            text: t,
                            book: (it.bookTitle || '').trim(),
                            author: (it.bookAuthor || '').trim(),
                            chapter: (it.chapter || '').trim()
                        });
                    }
                    if (out.length > MAX_CACHE) out = out.slice(0, MAX_CACHE);
                    try { localStorage.setItem(CACHE_KEY, JSON.stringify(out)); } catch (_) {}
                    if (cb) cb(out);
                })
                .catch(function () {});
        } catch (_) {}
    }

    function shuffle(a) {
        a = a.slice();
        for (var i = a.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var t = a[i]; a[i] = a[j]; a[j] = t;
        }
        return a;
    }

    function quoteHTML(q, isOwn) {
        var meta = '';
        var parts = [];
        if (q.book) parts.push('<span class="grq-book">' + esc(q.book) + '</span>');
        if (q.chapter) parts.push('<span class="grq-chapter">' + esc(q.chapter) + '</span>');
        var line1 = parts.join('<span class="grq-sep">&middot;</span>');
        var author = q.author ? '<span class="grq-author">' + esc(q.author) + '</span>' : '';
        if (line1 || author) meta = '<div class="grq-meta">' + line1 + author + '</div>';
        var cap = isOwn ? '<div class="grq-cap">&#10022; From your highlights</div>' : '';
        return '<div class="grq">' + cap
            + '<blockquote class="grq-text">&ldquo;' + esc(q.text) + '&rdquo;</blockquote>'
            + meta
            + '<div class="grq-hint">Press &amp; hold to keep reading</div>'
            + '</div>';
    }

    // Module state — only one loading screen is ever live at a time.
    var hostEl = null;
    var timer = null;
    var pool = [];
    var poolIsOwn = false;
    var idx = 0;
    // Press-and-hold state.
    var held = false;          // a pointer is currently held down
    var pendingReveal = false; // content finished loading while held — reveal on release
    var pendingHide = null;    // {class, style} captured from the host's deferred hide
    var observer = null;
    var catcher = null;        // full-screen transparent overlay that captures the hold

    function isHidden(el) {
        if (!el) return true;
        if (el.classList.contains('d-none') || el.classList.contains('hidden')) return true;
        if (el.style && el.style.display === 'none') return true;
        try { return getComputedStyle(el).display === 'none'; } catch (_) { return false; }
    }

    function stillValid() {
        // Auto-stop if the host vanished or its content was replaced by something
        // other than our quote (e.g. an error message). The hidden case is
        // handled by the observer; checked here too as a backstop.
        return hostEl && hostEl.isConnected
            && !isHidden(hostEl)
            && hostEl.querySelector('.grq');
    }

    function paint(q) {
        if (!hostEl) return;
        hostEl.innerHTML = quoteHTML(q, poolIsOwn);
        var node = hostEl.querySelector('.grq');
        if (held && node) node.classList.add('grq-held'); // keep expanded while reading
        // Next frame so the fade-in transition runs.
        requestAnimationFrame(function () {
            var n = hostEl && hostEl.querySelector('.grq');
            if (n) n.classList.add('grq-in');
        });
    }

    function rotate() {
        if (held) return;               // paused while holding
        if (!stillValid()) { teardown(); return; }
        if (!pool.length) return;
        var node = hostEl.querySelector('.grq');
        idx = (idx + 1) % pool.length;
        var next = pool[idx];
        if (node) {
            node.classList.remove('grq-in'); // fade out
            setTimeout(function () { if (!held && stillValid()) paint(next); }, FADE_MS);
        } else {
            paint(next);
        }
    }

    function setPool(list, isOwn) {
        if (!list || !list.length) return;
        pool = shuffle(list);
        poolIsOwn = !!isOwn;
        idx = 0;
        if (hostEl) paint(pool[0]);
    }

    // ----- Press-and-hold -----
    function onDown(e) {
        if (!hostEl) return;
        held = true;
        if (timer) { clearInterval(timer); timer = null; } // pause rotation
        // Capture the pointer so move/up keep targeting the catcher even if the
        // finger drifts — without this, a tiny movement drops the hold.
        if (catcher && e && e.pointerId != null) {
            try { catcher.setPointerCapture(e.pointerId); } catch (_) {}
        }
        var node = hostEl.querySelector('.grq');
        if (node) node.classList.add('grq-held');
    }

    function onUp() {
        if (!held) return;
        held = false;
        var node = hostEl && hostEl.querySelector('.grq');
        if (node) node.classList.remove('grq-held');
        if (pendingReveal) {
            // Content loaded while we were holding — now actually reveal it.
            applyPendingHide();
            teardown();
        } else if (hostEl && !timer) {
            timer = setInterval(rotate, ROTATE_MS); // resume rotation
        }
    }

    function applyPendingHide() {
        if (!pendingHide || !hostEl) return;
        if (pendingHide.class === null) hostEl.removeAttribute('class');
        else hostEl.setAttribute('class', pendingHide.class);
        if (pendingHide.style === null) hostEl.removeAttribute('style');
        else hostEl.setAttribute('style', pendingHide.style);
        pendingHide = null;
    }

    // The host page just changed class/style. If that hid the loading screen:
    //  - while held → remember it and revert so the quote stays up until release.
    //  - otherwise  → it's a normal reveal; tear down.
    function onMutations(records) {
        if (!hostEl || !isHidden(hostEl)) return;
        if (held) {
            pendingReveal = true;
            pendingHide = { class: hostEl.getAttribute('class'), style: hostEl.getAttribute('style') };
            for (var i = 0; i < records.length; i++) {
                var r = records[i];
                if (r.attributeName === 'class' || r.attributeName === 'style') {
                    if (r.oldValue === null) hostEl.removeAttribute(r.attributeName);
                    else hostEl.setAttribute(r.attributeName, r.oldValue);
                }
            }
        } else {
            teardown();
        }
    }

    function start(el, apiUrl) {
        if (!el) return;
        // Idempotent: re-starting on the same already-running host is a no-op so
        // repeated loadPart()/loading calls don't reset the rotation.
        if (hostEl === el && timer) return;
        teardown();
        injectStyle();
        hostEl = el;
        hostEl.classList.remove('hidden');
        hostEl.style.display = '';

        var cached = readCache();
        if (cached.length) setPool(cached, true);
        else setPool(BOILERPLATE, false);

        // Refresh in the background; if we showed boilerplate and real highlights
        // come back, swap to them.
        refreshCache(apiUrl, function (fresh) {
            if (fresh && fresh.length && !poolIsOwn) setPool(fresh, true);
        });

        // Watch the host for the page's own hide so press-and-hold can defer it.
        try {
            observer = new MutationObserver(onMutations);
            observer.observe(hostEl, { attributes: true, attributeOldValue: true, attributeFilter: ['class', 'style'] });
        } catch (_) { observer = null; }

        // Full-screen, transparent catcher so press-and-hold works no matter
        // where you tap, and touch-action:none stops the browser from stealing
        // the touch for scrolling — which used to fire pointercancel on the
        // slightest finger movement and drop the hold. The quote shows through
        // it; nothing else is interactive during the (brief) load anyway.
        catcher = document.createElement('div');
        catcher.id = 'grq-hold';
        catcher.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;'
            + 'z-index:2147483646;background:transparent;touch-action:none;';
        catcher.addEventListener('pointerdown', onDown);
        catcher.addEventListener('pointerup', onUp);
        catcher.addEventListener('pointercancel', onUp);
        (document.body || document.documentElement).appendChild(catcher);

        timer = setInterval(rotate, ROTATE_MS);
    }

    // Public stop. While held, defer the actual teardown until release so a
    // host that hides + stops mid-hold (e.g. the player's setMsg('')) still
    // keeps the quote on screen until the user lets go.
    function stop() {
        if (held) { pendingReveal = true; return; }
        teardown();
    }

    function teardown() {
        if (timer) { clearInterval(timer); timer = null; }
        if (observer) { try { observer.disconnect(); } catch (_) {} observer = null; }
        if (catcher) {
            try { catcher.removeEventListener('pointerdown', onDown); } catch (_) {}
            try { catcher.removeEventListener('pointerup', onUp); } catch (_) {}
            try { catcher.removeEventListener('pointercancel', onUp); } catch (_) {}
            try { if (catcher.parentNode) catcher.parentNode.removeChild(catcher); } catch (_) {}
            catcher = null;
        }
        hostEl = null; pool = []; idx = 0;
        held = false; pendingReveal = false; pendingHide = null;
    }

    window.GreatReadsQuotes = { start: start, stop: stop };
})();
