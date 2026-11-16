/* Podcast pages: everything here reads the episode blocks that are already in
   the HTML. Nothing about an episode (title, people, link) is defined in this
   file, so the pages stay correct when episodes are added with the dashboard. */
(() => {
    'use strict';

    const slug = (text) => text.toLowerCase()
        .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
        .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'episode';

    const fmt = (sec) => {
        if (!isFinite(sec) || sec < 0) return '–:––';
        const s = Math.floor(sec % 60), m = Math.floor(sec / 60) % 60, h = Math.floor(sec / 3600);
        return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(s).padStart(2, '0');
    };

    const el = (tag, cls, html) => {
        const node = document.createElement(tag);
        if (cls) node.className = cls;
        if (html != null) node.innerHTML = html;
        return node;
    };

    /* Read one episode block. Used on the class pages and for the overview. */
    const readEpisode = (card) => ({
        title: (card.querySelector('h3')?.textContent || '').trim(),
        author: (card.querySelector('.podcast-author')?.textContent || '').trim(),
        moodle: !!card.querySelector('.moodle-button'),
    });

    const withTransition = (fn) => {
        const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (document.startViewTransition && !calm) document.startViewTransition(fn);
        else fn();
    };

    /* ================= class page ================= */

    const list = document.querySelector('main.podcast-grid');
    if (list) {
        const cards = [...list.querySelectorAll('.podcast-card')];
        const used = new Set();
        const episodes = cards.map((card) => {
            const ep = readEpisode(card);
            let id = slug(ep.title);
            for (let n = 2; used.has(id); n++) id = slug(ep.title) + '-' + n;
            used.add(id);
            card.id = id;
            // an empty "Quellen" block is just noise
            const src = card.querySelector('.podcast-sources');
            if (src && !src.querySelector('li')) src.hidden = true;
            return { ...ep, id, card };
        });

        /* ---- players ---- */
        let current = null;

        cards.forEach((card) => {
            const audio = card.querySelector('audio');
            if (!audio) return;
            const title = card.querySelector('h3')?.textContent.trim() || 'Episode';

            const player = el('div', 'player');
            const btn = el('button', 'player-btn',
                '<svg class="i-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15l13-7.500z"/></svg>' +
                '<svg class="i-pause" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4.500h4.500v15H6zM13.500 4.500H18v15h-4.500z"/></svg>');
            btn.type = 'button';
            btn.setAttribute('aria-label', title + ' abspielen');

            const seek = el('input', 'player-seek');
            seek.type = 'range';
            seek.min = 0; seek.max = 1000; seek.value = 0; seek.step = 1;
            seek.disabled = true;
            seek.setAttribute('aria-label', 'Position in ' + title);

            const eq = el('span', 'player-eq', '<i></i><i></i><i></i>');
            eq.setAttribute('aria-hidden', 'true');
            const time = el('span', 'player-time', '0:00');

            player.append(btn, seek, eq, time);
            audio.after(player);
            audio.removeAttribute('controls');
            audio.classList.add('is-enhanced');

            let dragging = false;
            const paint = () => {
                const d = audio.duration, t = audio.currentTime;
                const ok = isFinite(d) && d > 0;
                seek.disabled = !ok;
                if (ok && !dragging) seek.value = Math.round((t / d) * 1000);
                seek.style.setProperty('--p', (seek.value / 10) + '%');
                time.textContent = ok ? fmt(t) + ' / ' + fmt(d) : fmt(t);
            };

            btn.addEventListener('click', () => {
                if (audio.paused) audio.play().catch(() => {});
                else audio.pause();
            });
            audio.addEventListener('play', () => {
                if (current && current !== audio) current.pause();
                current = audio;
                card.classList.add('is-playing');
                btn.setAttribute('aria-label', title + ' pausieren');
            });
            const stopped = () => {
                card.classList.remove('is-playing');
                btn.setAttribute('aria-label', title + ' abspielen');
            };
            audio.addEventListener('pause', stopped);
            audio.addEventListener('ended', stopped);
            ['timeupdate', 'durationchange', 'loadedmetadata', 'seeked'].forEach((ev) => audio.addEventListener(ev, paint));

            seek.addEventListener('input', () => {
                dragging = true;
                seek.style.setProperty('--p', (seek.value / 10) + '%');
                if (isFinite(audio.duration)) time.textContent = fmt((seek.value / 1000) * audio.duration) + ' / ' + fmt(audio.duration);
            });
            seek.addEventListener('change', () => {
                if (isFinite(audio.duration)) audio.currentTime = (seek.value / 1000) * audio.duration;
                dragging = false;
            });

            // every <source> failed: say so and offer the file itself
            const sources = [...audio.querySelectorAll('source')];
            const last = sources[sources.length - 1];
            const failed = () => {
                if (card.querySelector('.player-error')) return;
                stopped();
                const href = sources[0]?.getAttribute('src');
                const msg = el('p', 'player-error');
                msg.textContent = 'Die Aufnahme lässt sich gerade nicht laden. ';
                if (href) {
                    const a = el('a');
                    a.href = href; a.target = '_blank'; a.rel = 'noopener';
                    a.textContent = 'Datei direkt öffnen';
                    msg.append(a);
                }
                player.replaceWith(msg);
            };
            if (last) last.addEventListener('error', failed);
            audio.addEventListener('error', failed);
            paint();
        });

        /* ---- count, filter, jump list ---- */
        const tools = document.getElementById('ep-tools');
        if (tools && episodes.length) {
            const here = episodes.filter((e) => !e.moodle).length;
            const there = episodes.length - here;

            const count = el('p', 'ep-count');
            count.innerHTML = '<b>' + episodes.length + ' Episoden</b>, ' + here + ' direkt hier hörbar, ' + there + ' auf Moodle';

            const filters = el('div', 'ep-filters');
            filters.setAttribute('role', 'group');
            filters.setAttribute('aria-label', 'Episoden filtern');
            const options = [['all', 'Alle'], ['here', 'Direkt hörbar'], ['moodle', 'Auf Moodle']];
            const jump = el('ul', 'ep-jump');
            jump.setAttribute('aria-label', 'Zu einer Episode springen');
            const jumpItems = episodes.map((e) => {
                const li = el('li');
                const a = el('a');
                a.href = '#' + e.id;
                a.textContent = e.title;
                li.append(a);
                jump.append(li);
                return li;
            });

            const apply = (mode) => {
                episodes.forEach((e, i) => {
                    const show = mode === 'all' || (mode === 'moodle') === e.moodle;
                    e.card.hidden = !show;
                    jumpItems[i].hidden = !show;
                    if (!show) e.card.querySelector('audio')?.pause();
                });
                filters.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.mode === mode)));
            };
            options.forEach(([mode, label]) => {
                if ((mode === 'here' && !here) || (mode === 'moodle' && !there)) return;
                const b = el('button');
                b.type = 'button';
                b.dataset.mode = mode;
                b.textContent = label;
                b.setAttribute('aria-pressed', String(mode === 'all'));
                b.addEventListener('click', () => withTransition(() => apply(mode)));
                filters.append(b);
            });

            tools.append(count);
            if (filters.children.length > 1) tools.append(filters);
            tools.append(jump);
            tools.hidden = false;
        }

        // ids were only just assigned, so honour a #link from the overview now
        if (location.hash.length > 1) {
            const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
            if (target) target.scrollIntoView();
        }
    }

    /* ================= overview on podcasts/ ================= */

    const overview = document.getElementById('overview');
    if (overview) {
        const classes = (overview.dataset.classes || '').split(',').map((s) => s.trim()).filter(Boolean);
        Promise.all(classes.map((dir) =>
            fetch(dir + '/', { cache: 'no-cache' })
                .then((r) => { if (!r.ok) throw new Error(r.status); return r.text(); })
                .then((html) => {
                    const doc = new DOMParser().parseFromString(html, 'text/html');
                    const used = new Set();
                    const name = (doc.querySelector('h1')?.textContent || dir).replace(/^Podcasts von\s+/i, '').trim();
                    const episodes = [...doc.querySelectorAll('.podcast-card')].map((card) => {
                        const ep = readEpisode(card);
                        let id = slug(ep.title);
                        for (let n = 2; used.has(id); n++) id = slug(ep.title) + '-' + n;
                        used.add(id);
                        return { ...ep, id };
                    });
                    return { dir, name, episodes };
                })
        )).then((data) => {
            // one row per genre, in the order the genres first appear
            const rows = new Map();
            data.forEach((cls, col) => cls.episodes.forEach((ep) => {
                const key = slug(ep.title);
                if (!rows.has(key)) rows.set(key, { title: ep.title, cells: data.map(() => []) });
                rows.get(key).cells[col].push(ep);
            }));
            if (!rows.size) return;

            const table = el('table', 'overview-table');
            const head = el('tr');
            head.append(el('th', '', 'Thema'));
            data.forEach((cls) => { const th = el('th'); th.scope = 'col'; th.textContent = cls.name; head.append(th); });
            const thead = el('thead'); thead.append(head);
            const tbody = el('tbody');
            let i = 0;
            rows.forEach((row) => {
                const tr = el('tr');
                tr.style.animationDelay = (i++ * 35) + 'ms';
                const th = el('th'); th.scope = 'row'; th.textContent = row.title;
                tr.append(th);
                row.cells.forEach((eps, col) => {
                    const td = el('td');
                    if (!eps.length) { td.className = 'none'; td.textContent = '–'; }
                    eps.forEach((ep) => {
                        const a = el('a');
                        a.href = data[col].dir + '/#' + ep.id;
                        a.textContent = ep.author.replace(/^von\s+/i, '') || ep.title;
                        td.append(a);
                        if (ep.moodle) td.append(el('span', 'on-moodle', 'auf Moodle'));
                    });
                    tr.append(td);
                });
                tbody.append(tr);
            });
            table.append(thead, tbody);
            overview.querySelector('.overview-body').replaceChildren(table);
            overview.hidden = false;
        }).catch(() => { /* overview stays hidden; the class links above still work */ });
    }
})();
