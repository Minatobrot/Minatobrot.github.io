document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
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
            alert('About Panum:\n\nPanum ist ein unabhängiges Projekt, um den Schulalltag zu erleichtern. Es steht in keiner Verbindung zu schulNetz.\n\nEntwickelt von Minoshek Kishokumar.');
        });
    }

    if (datenschutzLink) {
        datenschutzLink.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Datenschutz:\n\nPanum speichert KEINE Daten auf externen Servern. Alle Daten (Noten, Einstellungen) bleiben lokal in deinem Browser (LocalStorage/SyncStorage). Wir tracken dich nicht und sammeln keine persönlichen Informationen.');
        });
    }

    if (impressumLink) {
        impressumLink.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Impressum:\n\nMinoshek Kishokumar\n[Adresse auf Anfrage]\nKontakt: Minoshekk@gmail.com\n\nDies ist ein privates, nicht-kommerzielles Projekt.');
        });
    }

    if (kontaktLink) {
        kontaktLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = 'mailto:Minoshekk@gmail.com';
        });
    }
});
