const statusText = document.getElementById('status-text');
const subText = document.getElementById('sub-text');
const bodyItem = document.body;
const glitchOverlay = document.getElementById('glitch-overlay');

let typingTimer = null;
let previousState = null;

// ==================== TYPEWRITER ====================
function typeWriter(text) {
    if (!subText) return; // Prevent crash if element is removed
    // Cancel any ongoing typing
    if (typingTimer) clearTimeout(typingTimer);
    
    subText.innerText = "";
    subText.classList.add('typing');
    let i = 0;
    
    function type() {
        if (i < text.length) {
            subText.innerText += text.charAt(i);
            // Auto-scroll to bottom so latest text is always visible
            subText.scrollTop = subText.scrollHeight;
            i++;
            typingTimer = setTimeout(type, 25);
        } else {
            // Done typing, remove cursor
            subText.classList.remove('typing');
        }
    }
    type();
}

// ==================== GLITCH TRANSITION (Feature 5) ====================
function triggerGlitch() {
    if (!glitchOverlay) return;
    // Remove any existing animation class
    glitchOverlay.classList.remove('active');
    
    // Force reflow so re-adding the class restarts the animation
    void glitchOverlay.offsetWidth;
    
    // Trigger the glitch burst
    glitchOverlay.classList.add('active');
    
    // Auto-remove after animation completes (150ms)
    setTimeout(() => {
        glitchOverlay.classList.remove('active');
    }, 200);
}

// ==================== WEBSOCKET CONNECTION ====================
function connect() {
    const ws = new WebSocket('ws://localhost:8765');
    
    ws.onopen = () => {
        if (statusText) statusText.innerText = "FRIDAY ONLINE";
        if (subText) subText.innerText = "System ready.";
        if (window.setUiState) window.setUiState('idle');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const state = data.state;
        const msgText = data.text;
        
        // ---- TRIGGER GLITCH ON STATE CHANGE (Feature 5) ----
        if (previousState !== null && previousState !== state) {
            triggerGlitch();
        }
        previousState = state;
        
        // Update styling
        bodyItem.className = 'state-' + state;
        
        if (window.setUiState) {
            window.setUiState(state);
        }
        
        if (statusText) {
            if (state === 'idle') {
                statusText.innerText = "IDLE";
            } else if (state === 'listening') {
                statusText.innerText = "LISTENING";
            } else if (state === 'thinking') {
                statusText.innerText = "THINKING";
            } else if (state === 'speaking') {
                statusText.innerText = "SPEAKING";
            }
        }
        
        if (msgText) {
            // Show Friday's words with character-by-character animation
            typeWriter(msgText);
        } else if (subText) {
            // Clear typing and show state text
            if (typingTimer) clearTimeout(typingTimer);
            subText.classList.remove('typing');
            
            if (state === 'listening') {
                subText.innerText = "Listening...";
            } else if (state === 'thinking') {
                subText.innerText = "Processing...";
            } else if (state === 'idle') {
                subText.innerText = "Awaiting command.";
            }
        }
    };

    ws.onclose = () => {
        if (statusText) statusText.innerText = "OFFLINE";
        if (subText) subText.innerText = "Reconnecting...";
        previousState = null;
        setTimeout(connect, 2000);
    };
}

connect();
