document.addEventListener('DOMContentLoaded', () => {

    // --- Navbar: show the bottom rule once the page has scrolled ---
    const navbar = document.getElementById('navbar');
    if (navbar) {
        const onScroll = () => navbar.classList.toggle('scrolled', window.scrollY > 40);
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    // --- Mobile menu toggle ---
    const mobileToggle = document.querySelector('.nav-mobile-toggle');
    const menuParts = document.querySelectorAll('.nav-links, .nav-actions');
    const setMenu = (open) => {
        menuParts.forEach(el => el.classList.toggle('open', open));
        if (mobileToggle) mobileToggle.setAttribute('aria-expanded', String(open));
    };
    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            setMenu(mobileToggle.getAttribute('aria-expanded') !== 'true');
        });
    }

    // --- Smooth scrolling for anchor links ---
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (!targetId || targetId === '#') return;
            const target = document.querySelector(targetId);
            if (!target) return;
            e.preventDefault();
            setMenu(false);
            target.scrollIntoView({ behavior: calm ? 'auto' : 'smooth' });
            history.replaceState(null, '', targetId);
        });
    });

    // --- Dark mode comparison: one frame, one switch ---
    const dm = document.getElementById('dm');
    if (dm) {
        const control = dm.querySelector('.dm-control');
        const toggle = dm.querySelector('.dm-switch');
        const label = dm.querySelector('.dm-label');
        const captions = {
            dark: dm.querySelector('.dm-dark figcaption').textContent,
            light: dm.querySelector('.dm-light figcaption').textContent,
        };
        const set = (dark) => {
            dm.dataset.mode = dark ? 'dark' : 'light';
            toggle.setAttribute('aria-checked', String(dark));
            label.textContent = dark ? captions.dark : captions.light;
        };
        dm.classList.add('is-live');
        control.hidden = false;
        set(true);
        toggle.addEventListener('click', () => set(toggle.getAttribute('aria-checked') !== 'true'));
    }

    // --- FAQ: opening one question closes the others ---
    const faqs = document.querySelectorAll('.faq-item');
    faqs.forEach(item => {
        item.addEventListener('toggle', () => {
            if (!item.open) return;
            faqs.forEach(other => { if (other !== item) other.open = false; });
        });
    });
});
