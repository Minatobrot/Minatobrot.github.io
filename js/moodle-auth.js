document.addEventListener('DOMContentLoaded', function() {
    const moodleDomain = 'moodle.ksasz.ch';

    // Create Modal if it doesn't exist
    if (!document.getElementById('moodle-auth-modal')) {
        const modalHTML = `
            <div id="moodle-auth-modal" class="modal-overlay">
                <div class="modal-content">
                    <h3>Anmeldung erforderlich</h3>
                    <p>Dieser Podcast wird auf Moodle gehostet.</p>
                    <p>Um ihn anzuhören, ist eine Anmeldung erforderlich.</p>
                    <p>Nach erfolgreichem Login wirst du automatisch auf diese Seite zurückgeleitet.</p>
                    <button id="moodle-login-btn" class="btn-modal">Weiter zu Moodle</button>
                    <button id="moodle-cancel-btn" class="btn-modal btn-secondary">Abbrechen</button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Bind events for modal
        document.getElementById('moodle-login-btn').addEventListener('click', redirectToMoodle);
        document.getElementById('moodle-cancel-btn').addEventListener('click', hideModal);
        
        // Close on overlay click
        document.getElementById('moodle-auth-modal').addEventListener('click', function(e) {
            if (e.target === this) hideModal();
        });
    }

    const modal = document.getElementById('moodle-auth-modal');

    function showModal() {
        modal.classList.add('show');
    }

    function hideModal() {
        modal.classList.remove('show');
    }

    function redirectToMoodle() {
        // Construct Moodle login URL with wantsurl
        const currentUrl = window.location.href;
        const encodedUrl = encodeURIComponent(currentUrl);
        // Standard Moodle login often uses /login/index.php. 
        // We usually pass the wantsurl parameter so Moodle knows where to go back.
        // However, standard Moodle login might not respect 'wantsurl' directly in the query string 
        // if not configured, but usually it does or uses 'ref'.
        // The user specifically asked for "wantsurl".
        // Example: https://moodle.ksasz.ch/login/index.php?wantsurl=...
        
        window.location.href = `https://${moodleDomain}/login/index.php?wantsurl=${encodedUrl}`;
    }

    // Attempt to play audio
    // We cannot easily pre-check auth status without CORS.
    // Strategy: 
    // 1. Intercept play.
    // 2. If valid session known (we can track via sessionStorage if we just came back?), just play.
    //    Actually, we can't fully trust sessionStorage for "valid session" because it might expire.
    //    But we can use it to avoid double-checking immediately after redirect.
    // 3. User requirement: "Wenn ein Nutzer sich bereits früher eingeloggt hat... darf kein erneutes Popup erscheinen"
    //    This implies we should try to play. If it fails (error), show popup.
    // BUT user also said: "Wenn keine gültige Session vorhanden ist, darf nicht sofort weitergeleitet werden. Stattdessen soll zuerst ein modernes, zentriertes Modal-Popup erscheinen."
    // AND "Wenn ein Nutzer auf einen MP3-Player klickt... soll geprüft werden"
    
    // The most robust way to "check" cross-origin without CORS is to let the audio *try* to load.
    // If it fails with 403, we know.
    // If we just let it play, the browser's native player might show an error UI before we can intercept.
    // However, we can listen for 'error' event on source or audio.

    const audios = document.querySelectorAll('audio');

    audios.forEach(audio => {
        // Identify if this is a Moodle audio
        // We check valid sources.
        const sources = audio.querySelectorAll('source');
        let isMoodle = false;
        sources.forEach(source => {
            if (source.src.includes(moodleDomain)) {
                isMoodle = true;
                // Add error listener to source specifically
                source.addEventListener('error', (e) => handleAudioError(e, audio));
            }
        });

        if (isMoodle) {
            // Also attach error to audio element itself (captures source errors in some browsers)
            audio.addEventListener('error', (e) => handleAudioError(e, audio), true);
            
            // Intercept Play attempt
            // We can't easily prevent the browser from STARTING the request on click.
            // But we can pause it immediately if we think we need to Login?
            // No, preventing default behavior of native controls is hard.
            // User says: "Wenn ein Nutzer auf einen MP3-Player klickt... soll geprüft werden"
            
            // If we use 'play' event:
            audio.addEventListener('play', function(e) {
                // Check if we suspect we are not logged in?
                // Actually, just letting it play is the "Check". 
                // If it plays, great. If it fails, we catch the error.
                // UNLESS the browser doesn't report 403 as a standard error we can catch before UI update.
                // Most browsers will fire an error event.
                
                // Let's rely on the error event for 403 / network failure.
                // It satisfies "If valid... play immediately".
                // It satisfies "If invalid... show modal" (on error).
                
                // WAIT. User said: "Wenn ein Nutzer auf einen MP3-Player klickt... soll geprüft werden... Wenn keine gültige Session vorhanden ist, darf nicht sofort weitergeleitet werden."
                // This implies "Don't redirect automatically on 403". (Which browsers don't do anyway for media).
                
                // Is there a case where we need to check BEFORE play?
                // "soll geprüft werden, ob eine gültige Moodle-Session existiert."
                // Since we can't read cookies, the only check is the network request response.
                
                // There is one edge case: The browser might pop up a native authentication dialog (basic auth) if the server requests it?
                // Moodle usually uses form-based auth (cookies), so it redirects to login page (303/302).
                // If it redirects, the audio element might fail to play because the response is an HTML page (login), not audio.
                // This will trigger an error (decoding error or network error).
            });
        }
    });

    function handleAudioError(e, audio) {
        // Check if the current src is moodle
        let currentSrc = audio.currentSrc;
        
        // If currentSrc is empty, logic might be needed to find which source failed.
        if (!currentSrc) {
            // Try to find the moodle source
            const sources = audio.querySelectorAll('source');
            for (let s of sources) {
                if (s.src.includes(moodleDomain)) {
                    currentSrc = s.src;
                    break;
                }
            }
        }

        if (currentSrc && currentSrc.includes(moodleDomain)) {
            // It's a Moodle error.
            // Prevent default error display if possible? (Hard with native controls)
            
            // Check network state?
            // If the error is 4 (MEDIA_ERR_SRC_NOT_SUPPORTED), it often means 403 or 404 or MIME type mismatch (which happens if redirect to login page).
            
            console.log("Moodle audio error detected:", e);
            
            // Show Modal
            showModal();
            
            // Pause to stop spinning?
            audio.pause();
            
            // We interpret this error as "Needs Login" because Archive.org files (public) work.
            // Moodle files require session.
        }
    }
});
