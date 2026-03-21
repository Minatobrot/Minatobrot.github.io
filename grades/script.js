document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (!targetId || targetId === '#') {
                return;
            }
            const targetElement = document.querySelector(targetId);
            if (!targetElement) {
                return;
            }
            e.preventDefault();
            targetElement.scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // Only animate once
            }
        });
    }, observerOptions);

    // Elements to animate
    const animatedElements = document.querySelectorAll('.feature-card, .step, .faq-item, h2');
    animatedElements.forEach(el => {
        el.classList.add('fade-in-section');
        observer.observe(el);
    });

    // Footer links handling
    const aboutLink = document.getElementById('link-about');
    const datenschutzLink = document.getElementById('link-datenschutz');
    const impressumLink = document.getElementById('link-impressum');
    const kontaktLink = document.getElementById('link-kontakt');

    if (aboutLink) {
        aboutLink.addEventListener('click', (e) => {
            e.preventDefault();
            alert('About Panum:\n\nPanum is an independent project made to improve the school workflow. It is not affiliated with schulNetz.\n\nDeveloped by Minoshek Kishokumar.');
        });
    }

    if (datenschutzLink) {
        datenschutzLink.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Privacy:\n\nPanum does NOT store any data on external servers. All data (grades and settings) stays local in your browser (LocalStorage/SyncStorage). No tracking and no personal data collection.');
        });
    }

    if (impressumLink) {
        impressumLink.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Imprint:\n\nMinoshek Kishokumar\n[Address on request]\nContact: Minoshekk@gmail.com\n\nThis is a private, non-commercial project.');
        });
    }

    if (kontaktLink) {
        kontaktLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = 'mailto:Minoshekk@gmail.com';
        });
    }
});
