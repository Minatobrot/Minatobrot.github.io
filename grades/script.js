document.addEventListener('DOMContentLoaded', () => {

    // --- Navbar scroll effect ---
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 40);
        }, { passive: true });
    }

    // --- Mobile menu toggle ---
    const mobileToggle = document.querySelector('.nav-mobile-toggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            document.querySelectorAll('.nav-links, .nav-actions').forEach(el => {
                el.classList.toggle('open');
            });
        });
    }

    // --- Smooth scrolling for anchor links ---
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (!targetId || targetId === '#') return;
            const target = document.querySelector(targetId);
            if (!target) return;
            e.preventDefault();

            // Close mobile menu if open
            document.querySelectorAll('.nav-links, .nav-actions').forEach(el => {
                el.classList.remove('open');
            });

            target.scrollIntoView({ behavior: 'smooth' });
        });
    });

    // --- Scroll-triggered fade-in animations ---
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.08,
        rootMargin: '0px 0px -40px 0px'
    });

    document.querySelectorAll(
        '.feature-card, .step-card, .trust-card, .showcase-card, .faq-item, .proof-item, .section-header'
    ).forEach(el => {
        el.classList.add('fade-in');
        observer.observe(el);
    });
});
