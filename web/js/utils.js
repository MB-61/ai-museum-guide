// ========================================
// AI Müze Rehberi - Utility Functions
// ========================================

// Toast notification
export function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');

    if (!toast || !toastMessage || !toastIcon) return;

    toastMessage.textContent = message;

    const icons = {
        'success': 'check_circle',
        'error': 'error',
        'warning': 'warning',
        'info': 'info'
    };
    const colors = {
        'success': 'text-green-400',
        'error': 'text-red-400',
        'warning': 'text-yellow-400',
        'info': 'text-primary'
    };

    toastIcon.textContent = icons[type] || icons.info;
    toastIcon.className = `material-symbols-outlined ${colors[type] || colors.info}`;

    toast.classList.remove('opacity-0', '-translate-y-4');
    toast.classList.add('opacity-100', 'translate-y-0');

    setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', '-translate-y-4');
    }, 3000);
}

// Status text update
export function setStatus(message) {
    const statusText = document.getElementById('status-text');
    if (statusText) {
        statusText.textContent = message;
    }
}

// Generate QR code for network URL
export function generateNetworkQR() {
    const urlElement = document.getElementById('network-url');
    const qrContainer = document.getElementById('network-qr');
    const currentUrl = window.location.href;

    if (urlElement) {
        urlElement.innerHTML = `<a href="${currentUrl}" class="text-primary hover:underline">${currentUrl}</a>`;
    }

    if (qrContainer && typeof QRCode !== 'undefined') {
        qrContainer.innerHTML = '';
        new QRCode(qrContainer, {
            text: currentUrl,
            width: 64,
            height: 64,
            colorDark: '#000000',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.L
        });
    }
}

// URL parameter helpers
export function getUrlParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

// Navigate to page
export function navigateTo(url) {
    window.location.href = url;
}

// Add message to chat
export function addMessage(text, isUser = false) {
    const messagesContainer = document.getElementById('messages');
    const messagesPanel = document.getElementById('messages-panel');

    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message-bubble ${isUser ? 'message-user' : 'message-ai'}`;
    messageDiv.textContent = text;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    if (messagesPanel) {
        messagesPanel.style.display = 'block';
    }
}

// Toggle messages panel
export function toggleMessages() {
    const messages = document.getElementById('messages');
    if (messages) {
        if (messages.style.maxHeight === '200px') {
            messages.style.maxHeight = '80px';
        } else {
            messages.style.maxHeight = '200px';
        }
    }
}

// Toggle chat input panel
export function toggleChatInput() {
    const panel = document.getElementById('chat-input-panel');
    const input = document.getElementById('chat-input');
    if (panel) {
        if (panel.style.display === 'none' || !panel.style.display) {
            panel.style.display = 'block';
            if (input) input.focus();
        } else {
            panel.style.display = 'none';
        }
    }
}

// Handle keyboard input
export function handleKeyPress(event, callback) {
    if (event.key === 'Enter') {
        callback();
    }
}

// Mobile keyboard handling
export function setupMobileKeyboard() {
    const chatInput = document.getElementById('chat-input');
    const chatInputPanel = document.getElementById('chat-input-panel');
    const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

    if (chatInput && chatInputPanel && isTouchDevice) {
        chatInput.addEventListener('focus', () => {
            chatInputPanel.style.position = 'fixed';
            chatInputPanel.style.top = '80px';
            chatInputPanel.style.bottom = 'auto';
            chatInputPanel.style.left = '16px';
            chatInputPanel.style.right = '16px';
            chatInputPanel.style.zIndex = '9999';
        });

        chatInput.addEventListener('blur', () => {
            setTimeout(() => {
                chatInputPanel.style.cssText = '';
            }, 100);
        });
    }
}

// Setup status observer for input button visibility
export function setupStatusObserver() {
    const statusElement = document.getElementById('status-floating');
    const toggleInputBtn = document.getElementById('toggle-input-btn');

    if (statusElement && toggleInputBtn) {
        const updateButtonVisibility = () => {
            const text = (document.getElementById('status-text')?.innerText || '').toLowerCase().trim();
            if (text.includes('hazır') || text.includes('durduruldu')) {
                toggleInputBtn.style.visibility = 'visible';
                toggleInputBtn.style.opacity = '1';
            } else {
                toggleInputBtn.style.visibility = 'hidden';
                toggleInputBtn.style.opacity = '0';
            }
        };

        const observer = new MutationObserver(updateButtonVisibility);
        observer.observe(statusElement, { childList: true, characterData: true, subtree: true });

        setTimeout(updateButtonVisibility, 500);
    }
}

// Make functions globally available for onclick handlers
window.showToast = showToast;
window.setStatus = setStatus;
window.toggleMessages = toggleMessages;
window.toggleChatInput = toggleChatInput;
